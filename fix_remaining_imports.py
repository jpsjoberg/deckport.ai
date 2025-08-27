#!/usr/bin/env python3
"""
Fix remaining import issues in admin files
"""

from pathlib import Path

def fix_imports(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already has the imports
    if ('from shared.auth.unified_admin_auth import' in content or 
        'from shared.auth.auto_rbac_decorator import' in content) and \
       'from shared.auth.admin_roles import Permission' in content:
        return False  # Already fixed
    
    lines = content.split('\n')
    
    # Find insertion point (after existing imports)
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_index = i + 1
        elif line.strip() == '' and insert_index > 0:
            continue
        elif line.strip() and insert_index > 0:
            break
    
    # Insert missing imports
    if 'from shared.auth.unified_admin_auth import' not in content and \
       'from shared.auth.auto_rbac_decorator import' not in content:
        lines.insert(insert_index, 'from shared.auth.unified_admin_auth import admin_auth_required')
        insert_index += 1
    
    if 'from shared.auth.admin_roles import Permission' not in content:
        lines.insert(insert_index, 'from shared.auth.admin_roles import Permission')
        insert_index += 1
    
    # Add blank line if needed
    if insert_index < len(lines) and lines[insert_index].strip():
        lines.insert(insert_index, '')
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    return True

def main():
    """Fix remaining import issues"""
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    files_to_fix = [
        'admin_communications_complex.py',
        'admin_players.py', 
        'admin_players_simple.py',
        'admin_communications.py',
        'admin_communications_simple.py',
        'admin_players_complex.py'
    ]
    
    print("🔧 Fixing Remaining Import Issues")
    print("=" * 35)
    
    fixed_count = 0
    for filename in files_to_fix:
        file_path = routes_dir / filename
        if file_path.exists():
            if fix_imports(file_path):
                print(f"✅ Fixed {filename}")
                fixed_count += 1
            else:
                print(f"⚠️  {filename} already correct")
    
    print(f"\n📊 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
