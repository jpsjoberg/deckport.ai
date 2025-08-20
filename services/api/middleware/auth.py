"""
Authentication middleware
"""

from functools import wraps
from flask import request, jsonify, g
from shared.auth.jwt_handler import verify_token, get_current_user_id

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token required'}), 401
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in g for use in route handlers
        g.current_user_id = payload.get('user_id')
        g.current_user_email = payload.get('email')
        g.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                pass
        
        # Verify token if present
        if token:
            payload = verify_token(token)
            if payload:
                g.current_user_id = payload.get('user_id')
                g.current_user_email = payload.get('email')
                g.token_payload = payload
        
        # Set defaults if no valid token
        if not hasattr(g, 'current_user_id'):
            g.current_user_id = None
            g.current_user_email = None
            g.token_payload = None
        
        return f(*args, **kwargs)
    
    return decorated_function
