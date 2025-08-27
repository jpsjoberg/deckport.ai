"""
Permission mapping for admin routes
Maps each admin endpoint to the required permissions for granular RBAC
"""

from typing import Dict, List, Set
from .admin_roles import Permission

class AdminEndpointPermissions:
    """Maps admin endpoints to required permissions"""
    
    # Endpoint permission mapping
    ENDPOINT_PERMISSIONS: Dict[str, List[Permission]] = {
        
        # === SECURITY MONITORING ===
        '/v1/admin/security/audit-logs': [Permission.SYSTEM_LOGS],
        '/v1/admin/security/security-events': [Permission.SYSTEM_LOGS],
        '/v1/admin/security/admin-activity': [Permission.ADMIN_VIEW],
        '/v1/admin/security/admin-sessions': [Permission.ADMIN_VIEW],
        '/v1/admin/security/rate-limits/<identifier>': [Permission.SYSTEM_CONFIG],
        '/v1/admin/security/rate-limits/<identifier>/reset': [Permission.SYSTEM_CONFIG],
        '/v1/admin/security/ip-access-control': [Permission.SYSTEM_CONFIG],
        '/v1/admin/security/ip-access-control/allowlist': [Permission.SYSTEM_CONFIG],
        '/v1/admin/security/ip-access-control/blocklist': [Permission.SYSTEM_CONFIG],
        '/v1/admin/security/dashboard': [Permission.SYSTEM_HEALTH],
        
        # === DASHBOARD & STATS ===
        '/v1/admin/dashboard/stats': [Permission.SYSTEM_HEALTH],
        '/v1/admin/dashboard/live-data': [Permission.SYSTEM_HEALTH],
        '/v1/admin/dashboard/console-activity': [Permission.CONSOLE_VIEW],
        
        # === DEVICE/CONSOLE MANAGEMENT ===
        '/v1/admin/devices': [Permission.CONSOLE_VIEW],
        '/v1/admin/devices/<device_uid>/approve': [Permission.CONSOLE_APPROVE],
        '/v1/admin/devices/<device_uid>/reject': [Permission.CONSOLE_APPROVE],
        '/v1/admin/devices/<device_uid>/reboot': [Permission.CONSOLE_REMOTE],
        '/v1/admin/devices/<device_uid>/shutdown': [Permission.CONSOLE_REMOTE],
        '/v1/admin/devices/<device_uid>/ping': [Permission.CONSOLE_MANAGE],
        
        # === PLAYER MANAGEMENT ===
        '/v1/admin/players/stats': [Permission.PLAYER_VIEW],
        '/v1/admin/players': [Permission.PLAYER_VIEW],
        '/v1/admin/players/<int:player_id>': [Permission.PLAYER_VIEW],
        '/v1/admin/players/<int:player_id>/ban': [Permission.PLAYER_BAN],
        '/v1/admin/players/<int:player_id>/unban': [Permission.PLAYER_BAN],
        '/v1/admin/players/<int:player_id>/warn': [Permission.PLAYER_WARN],
        '/v1/admin/players/<int:player_id>/notes': [Permission.PLAYER_EDIT],
        '/v1/admin/players/<int:player_id>/reset-password': [Permission.PLAYER_EDIT],
        '/v1/admin/players/support/tickets': [Permission.PLAYER_SUPPORT],
        '/v1/admin/players/moderation/reports': [Permission.PLAYER_VIEW],
        '/v1/admin/players/moderation/reports/<int:report_id>/resolve': [Permission.PLAYER_WARN],
        
        # === GAME OPERATIONS ===
        '/v1/admin/game-operations/dashboard': [Permission.GAME_VIEW],
        '/v1/admin/game-operations/matches/live': [Permission.GAME_MATCHES],
        '/v1/admin/game-operations/matches/<match_id>': [Permission.GAME_MATCHES],
        '/v1/admin/game-operations/matches/<match_id>/terminate': [Permission.GAME_MATCHES],
        '/v1/admin/game-operations/matchmaking/queue': [Permission.GAME_VIEW],
        '/v1/admin/game-operations/tournaments': [Permission.GAME_TOURNAMENTS],
        '/v1/admin/game-operations/balance/cards': [Permission.GAME_BALANCE],
        '/v1/admin/game-operations/balance/cards/<product_sku>': [Permission.GAME_BALANCE],
        '/v1/admin/game-operations/analytics/player-activity': [Permission.ANALYTICS_PLAYERS],
        '/v1/admin/game-operations/system/maintenance': [Permission.SYSTEM_MAINTENANCE],
        
        # === TOURNAMENTS ===
        '/v1/admin/tournaments/stats': [Permission.GAME_TOURNAMENTS],
        '/v1/admin/tournaments': [Permission.GAME_TOURNAMENTS],
        '/v1/admin/tournaments/<int:tournament_id>': [Permission.GAME_TOURNAMENTS],
        '/v1/admin/tournaments/<int:tournament_id>/start': [Permission.GAME_TOURNAMENTS],
        
        # === SHOP MANAGEMENT ===
        '/v1/admin/shop/stats': [Permission.SHOP_VIEW],
        '/v1/admin/shop/products': [Permission.SHOP_PRODUCTS],
        '/v1/admin/shop/orders': [Permission.SHOP_ORDERS],
        '/v1/admin/shop/inventory': [Permission.SHOP_INVENTORY],
        
        # === NFC CARD MANAGEMENT ===
        '/v1/admin/nfc/cards': [Permission.NFC_VIEW],
        '/v1/admin/nfc/cards/produce': [Permission.NFC_PRODUCE],
        '/v1/admin/nfc/cards/<card_id>/revoke': [Permission.NFC_REVOKE],
        '/v1/admin/nfc/batches': [Permission.NFC_MANAGE],
        
        # === CARD MANAGEMENT ===
        '/v1/admin/cards': [Permission.CARD_VIEW],
        '/v1/admin/cards/create': [Permission.CARD_CREATE],
        '/v1/admin/cards/<card_id>/edit': [Permission.CARD_EDIT],
        '/v1/admin/cards/<card_id>/publish': [Permission.CARD_PUBLISH],
        
        # === ANALYTICS ===
        '/v1/admin/analytics/revenue': [Permission.ANALYTICS_REVENUE],
        '/v1/admin/analytics/player-behavior': [Permission.ANALYTICS_PLAYERS],
        '/v1/admin/analytics/card-usage': [Permission.ANALYTICS_SYSTEM],
        '/v1/admin/analytics/system-metrics': [Permission.ANALYTICS_SYSTEM],
        '/v1/admin/analytics/dashboard-summary': [Permission.ANALYTICS_VIEW],
        
        # === COMMUNICATIONS ===
        '/v1/admin/communications/announcements': [Permission.COMM_MANAGE],
        '/v1/admin/communications/email-campaigns': [Permission.COMM_EMAIL],
        '/v1/admin/communications/social-metrics': [Permission.COMM_VIEW],
        '/v1/admin/communications/social-post': [Permission.COMM_BROADCAST],
        '/v1/admin/communications/dashboard-summary': [Permission.COMM_VIEW],
        
        # === ALERTS ===
        '/v1/admin/alerts': [Permission.SYSTEM_HEALTH],
        '/v1/admin/alerts/summary': [Permission.SYSTEM_HEALTH],
        '/v1/admin/alerts/<alert_id>/acknowledge': [Permission.SYSTEM_HEALTH],
        '/v1/admin/alerts/health-check': [Permission.SYSTEM_HEALTH],
        
        # === ARENAS ===
        '/v1/admin/arenas': [Permission.GAME_VIEW],
        '/v1/admin/arenas/<int:arena_id>': [Permission.GAME_VIEW],
        '/v1/admin/arenas/assign': [Permission.GAME_MATCHES],
    }
    
    # HTTP method-specific permissions (if different from default)
    METHOD_PERMISSIONS: Dict[str, Dict[str, List[Permission]]] = {
        # Example: Different permissions for GET vs POST on same endpoint
        '/v1/admin/players': {
            'GET': [Permission.PLAYER_VIEW],
            'POST': [Permission.PLAYER_EDIT],  # If creating players
        },
        '/v1/admin/communications/announcements': {
            'GET': [Permission.COMM_VIEW],
            'POST': [Permission.COMM_MANAGE],
        },
        '/v1/admin/analytics/revenue': {
            'GET': [Permission.ANALYTICS_VIEW],
            'POST': [Permission.ANALYTICS_REVENUE],  # If generating reports
        },
    }
    
    # Super admin only endpoints
    SUPER_ADMIN_ONLY: Set[str] = {
        '/v1/admin/security/rate-limits/<identifier>/reset',
        '/v1/admin/security/ip-access-control/allowlist',
        '/v1/admin/security/ip-access-control/blocklist',
        '/v1/admin/game-operations/system/maintenance',
        '/v1/admin/admins',  # Admin user management
        '/v1/admin/admins/create',
        '/v1/admin/admins/<int:admin_id>/deactivate',
    }
    
    @classmethod
    def get_required_permissions(cls, endpoint: str, method: str = 'GET') -> List[Permission]:
        """
        Get required permissions for an endpoint and HTTP method
        
        Args:
            endpoint: The endpoint path (e.g., '/v1/admin/players')
            method: HTTP method (GET, POST, PUT, DELETE)
            
        Returns:
            List of required permissions
        """
        # Check method-specific permissions first
        if endpoint in cls.METHOD_PERMISSIONS:
            method_perms = cls.METHOD_PERMISSIONS[endpoint].get(method)
            if method_perms:
                return method_perms
        
        # Fall back to general endpoint permissions
        return cls.ENDPOINT_PERMISSIONS.get(endpoint, [])
    
    @classmethod
    def is_super_admin_only(cls, endpoint: str) -> bool:
        """Check if endpoint requires super admin privileges"""
        return endpoint in cls.SUPER_ADMIN_ONLY
    
    @classmethod
    def get_endpoint_pattern(cls, actual_endpoint: str) -> str:
        """
        Match actual endpoint to pattern (handles dynamic segments)
        
        Args:
            actual_endpoint: Actual endpoint like '/v1/admin/players/123'
            
        Returns:
            Pattern like '/v1/admin/players/<int:player_id>'
        """
        # Simple pattern matching - in production, use more sophisticated routing
        for pattern in cls.ENDPOINT_PERMISSIONS.keys():
            if cls._matches_pattern(actual_endpoint, pattern):
                return pattern
        
        return actual_endpoint
    
    @classmethod
    def _matches_pattern(cls, endpoint: str, pattern: str) -> bool:
        """Check if endpoint matches pattern with dynamic segments"""
        endpoint_parts = endpoint.split('/')
        pattern_parts = pattern.split('/')
        
        if len(endpoint_parts) != len(pattern_parts):
            return False
        
        for ep, pp in zip(endpoint_parts, pattern_parts):
            if pp.startswith('<') and pp.endswith('>'):
                # Dynamic segment - matches anything
                continue
            elif ep != pp:
                return False
        
        return True

# Convenience functions for easy access
def get_endpoint_permissions(endpoint: str, method: str = 'GET') -> List[Permission]:
    """Get required permissions for an endpoint"""
    pattern = AdminEndpointPermissions.get_endpoint_pattern(endpoint)
    return AdminEndpointPermissions.get_required_permissions(pattern, method)

def requires_super_admin(endpoint: str) -> bool:
    """Check if endpoint requires super admin"""
    pattern = AdminEndpointPermissions.get_endpoint_pattern(endpoint)
    return AdminEndpointPermissions.is_super_admin_only(pattern)
