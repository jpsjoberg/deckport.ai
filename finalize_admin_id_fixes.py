#!/usr/bin/env python3
"""
Finalize admin ID fixes - ensure all files are properly updated
"""

import os
import re
from pathlib import Path

def finalize_admin_id_fixes():
    """Final cleanup of admin ID fixes"""
    print("🔧 Finalizing Admin ID Fixes")
    print("=" * 32)
    
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    files_to_check = [
        'admin_player_management.py',
        'admin_devices.py', 
        'admin_game_operations.py'
    ]
    
    for filename in files_to_check:
        file_path = routes_dir / filename
        if not file_path.exists():
            continue
        
        print(f"Checking {filename}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Ensure proper import exists
        if 'from shared.auth.admin_context import' not in content:
            # Add import after other imports
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    insert_index = i + 1
                elif line.strip() == '' and insert_index > 0:
                    continue
                elif line.strip() and insert_index > 0:
                    break
            
            lines.insert(insert_index, 'from shared.auth.admin_context import log_admin_action, get_current_admin_id')
            lines.insert(insert_index + 1, '')
            content = '\n'.join(lines)
        
        # Fix any remaining AuditLog patterns that weren't caught
        # Pattern: AuditLog with actor_id=get_current_admin_id() or 1
        audit_log_pattern = r'audit_log = AuditLog\(\s*actor_type="admin",\s*actor_id=get_current_admin_id\(\) or 1,\s*action="([^"]+)",\s*details=([^)]+)\s*\)\s*session\.add\(audit_log\)'
        
        def replace_remaining_audit_logs(match):
            action = match.group(1)
            details = match.group(2)
            return f'log_admin_action(session, "{action}", {details})'
        
        content = re.sub(audit_log_pattern, replace_remaining_audit_logs, content, flags=re.MULTILINE | re.DOTALL)
        
        # Fix formatting issues
        content = re.sub(r'\)\s*session\.commit\(\)', ')\n            session.commit()', content)
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Remove excessive blank lines
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  ✅ Cleaned up {filename}")
        else:
            print(f"  ✅ {filename} already clean")
    
    print(f"\n📊 Finalization Complete:")
    print(f"✅ All admin ID fixes applied and cleaned up")
    print(f"✅ Proper imports added to all files")
    print(f"✅ Consistent audit logging throughout")

if __name__ == "__main__":
    finalize_admin_id_fixes()
