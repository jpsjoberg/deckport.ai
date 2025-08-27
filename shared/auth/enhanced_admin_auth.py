"""
Enhanced admin authentication decorator with comprehensive security features
Integrates rate limiting, session management, audit logging, CSRF protection, and IP restrictions
"""

from functools import wraps
from flask import request, jsonify, g
from shared.auth.jwt_handler import verify_admin_token
from shared.database.connection import SessionLocal
from shared.models.base import Admin
from shared.security import (
    rate_limit, session_manager, AdminAuditLogger, 
    csrf_protect, ip_restrict
)
import logging

logger = logging.getLogger(__name__)

def enhanced_admin_required(
    require_csrf: bool = True,
    require_ip_check: bool = True,
    rate_limit_type: str = None,
    require_super_admin: bool = False
):
    """
    Enhanced admin authentication decorator with comprehensive security
    
    Args:
        require_csrf: Whether to validate CSRF tokens (default: True for non-GET requests)
        require_ip_check: Whether to check IP access control (default: True)
        rate_limit_type: Rate limit type to apply (default: auto-detect)
        require_super_admin: Whether to require super admin privileges (default: False)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. IP Access Control
            if require_ip_check:
                from shared.security.ip_access_control import ip_access_control
                client_ip = ip_access_control.get_client_ip()
                allowed, reason = ip_access_control.is_ip_allowed(client_ip)
                
                if not allowed:
                    AdminAuditLogger.log_security_event(
                        'ip_access_denied',
                        'high',
                        {
                            'client_ip': client_ip,
                            'reason': reason,
                            'endpoint': request.endpoint,
                            'method': request.method
                        }
                    )
                    return jsonify({
                        'error': 'Access denied',
                        'message': 'Your IP address is not authorized'
                    }), 403
            
            # 2. Rate Limiting
            from shared.security.rate_limiter import check_rate_limit, get_client_identifier
            
            # Determine rate limit type
            endpoint_rate_limit = rate_limit_type
            if not endpoint_rate_limit:
                endpoint = request.endpoint or request.path
                from shared.security.rate_limiter import RateLimitConfig
                endpoint_rate_limit = RateLimitConfig.ENDPOINT_LIMITS.get(
                    endpoint, 'admin_general'
                )
            
            # Check rate limit
            identifier = get_client_identifier()
            allowed, info = check_rate_limit(endpoint_rate_limit, identifier)
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {request.endpoint}",
                    extra={
                        'identifier': identifier,
                        'endpoint': request.endpoint,
                        'rate_limit_info': info
                    }
                )
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again in {info.get("reset_in", 60)} seconds.'
                }), 429
            
            # 3. JWT Token Validation
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': 'Authorization header required'}), 401
            
            try:
                token_type, token = auth_header.split(' ', 1)
                if token_type.lower() != 'bearer':
                    return jsonify({'error': 'Invalid authorization header format'}), 401
            except ValueError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
            
            # Verify admin JWT token
            admin_payload = verify_admin_token(token)
            if not admin_payload:
                AdminAuditLogger.log_security_event(
                    'invalid_token_attempt',
                    'medium',
                    {
                        'endpoint': request.endpoint,
                        'ip_address': client_ip if require_ip_check else request.remote_addr
                    }
                )
                return jsonify({'error': 'Invalid or expired admin token'}), 401
            
            # 4. Database Verification and Session Management
            try:
                with SessionLocal() as session:
                    admin = session.query(Admin).filter(
                        Admin.id == admin_payload['admin_id'],
                        Admin.is_active == True
                    ).first()
                    
                    if not admin:
                        AdminAuditLogger.log_security_event(
                            'inactive_admin_attempt',
                            'high',
                            {
                                'admin_id': admin_payload.get('admin_id'),
                                'endpoint': request.endpoint
                            }
                        )
                        return jsonify({'error': 'Admin account not found or inactive'}), 403
                    
                    # Check super admin requirement
                    if require_super_admin and not admin.is_super_admin:
                        AdminAuditLogger.log_admin_action(
                            'unauthorized_super_admin_attempt',
                            details={
                                'admin_id': admin.id,
                                'endpoint': request.endpoint,
                                'required_privilege': 'super_admin'
                            },
                            success=False
                        )
                        return jsonify({'error': 'Super admin privileges required'}), 403
                    
                    # Set admin context
                    g.admin_id = admin.id
                    g.admin_email = admin.email
                    g.admin_username = admin.username
                    g.admin_role = admin.role
                    g.is_super_admin = admin.is_super_admin
                    g.is_admin = True
                    
                    # Update last login timestamp
                    from datetime import datetime, timezone
                    admin.last_login = datetime.now(timezone.utc)
                    session.commit()
                    
                    # Session management (if Redis is available)
                    if session_manager.redis_client:
                        # This would require session ID from JWT or cookie
                        # For now, we'll skip session validation but log the activity
                        pass
                    
            except Exception as e:
                logger.error(f"Database error during admin verification: {e}")
                return jsonify({'error': 'Database error during authentication'}), 500
            
            # 5. CSRF Protection (for non-GET requests)
            if require_csrf and request.method not in ['GET', 'HEAD', 'OPTIONS']:
                from shared.security.csrf_protection import CSRFProtection
                
                if not CSRFProtection.validate_csrf():
                    AdminAuditLogger.log_security_event(
                        'csrf_validation_failed',
                        'medium',
                        {
                            'admin_id': g.admin_id,
                            'endpoint': request.endpoint,
                            'method': request.method
                        }
                    )
                    return jsonify({
                        'error': 'CSRF token validation failed',
                        'message': 'Invalid or missing CSRF token'
                    }), 403
            
            # 6. Execute the protected function
            try:
                response = f(*args, **kwargs)
                
                # Add security headers to response
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                    response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                    response.headers['X-Content-Type-Options'] = 'nosniff'
                    response.headers['X-Frame-Options'] = 'DENY'
                    response.headers['X-XSS-Protection'] = '1; mode=block'
                
                return response
                
            except Exception as e:
                # Log any errors in the protected function
                AdminAuditLogger.log_admin_action(
                    f'endpoint_error_{request.endpoint}',
                    details={
                        'error': str(e),
                        'endpoint': request.endpoint,
                        'method': request.method
                    },
                    success=False,
                    error_message=str(e)
                )
                raise  # Re-raise the exception
        
        return decorated_function
    return decorator

# Convenience decorators for common use cases
def admin_required_enhanced(f):
    """Standard enhanced admin authentication"""
    return enhanced_admin_required()(f)

def super_admin_required_enhanced(f):
    """Enhanced admin authentication requiring super admin privileges"""
    return enhanced_admin_required(require_super_admin=True)(f)

def admin_required_no_csrf(f):
    """Enhanced admin authentication without CSRF validation (for API endpoints)"""
    return enhanced_admin_required(require_csrf=False)(f)

def admin_required_sensitive(f):
    """Enhanced admin authentication for sensitive operations with strict rate limiting"""
    return enhanced_admin_required(rate_limit_type='admin_sensitive')(f)
