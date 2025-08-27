#!/usr/bin/env python3
"""
Migration script to unify admin authentication decorators
Converts require_admin_token to the new unified authentication system
"""

import os
import re
import sys
from pathlib import Path

def migrate_auth_decorators(file_path: str):
    """Migrate authentication decorators in a single file"""
    print(f"Migrating {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if already migrated
    if 'unified_admin_auth' in content:
        print(f"  Already migrated, skipping")
        return
    
    original_content = content
    
    # Step 1: Update imports
    # Remove old imports
    content = re.sub(r'from shared\.auth\.jwt_handler import verify_admin_token\n', '', content)
    content = re.sub(r'from functools import wraps\n', '', content)
    
    # Add new unified import
    if 'from shared.auth.auto_rbac_decorator import' in content:
        # File already has RBAC imports, just add unified auth
        content = re.sub(
            r'from shared\.auth\.auto_rbac_decorator import ([^\n]+)',
            r'from shared.auth.auto_rbac_decorator import \1\nfrom shared.auth.unified_admin_auth import admin_auth_required',
            content
        )
    else:
        # Add new import after existing imports
        import_section = []
        other_lines = []
        in_imports = True
        
        for line in content.split('\n'):
            if in_imports and (line.startswith('import ') or line.startswith('from ') or line.strip() == ''):
                import_section.append(line)
            else:
                if in_imports and line.strip():
                    # Add our import before the first non-import line
                    import_section.append('from shared.auth.unified_admin_auth import admin_auth_required')
                    import_section.append('from shared.auth.admin_roles import Permission')
                    import_section.append('')
                    in_imports = False
                other_lines.append(line)
        
        content = '\n'.join(import_section + other_lines)
    
    # Step 2: Remove the custom require_admin_token function definition
    # Match the entire function definition
    token_func_pattern = r'def require_admin_token\(f\):\s*"""[^"]*"""\s*@wraps\(f\)\s*def decorated_function\([^)]*\):[^}]*?return decorated_function\s*'
    content = re.sub(token_func_pattern, '', content, flags=re.DOTALL)
    
    # Alternative pattern for simpler function definitions
    token_func_pattern2 = r'def require_admin_token\(f\):[^}]*?return decorated_function\s*'
    content = re.sub(token_func_pattern2, '', content, flags=re.DOTALL)
    
    # Step 3: Replace decorator usage based on endpoint analysis
    filename = os.path.basename(file_path)
    
    # Analyze file type and suggest appropriate decorators
    if 'player' in filename:
        # Player management files
        content = re.sub(r'@require_admin_token\ndef ([^(]*ban[^(]*)\(', r'@admin_auth_required(permissions=[Permission.PLAYER_BAN])\ndef \1(', content)
        content = re.sub(r'@require_admin_token\ndef ([^(]*warn[^(]*)\(', r'@admin_auth_required(permissions=[Permission.PLAYER_WARN])\ndef \1(', content)
        content = re.sub(r'@require_admin_token\ndef ([^(]*get[^(]*|[^(]*stats[^(]*|[^(]*view[^(]*)\(', r'@admin_auth_required(permissions=[Permission.PLAYER_VIEW])\ndef \1(', content)
        # Default for other player operations
        content = re.sub(r'@require_admin_token\ndef', r'@admin_auth_required(permissions=[Permission.PLAYER_VIEW])\ndef', content)
    
    elif 'communication' in filename:
        # Communications files
        content = re.sub(r'@require_admin_token\ndef ([^(]*post[^(]*|[^(]*create[^(]*|[^(]*send[^(]*)\(', r'@admin_auth_required(permissions=[Permission.COMM_MANAGE])\ndef \1(', content)
        content = re.sub(r'@require_admin_token\ndef ([^(]*email[^(]*)\(', r'@admin_auth_required(permissions=[Permission.COMM_EMAIL])\ndef \1(', content)
        content = re.sub(r'@require_admin_token\ndef ([^(]*broadcast[^(]*)\(', r'@admin_auth_required(permissions=[Permission.COMM_BROADCAST])\ndef \1(', content)
        # Default for communications
        content = re.sub(r'@require_admin_token\ndef', r'@admin_auth_required(permissions=[Permission.COMM_VIEW])\ndef', content)
    
    elif 'analytics' in filename:
        # Analytics files
        content = re.sub(r'@require_admin_token\ndef ([^(]*revenue[^(]*)\(', r'@admin_auth_required(permissions=[Permission.ANALYTICS_REVENUE])\ndef \1(', content)
        content = re.sub(r'@require_admin_token\ndef ([^(]*player[^(]*)\(', r'@admin_auth_required(permissions=[Permission.ANALYTICS_PLAYERS])\ndef \1(', content)
        content = re.sub(r'@require_admin_token\ndef ([^(]*system[^(]*)\(', r'@admin_auth_required(permissions=[Permission.ANALYTICS_SYSTEM])\ndef \1(', content)
        # Default for analytics
        content = re.sub(r'@require_admin_token\ndef', r'@admin_auth_required(permissions=[Permission.ANALYTICS_VIEW])\ndef', content)
    
    elif 'alert' in filename:
        # Alerts files
        content = re.sub(r'@require_admin_token\ndef', r'@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])\ndef', content)
    
    else:
        # Default: use automatic permission detection
        content = re.sub(r'@require_admin_token\ndef', r'@admin_auth_required()\ndef', content)
    
    # Step 4: Clean up any remaining references
    # Remove empty lines that might have been left
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Migrated successfully")
    else:
        print(f"  ⚠️  No changes needed")

def main():
    """Main migration function"""
    print("🔄 Admin Authentication Decorator Migration")
    print("=" * 50)
    
    # Find all files that need migration
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    # Get files that still use require_admin_token
    files_to_migrate = []
    
    for file_path in routes_dir.glob('admin_*.py'):
        with open(file_path, 'r') as f:
            content = f.read()
            if 'def require_admin_token(' in content:
                files_to_migrate.append(file_path)
    
    print(f"Found {len(files_to_migrate)} files to migrate:")
    for file_path in files_to_migrate:
        print(f"  - {file_path.name}")
    
    if not files_to_migrate:
        print("✅ No files need migration!")
        return
    
    print(f"\n🚀 Starting migration...\n")
    
    # Migrate each file
    for file_path in files_to_migrate:
        try:
            migrate_auth_decorators(str(file_path))
        except Exception as e:
            print(f"❌ Error migrating {file_path}: {e}")
    
    print(f"\n📊 Migration Summary:")
    print(f"✅ Processed {len(files_to_migrate)} files")
    print(f"🔄 Authentication decorators unified")
    print(f"🔐 RBAC permissions applied based on endpoint analysis")
    
    print(f"\n🎯 Benefits:")
    print(f"✅ Consistent authentication across all admin routes")
    print(f"✅ Automatic permission detection and enforcement")
    print(f"✅ Better security with granular permissions")
    print(f"✅ Easier maintenance and debugging")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Test the migrated endpoints")
    print(f"2. Verify permissions are working correctly")
    print(f"3. Update any remaining manual decorators")
    print(f"4. Remove deprecated decorator functions")

if __name__ == "__main__":
    main()
