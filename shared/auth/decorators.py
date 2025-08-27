"""
Authentication decorators for API routes
"""

from functools import wraps
from flask import request, jsonify, g
from .jwt_handler import verify_token

def admin_required(f):
    """Decorator to require admin authentication with proper JWT verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
        
        # Verify admin JWT token
        from .jwt_handler import verify_admin_token
        admin_payload = verify_admin_token(token)
        
        if not admin_payload:
            return jsonify({'error': 'Invalid or expired admin token'}), 401
        
        # Verify admin exists and is active in database
        from shared.database.connection import SessionLocal
        from shared.models.base import Admin
        
        try:
            with SessionLocal() as session:
                admin = session.query(Admin).filter(
                    Admin.id == admin_payload['admin_id'],
                    Admin.is_active == True
                ).first()
                
                if not admin:
                    return jsonify({'error': 'Admin account not found or inactive'}), 403
                
                # Set admin context
                g.admin_id = admin.id
                g.admin_email = admin.email
                g.admin_username = admin.username
                g.is_super_admin = admin.is_super_admin
                g.is_admin = True
                
                # Update last login timestamp
                from datetime import datetime, timezone
                admin.last_login = datetime.now(timezone.utc)
                session.commit()
                
                return f(*args, **kwargs)
                
        except Exception as e:
            return jsonify({'error': 'Database error during admin verification'}), 500
    
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
        
        # Load player from database
        from shared.database.connection import SessionLocal
        from shared.models.base import Player
        
        try:
            with SessionLocal() as session:
                player = session.query(Player).filter(Player.id == payload.get('user_id')).first()
                if not player:
                    return jsonify({'error': 'Player not found'}), 401
                
                # Set player context
                g.user_id = payload.get('user_id')
                g.email = payload.get('email')
                g.current_player = player
                
                return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Database error'}), 500
    
    return decorated_function

def optional_player_auth(f):
    """Decorator for optional player authentication (allows guest access)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # No auth header = guest access
        if not auth_header:
            g.current_player = None
            g.user_id = None
            g.email = None
            return f(*args, **kwargs)
        
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                # Invalid format but allow guest access
                g.current_player = None
                g.user_id = None
                g.email = None
                return f(*args, **kwargs)
        except ValueError:
            # Invalid format but allow guest access
            g.current_player = None
            g.user_id = None
            g.email = None
            return f(*args, **kwargs)
        
        payload = verify_token(token)
        if not payload or payload.get('type') != 'access':
            # Invalid token but allow guest access
            g.current_player = None
            g.user_id = None
            g.email = None
            return f(*args, **kwargs)
        
        # Load player from database
        from shared.database.connection import SessionLocal
        from shared.models.base import Player
        
        try:
            with SessionLocal() as session:
                player = session.query(Player).filter(Player.id == payload.get('user_id')).first()
                if player:
                    # Set authenticated player context
                    g.user_id = payload.get('user_id')
                    g.email = payload.get('email')
                    g.current_player = player
                else:
                    # Player not found, allow guest access
                    g.current_player = None
                    g.user_id = None
                    g.email = None
                
                return f(*args, **kwargs)
        except Exception:
            # Database error, allow guest access
            g.current_player = None
            g.user_id = None
            g.email = None
            return f(*args, **kwargs)
    
    return decorated_function
