"""
Rate limiting system for admin endpoints
Implements Redis-based rate limiting with configurable limits per endpoint
"""

import os
import time
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CLIENT = None

def get_redis_client():
    """Get Redis client with connection pooling"""
    global REDIS_CLIENT
    if not REDIS_AVAILABLE:
        return None
        
    if REDIS_CLIENT is None:
        try:
            REDIS_CLIENT = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            REDIS_CLIENT.ping()
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            REDIS_CLIENT = None
    return REDIS_CLIENT

class RateLimitConfig:
    """Rate limit configuration for different admin operations"""
    
    # Default limits (requests per window)
    DEFAULT_LIMITS = {
        'admin_login': {'requests': 5, 'window': 300},  # 5 attempts per 5 minutes
        'admin_general': {'requests': 100, 'window': 60},  # 100 requests per minute
        'admin_sensitive': {'requests': 10, 'window': 60},  # 10 sensitive ops per minute
        'admin_bulk': {'requests': 5, 'window': 300},  # 5 bulk operations per 5 minutes
    }
    
    # Endpoint-specific limits
    ENDPOINT_LIMITS = {
        '/v1/auth/admin/login': 'admin_login',
        '/v1/admin/players/ban': 'admin_sensitive',
        '/v1/admin/players/unban': 'admin_sensitive',
        '/v1/admin/devices/approve': 'admin_sensitive',
        '/v1/admin/devices/reject': 'admin_sensitive',
        '/v1/admin/devices/reboot': 'admin_sensitive',
        '/v1/admin/devices/shutdown': 'admin_sensitive',
        '/v1/admin/tournaments/start': 'admin_sensitive',
        '/v1/admin/game-operations/maintenance': 'admin_sensitive',
        '/v1/admin/communications/broadcast': 'admin_bulk',
        '/v1/admin/analytics/export': 'admin_bulk',
    }

def get_client_identifier() -> str:
    """Get unique identifier for rate limiting (IP + admin ID if available)"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    admin_id = getattr(g, 'admin_id', None)
    
    if admin_id:
        return f"admin:{admin_id}:{ip_address}"
    else:
        return f"ip:{ip_address}"

def check_rate_limit(limit_type: str, identifier: str) -> Tuple[bool, Dict]:
    """
    Check if request is within rate limit
    Returns (allowed, info_dict)
    """
    redis_client = get_redis_client()
    
    # If Redis is not available, allow all requests (fail open)
    if not redis_client:
        return True, {'redis_available': False}
    
    config = RateLimitConfig.DEFAULT_LIMITS.get(limit_type, RateLimitConfig.DEFAULT_LIMITS['admin_general'])
    max_requests = config['requests']
    window_seconds = config['window']
    
    # Redis key for this limit
    key = f"rate_limit:{limit_type}:{identifier}"
    
    try:
        # Use sliding window counter
        now = int(time.time())
        window_start = now - window_seconds
        
        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_count = redis_client.zcard(key)
        
        if current_count >= max_requests:
            # Rate limit exceeded
            ttl = redis_client.ttl(key)
            return False, {
                'limit_exceeded': True,
                'limit': max_requests,
                'window': window_seconds,
                'current': current_count,
                'reset_in': ttl if ttl > 0 else window_seconds
            }
        
        # Add current request
        redis_client.zadd(key, {str(now): now})
        redis_client.expire(key, window_seconds)
        
        return True, {
            'limit_exceeded': False,
            'limit': max_requests,
            'window': window_seconds,
            'current': current_count + 1,
            'remaining': max_requests - current_count - 1
        }
        
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        # Fail open on Redis errors
        return True, {'redis_error': str(e)}

def rate_limit(limit_type: Optional[str] = None):
    """
    Decorator to apply rate limiting to admin endpoints
    
    Usage:
        @rate_limit('admin_sensitive')
        def sensitive_admin_operation():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine limit type
            endpoint_limit_type = limit_type
            if not endpoint_limit_type:
                # Auto-detect based on endpoint
                endpoint = request.endpoint or request.path
                endpoint_limit_type = RateLimitConfig.ENDPOINT_LIMITS.get(
                    endpoint, 'admin_general'
                )
            
            # Get client identifier
            identifier = get_client_identifier()
            
            # Check rate limit
            allowed, info = check_rate_limit(endpoint_limit_type, identifier)
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {request.endpoint}",
                    extra={
                        'identifier': identifier,
                        'endpoint': request.endpoint,
                        'limit_type': endpoint_limit_type,
                        'rate_limit_info': info
                    }
                )
                
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again in {info.get("reset_in", 60)} seconds.',
                    'limit': info.get('limit'),
                    'window': info.get('window'),
                    'reset_in': info.get('reset_in')
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                response.headers['X-RateLimit-Window'] = str(info.get('window', 0))
            
            return response
        
        return decorated_function
    return decorator

def get_rate_limit_status(identifier: str) -> Dict:
    """Get current rate limit status for an identifier"""
    redis_client = get_redis_client()
    
    if not redis_client:
        return {'redis_available': False}
    
    status = {}
    
    for limit_name, config in RateLimitConfig.DEFAULT_LIMITS.items():
        key = f"rate_limit:{limit_name}:{identifier}"
        
        try:
            current_count = redis_client.zcard(key)
            ttl = redis_client.ttl(key)
            
            status[limit_name] = {
                'current': current_count,
                'limit': config['requests'],
                'window': config['window'],
                'reset_in': ttl if ttl > 0 else 0
            }
        except Exception as e:
            status[limit_name] = {'error': str(e)}
    
    return status

def reset_rate_limit(identifier: str, limit_type: Optional[str] = None):
    """Reset rate limit for an identifier (admin function)"""
    redis_client = get_redis_client()
    
    if not redis_client:
        return False
    
    try:
        if limit_type:
            key = f"rate_limit:{limit_type}:{identifier}"
            redis_client.delete(key)
        else:
            # Reset all limits for identifier
            pattern = f"rate_limit:*:{identifier}"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        
        return True
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        return False
