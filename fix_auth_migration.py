#!/usr/bin/env python3
"""
Fix authentication migration - properly remove old decorators and update usage
"""

import os
import re
from pathlib import Path

def fix_auth_file(file_path: str):
    """Fix authentication in a single file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Step 1: Clean up imports - remove duplicates and fix order
    lines = content.split('\n')
    cleaned_lines = []
    imports_added = False
    
    for i, line in enumerate(lines):
        # Skip the old function definition entirely
        if line.strip().startswith('def require_admin_token(f):'):
            # Skip this function and everything until the next function or class
            j = i + 1
            while j < len(lines):
                if (lines[j].strip().startswith('def ') and not lines[j].strip().startswith('def decorated_function')) or \
                   lines[j].strip().startswith('class ') or \
                   lines[j].strip().startswith('@'):
                    break
                j += 1
            # Skip to the line before the next function/class
            i = j - 1
            continue
        
        # Add proper imports at the beginning
        if not imports_added and line.strip() and not line.startswith('#') and not line.startswith('"""'):
            if 'from shared.auth.unified_admin_auth import admin_auth_required' not in content:
                cleaned_lines.append('from shared.auth.unified_admin_auth import admin_auth_required')
            if 'from shared.auth.admin_roles import Permission' not in content:
                cleaned_lines.append('from shared.auth.admin_roles import Permission')
            cleaned_lines.append('')
            imports_added = True
        
        # Skip duplicate imports
        if 'from shared.auth.unified_admin_auth import' in line or \
           ('from shared.auth.admin_roles import Permission' in line and imports_added):
            continue
            
        # Skip old imports
        if 'from shared.auth.jwt_handler import verify_admin_token' in line or \
           'from functools import wraps' in line:
            continue
        
        cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    # Step 2: Replace decorator usage
    filename = os.path.basename(file_path)
    
    if 'player' in filename:
        content = re.sub(r'@require_admin_token', '@admin_auth_required(permissions=[Permission.PLAYER_VIEW])', content)
    elif 'communication' in filename:
        content = re.sub(r'@require_admin_token', '@admin_auth_required(permissions=[Permission.COMM_VIEW])', content)
    elif 'analytics' in filename:
        content = re.sub(r'@require_admin_token', '@admin_auth_required(permissions=[Permission.ANALYTICS_VIEW])', content)
    elif 'alert' in filename:
        content = re.sub(r'@require_admin_token', '@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])', content)
    else:
        content = re.sub(r'@require_admin_token', '@admin_auth_required()', content)
    
    # Step 3: Clean up any remaining issues
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Remove excessive blank lines
    content = re.sub(r'@wraps\(f\)', '', content)  # Remove any leftover @wraps
    
    # Only write if content changed significantly
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Fixed successfully")
        return True
    else:
        print(f"  ⚠️  No changes needed")
        return False

def main():
    """Main fix function"""
    print("🔧 Fixing Authentication Migration")
    print("=" * 40)
    
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    # Get files that still have require_admin_token function
    files_to_fix = []
    for file_path in routes_dir.glob('admin_*.py'):
        with open(file_path, 'r') as f:
            content = f.read()
            if 'def require_admin_token(' in content:
                files_to_fix.append(file_path)
    
    print(f"Found {len(files_to_fix)} files to fix:")
    for file_path in files_to_fix:
        print(f"  - {file_path.name}")
    
    if not files_to_fix:
        print("✅ No files need fixing!")
        return
    
    print(f"\n🚀 Starting fixes...\n")
    
    fixed_count = 0
    for file_path in files_to_fix:
        try:
            if fix_auth_file(str(file_path)):
                fixed_count += 1
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
    
    print(f"\n📊 Fix Summary:")
    print(f"✅ Fixed {fixed_count}/{len(files_to_fix)} files")
    print(f"🔄 Authentication decorators unified")

if __name__ == "__main__":
    main()
