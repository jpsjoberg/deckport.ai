"""
Automatic RBAC decorator that determines permissions based on endpoint
Integrates with the permission mapping system for seamless authorization
"""

from functools import wraps
from flask import request, jsonify, g
from typing import List, Optional
from .admin_roles import Permission, AdminRole
from .permission_mapping import get_endpoint_permissions, requires_super_admin
from .rbac_decorators import can_access_endpoint
from shared.auth.jwt_handler import verify_admin_token
from shared.database.connection import SessionLocal
from shared.models.base import Admin
from shared.security import AdminAuditLogger
import logging

logger = logging.getLogger(__name__)

def auto_rbac_required(
    override_permissions: Optional[List[Permission]] = None,
    require_super_admin: Optional[bool] = None,
    rate_limit_type: str = None
):
    """
    Automatic RBAC decorator that determines permissions from endpoint
    
    Args:
        override_permissions: Override automatic permission detection
        require_super_admin: Override super admin requirement detection
        rate_limit_type: Rate limit type for the endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get endpoint and method
            endpoint = request.endpoint or request.path
            method = request.method
            
            # Determine required permissions
            if override_permissions is not None:
                required_permissions = override_permissions
            else:
                required_permissions = get_endpoint_permissions(endpoint, method)
            
            # Determine super admin requirement
            if require_super_admin is not None:
                needs_super_admin = require_super_admin
            else:
                needs_super_admin = requires_super_admin(endpoint)
            
            # Authentication check
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                AdminAuditLogger.log_security_event(
                    'missing_auth_header',
                    'medium',
                    {'endpoint': endpoint, 'method': method}
                )
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
                    'invalid_admin_token',
                    'high',
                    {'endpoint': endpoint, 'method': method}
                )
                return jsonify({'error': 'Invalid or expired admin token'}), 401
            
            # Database verification and permission checking
            try:
                with SessionLocal() as session:
                    admin = session.query(Admin).filter(
                        Admin.id == admin_payload['admin_id'],
                        Admin.is_active == True
                    ).first()
                    
                    if not admin:
                        AdminAuditLogger.log_security_event(
                            'inactive_admin_access',
                            'high',
                            {
                                'admin_id': admin_payload.get('admin_id'),
                                'endpoint': endpoint
                            }
                        )
                        return jsonify({'error': 'Admin account not found or inactive'}), 403
                    
                    # Check super admin requirement
                    if needs_super_admin and not admin.is_super_admin:
                        AdminAuditLogger.log_admin_action(
                            'unauthorized_super_admin_attempt',
                            details={
                                'admin_id': admin.id,
                                'endpoint': endpoint,
                                'method': method,
                                'required_permissions': [p.value for p in required_permissions]
                            },
                            success=False
                        )
                        return jsonify({
                            'error': 'Super admin privileges required',
                            'endpoint': endpoint
                        }), 403
                    
                    # Check permissions
                    if required_permissions:
                        admin_role = AdminRole(admin.role) if admin.role in [r.value for r in AdminRole] else AdminRole.ADMIN
                        has_access = can_access_endpoint(
                            admin_role,
                            admin.is_super_admin,
                            required_permissions
                        )
                        
                        if not has_access:
                            AdminAuditLogger.log_admin_action(
                                'insufficient_permissions',
                                details={
                                    'admin_id': admin.id,
                                    'admin_role': admin.role,
                                    'endpoint': endpoint,
                                    'method': method,
                                    'required_permissions': [p.value for p in required_permissions],
                                    'is_super_admin': admin.is_super_admin
                                },
                                success=False
                            )
                            return jsonify({
                                'error': 'Insufficient permissions',
                                'required_permissions': [p.value for p in required_permissions],
                                'user_role': admin.role,
                                'endpoint': endpoint
                            }), 403
                    
                    # Set admin context
                    g.admin_id = admin.id
                    g.admin_email = admin.email
                    g.admin_username = admin.username
                    g.admin_role = AdminRole(admin.role) if admin.role in [r.value for r in AdminRole] else AdminRole.ADMIN
                    g.is_super_admin = admin.is_super_admin
                    g.is_admin = True
                    
                    # Update last login timestamp
                    from datetime import datetime, timezone
                    admin.last_login = datetime.now(timezone.utc)
                    session.commit()
                    
                    # Log successful access for sensitive operations
                    if needs_super_admin or any(p in [
                        Permission.PLAYER_BAN, Permission.CONSOLE_REMOTE, 
                        Permission.SYSTEM_MAINTENANCE, Permission.ADMIN_DELETE
                    ] for p in required_permissions):
                        AdminAuditLogger.log_admin_action(
                            f'sensitive_access_{endpoint.replace("/", "_").replace("-", "_")}',
                            details={
                                'endpoint': endpoint,
                                'method': method,
                                'permissions_used': [p.value for p in required_permissions],
                                'super_admin_required': needs_super_admin
                            }
                        )
                    
                    # Execute the protected function
                    return f(*args, **kwargs)
                    
            except Exception as e:
                logger.error(f"Database error during RBAC verification: {e}")
                return jsonify({'error': 'Database error during authorization'}), 500
        
        return decorated_function
    return decorator

# Convenience decorators for common patterns
def admin_view_required(f):
    """Decorator for admin view operations"""
    return auto_rbac_required()(f)

def admin_manage_required(permissions: List[Permission]):
    """Decorator for admin management operations"""
    def decorator(f):
        return auto_rbac_required(override_permissions=permissions)(f)
    return decorator

def super_admin_only(f):
    """Decorator for super admin only operations"""
    return auto_rbac_required(require_super_admin=True)(f)

def player_management_required(permission: Permission):
    """Decorator for player management operations"""
    return auto_rbac_required(override_permissions=[permission])

def console_management_required(permission: Permission):
    """Decorator for console management operations"""
    return auto_rbac_required(override_permissions=[permission])

def system_admin_required(permission: Permission):
    """Decorator for system administration operations"""
    return auto_rbac_required(override_permissions=[permission])
