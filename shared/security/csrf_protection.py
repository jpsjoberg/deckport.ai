"""
CSRF protection for admin forms
Implements token-based CSRF protection with secure token generation
"""

import os
import hmac
import hashlib
import secrets
from typing import Optional
from datetime import datetime, timezone, timedelta
from flask import request, session, g

# CSRF Configuration
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production"))
CSRF_TOKEN_TIMEOUT_MINUTES = 60  # CSRF tokens expire after 1 hour

class CSRFProtection:
    """CSRF protection implementation"""
    
    @staticmethod
    def generate_csrf_token(admin_id: Optional[int] = None) -> str:
        """
        Generate a secure CSRF token
        
        Args:
            admin_id: Admin ID to bind token to (optional)
        
        Returns:
            Base64-encoded CSRF token
        """
        # Get admin ID from context if not provided
        if admin_id is None:
            admin_id = getattr(g, 'admin_id', 0)
        
        # Generate timestamp and random data
        timestamp = int(datetime.now(timezone.utc).timestamp())
        random_data = secrets.token_bytes(16)
        
        # Create token payload
        payload = f"{admin_id}:{timestamp}:{random_data.hex()}"
        
        # Generate HMAC signature
        signature = hmac.new(
            CSRF_SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine payload and signature
        token = f"{payload}:{signature}"
        
        # Base64 encode for safe transport
        import base64
        return base64.b64encode(token.encode()).decode()
    
    @staticmethod
    def verify_csrf_token(token: str, admin_id: Optional[int] = None) -> bool:
        """
        Verify a CSRF token
        
        Args:
            token: Base64-encoded CSRF token
            admin_id: Admin ID to verify against (optional)
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Get admin ID from context if not provided
            if admin_id is None:
                admin_id = getattr(g, 'admin_id', 0)
            
            # Base64 decode
            import base64
            decoded_token = base64.b64decode(token.encode()).decode()
            
            # Split token parts
            parts = decoded_token.split(':')
            if len(parts) != 4:
                return False
            
            token_admin_id, timestamp_str, random_data, signature = parts
            
            # Verify admin ID matches
            if int(token_admin_id) != admin_id:
                return False
            
            # Check token age
            timestamp = int(timestamp_str)
            current_time = int(datetime.now(timezone.utc).timestamp())
            token_age_minutes = (current_time - timestamp) / 60
            
            if token_age_minutes > CSRF_TOKEN_TIMEOUT_MINUTES:
                return False
            
            # Verify HMAC signature
            payload = f"{token_admin_id}:{timestamp_str}:{random_data}"
            expected_signature = hmac.new(
                CSRF_SECRET_KEY.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False
    
    @staticmethod
    def get_csrf_token_from_request() -> Optional[str]:
        """Extract CSRF token from request (header or form data)"""
        # Check X-CSRF-Token header first
        token = request.headers.get('X-CSRF-Token')
        
        if not token:
            # Check form data
            token = request.form.get('csrf_token')
        
        if not token:
            # Check JSON data
            json_data = request.get_json(silent=True)
            if json_data:
                token = json_data.get('csrf_token')
        
        return token
    
    @staticmethod
    def validate_csrf() -> bool:
        """Validate CSRF token from current request"""
        # Skip CSRF validation for GET requests (read-only)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Get token from request
        token = CSRFProtection.get_csrf_token_from_request()
        
        if not token:
            return False
        
        # Verify token
        return CSRFProtection.verify_csrf_token(token)

def csrf_protect(f):
    """
    Decorator to protect admin endpoints with CSRF validation
    
    Usage:
        @csrf_protect
        def admin_action():
            pass
    """
    from functools import wraps
    from flask import jsonify
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not CSRFProtection.validate_csrf():
            return jsonify({
                'error': 'CSRF token validation failed',
                'message': 'Invalid or missing CSRF token'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def generate_csrf_token_for_template():
    """Generate CSRF token for use in templates"""
    return CSRFProtection.generate_csrf_token()
