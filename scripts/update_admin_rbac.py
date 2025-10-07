#!/usr/bin/env python3
"""
Script to automatically update all admin routes with proper RBAC decorators
"""

import os
import re
import sys
from pathlib import Path

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

def update_admin_route_file(file_path: str):
    """Update a single admin route file with RBAC decorators"""
    print(f"Updating {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if already updated
    if 'auto_rbac_decorator' in content:
        print(f"  Already updated, skipping")
        return
    
    # Add imports
    if 'from shared.auth.decorators import admin_required' in content:
        content = content.replace(
            'from shared.auth.decorators import admin_required',
            'from shared.auth.auto_rbac_decorator import auto_rbac_required\nfrom shared.auth.admin_roles import Permission'
        )
    elif 'def require_admin_token(f):' in content:
        # Handle files with custom decorators
        import_section = content.split('\n')
        for i, line in enumerate(import_section):
            if line.startswith('import logging'):
                import_section.insert(i, 'from shared.auth.auto_rbac_decorator import auto_rbac_required')
                import_section.insert(i+1, 'from shared.auth.admin_roles import Permission')
                break
        content = '\n'.join(import_section)
    
    # Replace decorators based on file type
    filename = os.path.basename(file_path)
    
    if 'admin_tournaments' in filename:
        # Tournament management
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef', '@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])\ndef', content)
    
    elif 'admin_dashboard' in filename:
        # Dashboard stats
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])\ndef', content)
    
    elif 'admin_analytics' in filename:
        # Analytics routes
        content = re.sub(r'@admin_required\ndef get_revenue', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_REVENUE])\ndef get_revenue', content)
        content = re.sub(r'@require_admin_token\ndef get_revenue', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_REVENUE])\ndef get_revenue', content)
        content = re.sub(r'@admin_required\ndef get_player', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_PLAYERS])\ndef get_player', content)
        content = re.sub(r'@require_admin_token\ndef get_player', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_PLAYERS])\ndef get_player', content)
        content = re.sub(r'@admin_required\ndef get_card', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_SYSTEM])\ndef get_card', content)
        content = re.sub(r'@require_admin_token\ndef get_card', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_SYSTEM])\ndef get_card', content)
        content = re.sub(r'@admin_required\ndef get_system', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_SYSTEM])\ndef get_system', content)
        content = re.sub(r'@require_admin_token\ndef get_system', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_SYSTEM])\ndef get_system', content)
        # Default analytics view
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_VIEW])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef', '@auto_rbac_required(override_permissions=[Permission.ANALYTICS_VIEW])\ndef', content)
    
    elif 'admin_communications' in filename:
        # Communications routes
        content = re.sub(r'@admin_required\ndef.*announcements.*POST', '@auto_rbac_required(override_permissions=[Permission.COMM_MANAGE])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef.*announcements.*POST', '@auto_rbac_required(override_permissions=[Permission.COMM_MANAGE])\ndef', content)
        content = re.sub(r'@admin_required\ndef.*email', '@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef.*email', '@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])\ndef', content)
        content = re.sub(r'@admin_required\ndef.*broadcast', '@auto_rbac_required(override_permissions=[Permission.COMM_BROADCAST])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef.*broadcast', '@auto_rbac_required(override_permissions=[Permission.COMM_BROADCAST])\ndef', content)
        # Default communications view
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef', '@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])\ndef', content)
    
    elif 'admin_alerts' in filename:
        # Alerts routes
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])\ndef', content)
        content = re.sub(r'@require_admin_token\ndef', '@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])\ndef', content)
    
    elif 'admin_arenas' in filename:
        # Arena management
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.GAME_VIEW])\ndef', content)
    
    elif 'shop_admin' in filename:
        # Shop management
        content = re.sub(r'@admin_required\ndef.*stats', '@auto_rbac_required(override_permissions=[Permission.SHOP_VIEW])\ndef', content)
        content = re.sub(r'@admin_required\ndef.*products', '@auto_rbac_required(override_permissions=[Permission.SHOP_PRODUCTS])\ndef', content)
        content = re.sub(r'@admin_required\ndef.*orders', '@auto_rbac_required(override_permissions=[Permission.SHOP_ORDERS])\ndef', content)
        content = re.sub(r'@admin_required\ndef.*inventory', '@auto_rbac_required(override_permissions=[Permission.SHOP_INVENTORY])\ndef', content)
        # Default shop view
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required(override_permissions=[Permission.SHOP_VIEW])\ndef', content)
    
    else:
        # Default: require basic admin view permission
        content = re.sub(r'@admin_required\ndef', '@auto_rbac_required()\ndef', content)
        content = re.sub(r'@require_admin_token\ndef', '@auto_rbac_required()\ndef', content)
    
    # Write updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"  Updated successfully")

def main():
    """Update all admin route files"""
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    # Find all admin route files
    admin_files = list(routes_dir.glob('admin_*.py'))
    
    print(f"Found {len(admin_files)} admin route files to update:")
    
    for file_path in admin_files:
        # Skip files we've already manually updated
        if file_path.name in ['admin_devices.py', 'admin_player_management.py', 
                              'admin_game_operations.py', 'admin_security_monitoring.py']:
            print(f"Skipping {file_path.name} (already manually updated)")
            continue
        
        try:
            update_admin_route_file(str(file_path))
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
    
    print("\nRBAC update completed!")
    print("\nNext steps:")
    print("1. Test the updated routes")
    print("2. Verify permissions are working correctly")
    print("3. Update frontend to handle permission-based UI")

if __name__ == "__main__":
    main()
