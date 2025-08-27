"""
Admin Role-Based Access Control (RBAC) System
Defines admin roles, permissions, and access control logic
"""

from enum import Enum
from typing import Set, Dict, List
from dataclasses import dataclass

class AdminRole(str, Enum):
    """Admin role levels with hierarchical permissions"""
    SUPER_ADMIN = "super_admin"      # Full system access
    ADMIN = "admin"                  # Standard admin access
    MODERATOR = "moderator"          # Player management and content moderation
    SUPPORT = "support"              # Player support and basic operations
    VIEWER = "viewer"                # Read-only access for monitoring

class Permission(str, Enum):
    """Granular permissions for admin operations"""
    
    # System Administration
    SYSTEM_CONFIG = "system.config"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_LOGS = "system.logs"
    SYSTEM_HEALTH = "system.health"
    
    # Admin Management
    ADMIN_CREATE = "admin.create"
    ADMIN_EDIT = "admin.edit"
    ADMIN_DELETE = "admin.delete"
    ADMIN_VIEW = "admin.view"
    ADMIN_ROLES = "admin.roles"
    
    # Console Management
    CONSOLE_APPROVE = "console.approve"
    CONSOLE_MANAGE = "console.manage"
    CONSOLE_REMOTE = "console.remote"
    CONSOLE_VIEW = "console.view"
    
    # Player Management
    PLAYER_BAN = "player.ban"
    PLAYER_WARN = "player.warn"
    PLAYER_EDIT = "player.edit"
    PLAYER_VIEW = "player.view"
    PLAYER_SUPPORT = "player.support"
    
    # Card Management
    CARD_CREATE = "card.create"
    CARD_EDIT = "card.edit"
    CARD_PUBLISH = "card.publish"
    CARD_VIEW = "card.view"
    
    # NFC Management
    NFC_PRODUCE = "nfc.produce"
    NFC_REVOKE = "nfc.revoke"
    NFC_MANAGE = "nfc.manage"
    NFC_VIEW = "nfc.view"
    
    # Game Operations
    GAME_TOURNAMENTS = "game.tournaments"
    GAME_MATCHES = "game.matches"
    GAME_BALANCE = "game.balance"
    GAME_VIEW = "game.view"
    
    # Shop Management
    SHOP_PRODUCTS = "shop.products"
    SHOP_ORDERS = "shop.orders"
    SHOP_INVENTORY = "shop.inventory"
    SHOP_VIEW = "shop.view"
    
    # Analytics & Reports
    ANALYTICS_REVENUE = "analytics.revenue"
    ANALYTICS_PLAYERS = "analytics.players"
    ANALYTICS_SYSTEM = "analytics.system"
    ANALYTICS_VIEW = "analytics.view"
    
    # Communications
    COMM_BROADCAST = "comm.broadcast"
    COMM_EMAIL = "comm.email"
    COMM_MANAGE = "comm.manage"
    COMM_VIEW = "comm.view"
    
    # Content Management System
    CMS_CREATE = "cms.create"
    CMS_EDIT = "cms.edit"
    CMS_DELETE = "cms.delete"
    CMS_PUBLISH = "cms.publish"
    CMS_VIEW = "cms.view"
    CMS_ANALYTICS = "cms.analytics"

@dataclass
class RoleDefinition:
    """Definition of an admin role with its permissions"""
    name: str
    description: str
    permissions: Set[Permission]
    color: str  # For UI display

# Role Definitions with Hierarchical Permissions
ROLE_DEFINITIONS: Dict[AdminRole, RoleDefinition] = {
    AdminRole.SUPER_ADMIN: RoleDefinition(
        name="Super Administrator",
        description="Full system access including admin management",
        permissions=set(Permission),  # All permissions
        color="red"
    ),
    
    AdminRole.ADMIN: RoleDefinition(
        name="Administrator", 
        description="Standard admin access to all operational features",
        permissions={
            # System (limited)
            Permission.SYSTEM_HEALTH, Permission.SYSTEM_LOGS,
            
            # Console Management
            Permission.CONSOLE_APPROVE, Permission.CONSOLE_MANAGE, 
            Permission.CONSOLE_REMOTE, Permission.CONSOLE_VIEW,
            
            # Player Management
            Permission.PLAYER_BAN, Permission.PLAYER_WARN, 
            Permission.PLAYER_EDIT, Permission.PLAYER_VIEW, Permission.PLAYER_SUPPORT,
            
            # Card Management
            Permission.CARD_CREATE, Permission.CARD_EDIT, 
            Permission.CARD_PUBLISH, Permission.CARD_VIEW,
            
            # NFC Management
            Permission.NFC_PRODUCE, Permission.NFC_REVOKE, 
            Permission.NFC_MANAGE, Permission.NFC_VIEW,
            
            # Game Operations
            Permission.GAME_TOURNAMENTS, Permission.GAME_MATCHES, 
            Permission.GAME_BALANCE, Permission.GAME_VIEW,
            
            # Shop Management
            Permission.SHOP_PRODUCTS, Permission.SHOP_ORDERS, 
            Permission.SHOP_INVENTORY, Permission.SHOP_VIEW,
            
            # Analytics
            Permission.ANALYTICS_REVENUE, Permission.ANALYTICS_PLAYERS, 
            Permission.ANALYTICS_SYSTEM, Permission.ANALYTICS_VIEW,
            
            # Communications
            Permission.COMM_BROADCAST, Permission.COMM_EMAIL, 
            Permission.COMM_MANAGE, Permission.COMM_VIEW,
            
            # Content Management System
            Permission.CMS_CREATE, Permission.CMS_EDIT, Permission.CMS_DELETE,
            Permission.CMS_PUBLISH, Permission.CMS_VIEW, Permission.CMS_ANALYTICS,
        },
        color="blue"
    ),
    
    AdminRole.MODERATOR: RoleDefinition(
        name="Moderator",
        description="Player management and content moderation",
        permissions={
            # System (read-only)
            Permission.SYSTEM_HEALTH,
            
            # Console (view only)
            Permission.CONSOLE_VIEW,
            
            # Player Management (full)
            Permission.PLAYER_BAN, Permission.PLAYER_WARN, 
            Permission.PLAYER_EDIT, Permission.PLAYER_VIEW, Permission.PLAYER_SUPPORT,
            
            # Card Management (limited)
            Permission.CARD_VIEW, Permission.CARD_EDIT,
            
            # NFC (view only)
            Permission.NFC_VIEW,
            
            # Game Operations (limited)
            Permission.GAME_VIEW, Permission.GAME_MATCHES,
            
            # Shop (view only)
            Permission.SHOP_VIEW,
            
            # Analytics (limited)
            Permission.ANALYTICS_PLAYERS, Permission.ANALYTICS_VIEW,
            
            # Communications (limited)
            Permission.COMM_VIEW, Permission.COMM_MANAGE,
            
            # Content Management System (limited)
            Permission.CMS_CREATE, Permission.CMS_EDIT, Permission.CMS_VIEW,
        },
        color="green"
    ),
    
    AdminRole.SUPPORT: RoleDefinition(
        name="Support Agent",
        description="Player support and basic operations",
        permissions={
            # System (health only)
            Permission.SYSTEM_HEALTH,
            
            # Console (view only)
            Permission.CONSOLE_VIEW,
            
            # Player Management (support focused)
            Permission.PLAYER_VIEW, Permission.PLAYER_SUPPORT, Permission.PLAYER_WARN,
            
            # Card Management (view only)
            Permission.CARD_VIEW,
            
            # NFC (view only)
            Permission.NFC_VIEW,
            
            # Game Operations (view only)
            Permission.GAME_VIEW,
            
            # Shop (view only)
            Permission.SHOP_VIEW,
            
            # Analytics (view only)
            Permission.ANALYTICS_VIEW,
            
            # Communications (view only)
            Permission.COMM_VIEW,
        },
        color="yellow"
    ),
    
    AdminRole.VIEWER: RoleDefinition(
        name="Viewer",
        description="Read-only access for monitoring and reporting",
        permissions={
            # System (health only)
            Permission.SYSTEM_HEALTH,
            
            # All view permissions
            Permission.CONSOLE_VIEW, Permission.PLAYER_VIEW, Permission.CARD_VIEW,
            Permission.NFC_VIEW, Permission.GAME_VIEW, Permission.SHOP_VIEW,
            Permission.ANALYTICS_VIEW, Permission.COMM_VIEW,
        },
        color="gray"
    )
}

def get_role_permissions(role: AdminRole) -> Set[Permission]:
    """Get all permissions for a given role"""
    return ROLE_DEFINITIONS[role].permissions

def has_permission(user_role: AdminRole, required_permission: Permission) -> bool:
    """Check if a role has a specific permission"""
    role_permissions = get_role_permissions(user_role)
    return required_permission in role_permissions

def get_user_permissions(user_role: AdminRole, is_super_admin: bool = False) -> Set[Permission]:
    """Get all permissions for a user, considering super admin status"""
    if is_super_admin:
        return set(Permission)  # Super admins have all permissions
    return get_role_permissions(user_role)

def can_access_endpoint(user_role: AdminRole, is_super_admin: bool, required_permissions: List[Permission]) -> bool:
    """Check if user can access an endpoint requiring specific permissions"""
    if is_super_admin:
        return True  # Super admins can access everything
    
    user_permissions = get_role_permissions(user_role)
    
    # User needs at least one of the required permissions
    return any(perm in user_permissions for perm in required_permissions)

def get_role_hierarchy_level(role: AdminRole) -> int:
    """Get numeric level for role hierarchy (higher = more permissions)"""
    hierarchy = {
        AdminRole.VIEWER: 1,
        AdminRole.SUPPORT: 2, 
        AdminRole.MODERATOR: 3,
        AdminRole.ADMIN: 4,
        AdminRole.SUPER_ADMIN: 5
    }
    return hierarchy.get(role, 0)

def can_manage_role(manager_role: AdminRole, manager_is_super: bool, target_role: AdminRole) -> bool:
    """Check if a manager can manage (create/edit/delete) users with target role"""
    if manager_is_super:
        return True  # Super admins can manage anyone
    
    manager_level = get_role_hierarchy_level(manager_role)
    target_level = get_role_hierarchy_level(target_role)
    
    # Can only manage users at lower hierarchy levels
    return manager_level > target_level



