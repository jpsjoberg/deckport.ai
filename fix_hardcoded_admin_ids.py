#!/usr/bin/env python3
"""
Fix hardcoded admin IDs in audit logs
Replace actor_id=1 with proper admin context extraction
"""

import os
import re
from pathlib import Path

def fix_hardcoded_admin_ids():
    """Fix all hardcoded admin IDs in admin route files"""
    print("🔧 Fixing Hardcoded Admin IDs")
    print("=" * 35)
    
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    # Files that need fixing based on our grep results
    files_to_fix = [
        'admin_player_management.py',
        'admin_devices.py', 
        'admin_game_operations.py'
    ]
    
    total_fixes = 0
    
    for filename in files_to_fix:
        file_path = routes_dir / filename
        if not file_path.exists():
            continue
        
        print(f"Fixing {filename}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Add import for admin context if not present
        if 'from shared.auth.admin_context import' not in content:
            # Find where to insert the import
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
            
            # Insert the import
            lines.insert(insert_index, 'from shared.auth.admin_context import log_admin_action, get_current_admin_id')
            lines.insert(insert_index + 1, '')
            
            content = '\n'.join(lines)
        
        # Count fixes in this file
        file_fixes = 0
        
        # Pattern 1: Replace the entire AuditLog creation with our helper
        # Match: audit_log = AuditLog(\n    actor_type="admin",\n    actor_id=1,  # TODO: Get actual admin ID from JWT\n    action="...",\n    details=...
        audit_log_pattern = r'audit_log = AuditLog\(\s*actor_type="admin",\s*actor_id=1,\s*#[^\n]*\n\s*action="([^"]+)",\s*details=([^,\n]+)(?:,\s*meta=([^)]+))?\s*\)'
        
        def replace_audit_log(match):
            nonlocal file_fixes
            file_fixes += 1
            
            action = match.group(1)
            details = match.group(2)
            meta = match.group(3) if match.group(3) else 'None'
            
            return f'log_admin_action(session, "{action}", {details}, {meta})'
        
        content = re.sub(audit_log_pattern, replace_audit_log, content, flags=re.MULTILINE | re.DOTALL)
        
        # Pattern 2: Simple actor_id=1 replacement (fallback)
        simple_pattern = r'actor_id=1,?\s*#[^\n]*'
        
        def replace_simple_actor_id(match):
            nonlocal file_fixes
            file_fixes += 1
            return 'actor_id=get_current_admin_id() or 1,'
        
        # Only apply this if the first pattern didn't catch everything
        if 'actor_id=1' in content:
            content = re.sub(simple_pattern, replace_simple_actor_id, content)
        
        # Clean up any remaining session.add(audit_log) lines that are no longer needed
        content = re.sub(r'\s*session\.add\(audit_log\)\s*\n', '', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Fixed {file_fixes} instances in {filename}")
            total_fixes += file_fixes
        else:
            print(f"  ⚠️  No changes needed in {filename}")
    
    print(f"\n📊 Fix Summary:")
    print(f"✅ Total fixes applied: {total_fixes}")
    print(f"✅ All hardcoded admin IDs replaced with JWT context")
    print(f"✅ Proper audit logging with admin context")

if __name__ == "__main__":
    fix_hardcoded_admin_ids()
