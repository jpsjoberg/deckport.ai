"""
Admin session management system
Handles session tracking, timeout, and security monitoring
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
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from flask import request, g

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")  # Different DB for sessions
REDIS_CLIENT = None

# Session configuration
SESSION_TIMEOUT_MINUTES = int(os.getenv("ADMIN_SESSION_TIMEOUT_MINUTES", "30"))
MAX_CONCURRENT_SESSIONS = int(os.getenv("ADMIN_MAX_CONCURRENT_SESSIONS", "3"))
SESSION_REFRESH_THRESHOLD_MINUTES = 5  # Refresh session if less than 5 minutes remaining

def get_redis_client():
    """Get Redis client for session management"""
    global REDIS_CLIENT
    if not REDIS_AVAILABLE:
        return None
        
    if REDIS_CLIENT is None:
        try:
            REDIS_CLIENT = redis.from_url(REDIS_URL, decode_responses=True)
            REDIS_CLIENT.ping()
            logger.info("Redis connection established for session management")
        except Exception as e:
            logger.warning(f"Redis not available for session management: {e}")
            REDIS_CLIENT = None
    return REDIS_CLIENT

@dataclass
class AdminSession:
    """Admin session data structure"""
    session_id: str
    admin_id: int
    admin_email: str
    admin_username: str
    is_super_admin: bool
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key in ['created_at', 'last_activity', 'expires_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'AdminSession':
        """Create from dictionary from Redis"""
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'last_activity', 'expires_at']:
            if isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)

class SessionManager:
    """Manages admin sessions with Redis backend"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def create_session(self, admin_id: int, admin_email: str, admin_username: str, 
                      is_super_admin: bool) -> Optional[AdminSession]:
        """Create a new admin session"""
        if not self.redis_client:
            return None
        
        try:
            # Generate session ID
            session_id = self._generate_session_id(admin_id)
            
            # Get client info
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')[:500]  # Truncate long user agents
            
            # Create session
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            
            session = AdminSession(
                session_id=session_id,
                admin_id=admin_id,
                admin_email=admin_email,
                admin_username=admin_username,
                is_super_admin=is_super_admin,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=now,
                last_activity=now,
                expires_at=expires_at
            )
            
            # Check concurrent session limit
            self._enforce_concurrent_session_limit(admin_id)
            
            # Store session
            session_key = f"admin_session:{session_id}"
            admin_sessions_key = f"admin_sessions:{admin_id}"
            
            # Store session data
            self.redis_client.hset(session_key, mapping=session.to_dict())
            self.redis_client.expire(session_key, SESSION_TIMEOUT_MINUTES * 60)
            
            # Add to admin's session list
            self.redis_client.sadd(admin_sessions_key, session_id)
            self.redis_client.expire(admin_sessions_key, SESSION_TIMEOUT_MINUTES * 60)
            
            logger.info(f"Created admin session {session_id} for admin {admin_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating admin session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[AdminSession]:
        """Get session by ID"""
        if not self.redis_client:
            return None
        
        try:
            session_key = f"admin_session:{session_id}"
            session_data = self.redis_client.hgetall(session_key)
            
            if not session_data:
                return None
            
            session = AdminSession.from_dict(session_data)
            
            # Check if session is expired
            if session.expires_at < datetime.now(timezone.utc):
                self.invalidate_session(session_id)
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def refresh_session(self, session_id: str) -> bool:
        """Refresh session timeout"""
        if not self.redis_client:
            return False
        
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Update activity and expiration
            now = datetime.now(timezone.utc)
            session.last_activity = now
            session.expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            
            # Update in Redis
            session_key = f"admin_session:{session_id}"
            self.redis_client.hset(session_key, mapping=session.to_dict())
            self.redis_client.expire(session_key, SESSION_TIMEOUT_MINUTES * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing session {session_id}: {e}")
            return False
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a specific session"""
        if not self.redis_client:
            return False
        
        try:
            session = self.get_session(session_id)
            if session:
                # Remove from admin's session list
                admin_sessions_key = f"admin_sessions:{session.admin_id}"
                self.redis_client.srem(admin_sessions_key, session_id)
            
            # Remove session
            session_key = f"admin_session:{session_id}"
            self.redis_client.delete(session_key)
            
            logger.info(f"Invalidated admin session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating session {session_id}: {e}")
            return False
    
    def invalidate_all_sessions(self, admin_id: int) -> bool:
        """Invalidate all sessions for an admin"""
        if not self.redis_client:
            return False
        
        try:
            admin_sessions_key = f"admin_sessions:{admin_id}"
            session_ids = self.redis_client.smembers(admin_sessions_key)
            
            for session_id in session_ids:
                session_key = f"admin_session:{session_id}"
                self.redis_client.delete(session_key)
            
            # Clear the session list
            self.redis_client.delete(admin_sessions_key)
            
            logger.info(f"Invalidated all sessions for admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating all sessions for admin {admin_id}: {e}")
            return False
    
    def get_admin_sessions(self, admin_id: int) -> List[AdminSession]:
        """Get all active sessions for an admin"""
        if not self.redis_client:
            return []
        
        try:
            admin_sessions_key = f"admin_sessions:{admin_id}"
            session_ids = self.redis_client.smembers(admin_sessions_key)
            
            sessions = []
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session:
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting sessions for admin {admin_id}: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (maintenance task)"""
        if not self.redis_client:
            return 0
        
        try:
            # Find all session keys
            session_keys = self.redis_client.keys("admin_session:*")
            cleaned = 0
            
            for session_key in session_keys:
                session_data = self.redis_client.hgetall(session_key)
                if session_data:
                    try:
                        expires_at = datetime.fromisoformat(session_data['expires_at'])
                        if expires_at < datetime.now(timezone.utc):
                            session_id = session_key.split(':')[1]
                            self.invalidate_session(session_id)
                            cleaned += 1
                    except Exception:
                        # Invalid session data, remove it
                        self.redis_client.delete(session_key)
                        cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} expired admin sessions")
            return cleaned
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return 0
    
    def _generate_session_id(self, admin_id: int) -> str:
        """Generate unique session ID"""
        timestamp = int(time.time() * 1000)  # Milliseconds
        return f"{admin_id}_{timestamp}_{os.urandom(8).hex()}"
    
    def _enforce_concurrent_session_limit(self, admin_id: int):
        """Enforce maximum concurrent sessions per admin"""
        try:
            sessions = self.get_admin_sessions(admin_id)
            
            if len(sessions) >= MAX_CONCURRENT_SESSIONS:
                # Sort by last activity and remove oldest sessions
                sessions.sort(key=lambda s: s.last_activity)
                sessions_to_remove = sessions[:-MAX_CONCURRENT_SESSIONS + 1]
                
                for session in sessions_to_remove:
                    self.invalidate_session(session.session_id)
                    logger.info(f"Removed old session {session.session_id} for admin {admin_id}")
        
        except Exception as e:
            logger.error(f"Error enforcing session limit for admin {admin_id}: {e}")

# Global session manager instance
session_manager = SessionManager()
