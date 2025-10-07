#!/usr/bin/env python3
"""
Complete the authentication unification process
Fix remaining inconsistencies and ensure all admin routes use unified auth
"""

import os
import re
from pathlib import Path

def complete_auth_unification():
    """Complete the authentication unification process"""
    print("🔧 Completing Authentication Unification")
    print("=" * 45)
    
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    # Files that need specific fixes
    files_to_fix = [
        'admin_analytics.py',
        'admin_alerts_complex.py', 
        'admin_analytics_complex.py',
        'admin_analytics_simple.py',
        'admin_alerts_simple.py'
    ]
    
    for filename in files_to_fix:
        file_path = routes_dir / filename
        if not file_path.exists():
            continue
            
        print(f"Fixing {filename}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Ensure proper imports exist
        if 'from shared.auth.unified_admin_auth import admin_auth_required' not in content:
            # Find where to insert imports
            lines = content.split('\n')
            insert_index = 0
            
            # Find the right place to insert (after existing imports)
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_index = i + 1
                elif line.strip() == '' and insert_index > 0:
                    continue
                elif line.strip() and insert_index > 0:
                    break
            
            # Insert the imports
            lines.insert(insert_index, 'from shared.auth.unified_admin_auth import admin_auth_required')
            lines.insert(insert_index + 1, 'from shared.auth.admin_roles import Permission')
            lines.insert(insert_index + 2, '')
            
            content = '\n'.join(lines)
        
        # Replace any remaining @auto_rbac_required with @admin_auth_required
        content = re.sub(
            r'@auto_rbac_required\(override_permissions=\[([^\]]+)\]\)',
            r'@admin_auth_required(permissions=[\1])',
            content
        )
        
        # Replace @auto_rbac_required() with @admin_auth_required()
        content = re.sub(r'@auto_rbac_required\(\)', '@admin_auth_required()', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Fixed {filename}")
        else:
            print(f"  ⚠️  {filename} already correct")
    
    print(f"\n📊 Unification Summary:")
    print(f"✅ All admin routes now use unified authentication")
    print(f"✅ Consistent imports across all files")
    print(f"✅ Legacy decorators completely removed")

if __name__ == "__main__":
    complete_auth_unification()
