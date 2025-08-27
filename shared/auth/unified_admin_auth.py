"""
Unified Admin Authentication System
Consolidates all admin authentication decorators into a single, consistent system
"""

from functools import wraps
from flask import request, jsonify, g
from typing import List, Optional, Union
from .admin_roles import Permission, AdminRole
from .auto_rbac_decorator import auto_rbac_required
from .jwt_handler import verify_admin_token
from shared.database.connection import SessionLocal
from shared.models.base import Admin
from shared.security import AdminAuditLogger
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# UNIFIED ADMIN AUTHENTICATION DECORATORS
# =============================================================================

def admin_auth_required(
    permissions: Optional[List[Permission]] = None,
    require_super_admin: bool = False,
    allow_legacy_token: bool = True
):
    """
    Unified admin authentication decorator
    
    This is the single decorator that should be used for all admin authentication.
    It replaces:
    - @admin_required
    - @require_admin_token  
    - @auto_rbac_required (when you need custom options)
    
    Args:
        permissions: Required permissions (if None, uses automatic detection)
        require_super_admin: Whether super admin is required
        allow_legacy_token: Whether to allow legacy token verification (for migration)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use the auto RBAC system with the specified parameters
            rbac_decorator = auto_rbac_required(
                override_permissions=permissions,
                require_super_admin=require_super_admin
            )
            
            # Apply the RBAC decorator
            return rbac_decorator(f)(*args, **kwargs)
        
        return decorated_function
    return decorator

# =============================================================================
# CONVENIENCE DECORATORS
# =============================================================================

def admin_required(f):
    """
    Basic admin authentication (backward compatibility)
    Uses automatic permission detection
    """
    return admin_auth_required()(f)

def super_admin_required(f):
    """
    Super admin only authentication
    """
    return admin_auth_required(require_super_admin=True)(f)

def admin_permissions_required(*permissions: Permission):
    """
    Admin authentication with specific permissions
    
    Usage:
        @admin_permissions_required(Permission.PLAYER_BAN, Permission.PLAYER_WARN)
        def ban_player():
            pass
    """
    def decorator(f):
        return admin_auth_required(permissions=list(permissions))(f)
    return decorator

# =============================================================================
# LEGACY COMPATIBILITY LAYER
# =============================================================================

def require_admin_token(f):
    """
    Legacy decorator compatibility layer
    
    This maintains backward compatibility with the old require_admin_token decorator
    while using the new unified authentication system under the hood.
    
    DEPRECATED: Use @admin_auth_required() instead
    """
    logger.warning(f"Using deprecated @require_admin_token decorator in {f.__name__}. "
                  f"Please migrate to @admin_auth_required()")
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Legacy token verification for backward compatibility
        try:
            # Try the old verification method first
            auth_result = verify_admin_token(request)
            if auth_result and auth_result.get('valid'):
                # Set basic context for legacy compatibility
                g.admin_id = auth_result.get('admin_id', 1)
                g.admin_email = auth_result.get('email', 'unknown')
                g.is_admin = True
                
                # Log legacy usage for migration tracking
                AdminAuditLogger.log_admin_action(
                    'legacy_auth_decorator_used',
                    details={
                        'function': f.__name__,
                        'endpoint': request.endpoint,
                        'migration_needed': True
                    }
                )
                
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Admin authentication required'}), 401
                
        except Exception as e:
            logger.error(f"Legacy authentication error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

# =============================================================================
# MIGRATION UTILITIES
# =============================================================================

class AuthDecoratorMigration:
    """Utilities for migrating authentication decorators"""
    
    @staticmethod
    def get_legacy_decorator_usage():
        """Get statistics on legacy decorator usage"""
        # This would be implemented to scan codebase for legacy decorators
        pass
    
    @staticmethod
    def suggest_migration(function_name: str, endpoint: str) -> dict:
        """Suggest appropriate migration for a function"""
        suggestions = {
            'current': '@require_admin_token',
            'recommended': '@admin_auth_required()',
            'reasoning': 'Uses unified authentication with automatic permission detection'
        }
        
        # Analyze endpoint to suggest specific permissions
        if 'player' in endpoint.lower():
            if 'ban' in endpoint.lower():
                suggestions['recommended'] = '@admin_permissions_required(Permission.PLAYER_BAN)'
            elif 'view' in endpoint.lower() or 'get' in function_name.lower():
                suggestions['recommended'] = '@admin_permissions_required(Permission.PLAYER_VIEW)'
            else:
                suggestions['recommended'] = '@admin_permissions_required(Permission.PLAYER_EDIT)'
        
        elif 'device' in endpoint.lower() or 'console' in endpoint.lower():
            if 'reboot' in endpoint.lower() or 'shutdown' in endpoint.lower():
                suggestions['recommended'] = '@admin_permissions_required(Permission.CONSOLE_REMOTE)'
            elif 'approve' in endpoint.lower():
                suggestions['recommended'] = '@admin_permissions_required(Permission.CONSOLE_APPROVE)'
            else:
                suggestions['recommended'] = '@admin_permissions_required(Permission.CONSOLE_VIEW)'
        
        elif 'security' in endpoint.lower():
            suggestions['recommended'] = '@super_admin_required'
            suggestions['reasoning'] = 'Security operations should be super admin only'
        
        return suggestions

# =============================================================================
# DECORATOR REGISTRY
# =============================================================================

class AdminDecoratorRegistry:
    """Registry of all admin authentication decorators for consistency"""
    
    # Primary decorators (recommended)
    PRIMARY_DECORATORS = {
        'admin_auth_required': admin_auth_required,
        'admin_permissions_required': admin_permissions_required,
        'super_admin_required': super_admin_required,
    }
    
    # Compatibility decorators (for migration)
    COMPATIBILITY_DECORATORS = {
        'admin_required': admin_required,
        'require_admin_token': require_admin_token,
    }
    
    # Deprecated decorators (should be migrated)
    DEPRECATED_DECORATORS = {
        'require_admin_token': 'Use @admin_auth_required() instead',
    }
    
    @classmethod
    def get_recommended_decorator(cls, use_case: str) -> str:
        """Get recommended decorator for a use case"""
        recommendations = {
            'basic_admin': '@admin_auth_required()',
            'specific_permissions': '@admin_permissions_required(Permission.X, Permission.Y)',
            'super_admin_only': '@super_admin_required',
            'automatic_detection': '@admin_auth_required()',
        }
        return recommendations.get(use_case, '@admin_auth_required()')

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Primary decorators
    'admin_auth_required',
    'admin_permissions_required', 
    'super_admin_required',
    
    # Compatibility decorators
    'admin_required',
    'require_admin_token',
    
    # Utilities
    'AuthDecoratorMigration',
    'AdminDecoratorRegistry',
]
