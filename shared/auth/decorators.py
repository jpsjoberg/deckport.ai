"""
Authentication decorators for API routes
"""

from functools import wraps
from flask import request, jsonify, g
from .jwt_handler import verify_token

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, we'll use a simple admin token approach
        # In production, this should be proper JWT with admin roles
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            # Extract token from "Bearer <token>" format
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({'error': 'Invalid authorization header format'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # For MVP, we'll accept a simple admin token
        # TODO: Implement proper JWT-based admin authentication
        admin_token = "admin-dev-token-change-in-production"
        
        if token == admin_token:
            # Set admin context
            g.admin_id = 1
            g.is_admin = True
            return f(*args, **kwargs)
        
        # Try to verify as regular JWT token and check for admin role
        payload = verify_token(token)
        if payload and payload.get('role') == 'admin':
            g.admin_id = payload.get('user_id')
            g.is_admin = True
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Admin access required'}), 403
    
    return decorated_function

def device_required(f):
    """Decorator to require device authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({'error': 'Invalid authorization header format'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('type') != 'device':
            return jsonify({'error': 'Invalid device token'}), 401
        
        # Set device context
        g.device_uid = payload.get('device_uid')
        g.console_id = payload.get('console_id')
        return f(*args, **kwargs)
    
    return decorated_function

def player_required(f):
    """Decorator to require player authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({'error': 'Invalid authorization header format'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        payload = verify_token(token)
        if not payload or payload.get('type') != 'access':
            return jsonify({'error': 'Invalid player token'}), 401
        
        # Set player context
        g.user_id = payload.get('user_id')
        g.email = payload.get('email')
        return f(*args, **kwargs)
    
    return decorated_function
