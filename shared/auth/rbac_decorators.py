"""
Role-Based Access Control (RBAC) Decorators
Provides permission-based access control for admin endpoints
"""

from functools import wraps
from typing import List, Union
from flask import request, jsonify, g

from .admin_roles import Permission, AdminRole, can_access_endpoint
from .jwt_handler import verify_admin_token

def require_permissions(*permissions: Permission):
    """
    Decorator to require specific permissions for admin endpoints
    
    Usage:
        @require_permissions(Permission.PLAYER_BAN, Permission.PLAYER_WARN)
        def ban_player():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get authorization header
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
                    
                    # Check permissions
                    admin_role = AdminRole(admin.role)
                    has_access = can_access_endpoint(
                        admin_role, 
                        admin.is_super_admin, 
                        list(permissions)
                    )
                    
                    if not has_access:
                        return jsonify({
                            'error': 'Insufficient permissions',
                            'required_permissions': [p.value for p in permissions],
                            'user_role': admin.role
                        }), 403
                    
                    # Set admin context with role information
                    g.admin_id = admin.id
                    g.admin_email = admin.email
                    g.admin_username = admin.username
                    g.admin_role = admin_role
                    g.is_super_admin = admin.is_super_admin
                    g.is_admin = True
                    
                    # Update last login timestamp
                    from datetime import datetime, timezone
                    admin.last_login = datetime.now(timezone.utc)
                    session.commit()
                    
                    return f(*args, **kwargs)
                    
            except Exception as e:
                return jsonify({'error': 'Database error during permission verification'}), 500
        
        return decorated_function
    return decorator

def require_role(*roles: AdminRole):
    """
    Decorator to require specific admin roles
    
    Usage:
        @require_role(AdminRole.ADMIN, AdminRole.SUPER_ADMIN)
        def admin_only_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get authorization header
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
                    
                    # Check role access
                    admin_role = AdminRole(admin.role)
                    
                    # Super admins can access everything
                    if admin.is_super_admin:
                        has_access = True
                    else:
                        has_access = admin_role in roles
                    
                    if not has_access:
                        return jsonify({
                            'error': 'Insufficient role level',
                            'required_roles': [r.value for r in roles],
                            'user_role': admin.role
                        }), 403
                    
                    # Set admin context
                    g.admin_id = admin.id
                    g.admin_email = admin.email
                    g.admin_username = admin.username
                    g.admin_role = admin_role
                    g.is_super_admin = admin.is_super_admin
                    g.is_admin = True
                    
                    # Update last login timestamp
                    from datetime import datetime, timezone
                    admin.last_login = datetime.now(timezone.utc)
                    session.commit()
                    
                    return f(*args, **kwargs)
                    
            except Exception as e:
                return jsonify({'error': 'Database error during role verification'}), 500
        
        return decorated_function
    return decorator

def super_admin_required(f):
    """
    Decorator to require super admin access only
    
    Usage:
        @super_admin_required
        def super_admin_only():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get authorization header
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
                
                # Check super admin status
                if not admin.is_super_admin:
                    return jsonify({
                        'error': 'Super admin access required',
                        'user_role': admin.role
                    }), 403
                
                # Set admin context
                g.admin_id = admin.id
                g.admin_email = admin.email
                g.admin_username = admin.username
                g.admin_role = AdminRole(admin.role)
                g.is_super_admin = admin.is_super_admin
                g.is_admin = True
                
                # Update last login timestamp
                from datetime import datetime, timezone
                admin.last_login = datetime.now(timezone.utc)
                session.commit()
                
                return f(*args, **kwargs)
                
        except Exception as e:
            return jsonify({'error': 'Database error during super admin verification'}), 500
    
    return decorated_function

# Convenience decorators for common permission combinations
def player_management_required(f):
    """Require player management permissions"""
    return require_permissions(Permission.PLAYER_VIEW, Permission.PLAYER_EDIT)(f)

def console_management_required(f):
    """Require console management permissions"""
    return require_permissions(Permission.CONSOLE_VIEW, Permission.CONSOLE_MANAGE)(f)

def card_management_required(f):
    """Require card management permissions"""
    return require_permissions(Permission.CARD_VIEW, Permission.CARD_EDIT)(f)

def system_admin_required(f):
    """Require system administration permissions"""
    return require_permissions(Permission.SYSTEM_CONFIG, Permission.SYSTEM_MAINTENANCE)(f)














