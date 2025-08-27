#!/usr/bin/env python3
"""
Fix remaining AuditLog instances in admin_devices.py
Convert them to use the new log_admin_action helper
"""

import re
from pathlib import Path

def fix_remaining_audit_logs():
    """Fix remaining AuditLog instances"""
    print("🔧 Fixing Remaining AuditLog Instances")
    print("=" * 38)
    
    file_path = Path('/home/jp/deckport.ai/services/api/routes/admin_devices.py')
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match AuditLog creation with get_current_admin_id() or 1
    audit_log_pattern = r'audit_log = AuditLog\(\s*actor_type="admin",\s*actor_id=get_current_admin_id\(\) or 1,\s*action="([^"]+)",\s*details=([^)]+)\s*\)\s*session\.add\(audit_log\)'
    
    def replace_audit_log(match):
        action = match.group(1)
        details = match.group(2)
        return f'log_admin_action(session, "{action}", f"Console {{device_uid}} {action.replace("console_", "").replace("_", " ")} by admin", {details})'
    
    # Apply the replacement
    content = re.sub(audit_log_pattern, replace_audit_log, content, flags=re.MULTILINE | re.DOTALL)
    
    # Also handle cases where session.add(audit_log) is on a separate line
    content = re.sub(r'audit_log = AuditLog\(\s*actor_type="admin",\s*actor_id=get_current_admin_id\(\) or 1,\s*action="([^"]+)",\s*details=([^)]+)\s*\)', 
                    lambda m: f'log_admin_action(session, "{m.group(1)}", f"Console {{device_uid}} {m.group(1).replace("console_", "").replace("_", " ")} by admin", {m.group(2)})', 
                    content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove any remaining session.add(audit_log) lines
    content = re.sub(r'\s*session\.add\(audit_log\)\s*\n', '', content)
    
    # Clean up formatting
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Fixed remaining AuditLog instances in admin_devices.py")
    else:
        print(f"  ⚠️  No changes needed")
    
    print(f"\n📊 All AuditLog instances now use log_admin_action helper")

if __name__ == "__main__":
    fix_remaining_audit_logs()
