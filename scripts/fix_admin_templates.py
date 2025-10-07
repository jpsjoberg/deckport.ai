#!/usr/bin/env python3
"""
Fix All Admin Template Datetime Issues
Systematically fixes all datetime template errors across the admin panel
"""

import os
import re
from pathlib import Path

def fix_datetime_templates():
    """Fix all datetime template issues in admin templates"""
    
    print("🔧 Fixing Admin Template Datetime Issues")
    print("=" * 50)
    
    # Template directory
    templates_dir = Path("/home/jp/deckport.ai/frontend/templates/admin")
    
    # Pattern to find datetime slicing issues
    datetime_pattern = r'\{\{\s*([^}]+)\.created_at\[:10\]\s*([^}]*)\}\}'
    
    # Replacement pattern - safe datetime handling
    def datetime_replacement(match):
        var_name = match.group(1).strip()
        condition = match.group(2).strip()
        
        if condition:
            # Has conditional (like "if card.created_at else 'Today'")
            return f"{{% if {var_name}.created_at %}}{{% if {var_name}.created_at is string %}}{{{{{ var_name}.created_at[:10] }}}}{{% else %}}{{{{{ var_name}.created_at.strftime('%Y-%m-%d') if hasattr({var_name}.created_at, 'strftime') else 'Today' }}}}{{% endif %}}{{% else %}}Today{{% endif %}}"
        else:
            # No conditional - just the datetime slice
            return f"{{% if {var_name}.created_at is string %}}{{{{{ var_name}.created_at[:10] }}}}{{% else %}}{{{{{ var_name}.created_at.strftime('%Y-%m-%d') if hasattr({var_name}.created_at, 'strftime') else 'Today' }}}}{{% endif %}"
    
    fixed_files = []
    
    # Find all HTML files recursively
    for html_file in templates_dir.rglob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has datetime issues
            if '.created_at[:10]' in content:
                print(f"📝 Fixing: {html_file.relative_to(templates_dir)}")
                
                # Fix the datetime issues
                new_content = re.sub(datetime_pattern, datetime_replacement, content)
                
                # Write back the fixed content
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                fixed_files.append(str(html_file.relative_to(templates_dir)))
                print(f"  ✅ Fixed datetime issues in {html_file.name}")
        
        except Exception as e:
            print(f"  ❌ Error fixing {html_file}: {e}")
    
    print(f"\n✅ Fixed {len(fixed_files)} template files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")
    
    return len(fixed_files)

def main():
    """Main function"""
    print("🎮 Deckport Admin Template Fixer")
    print("=" * 50)
    
    fixed_count = fix_datetime_templates()
    
    print("=" * 50)
    if fixed_count > 0:
        print(f"✅ Successfully fixed {fixed_count} template files")
        print("🔄 Restart frontend.service to apply changes:")
        print("   sudo systemctl restart frontend.service")
    else:
        print("ℹ️ No template files needed fixing")
    
    return True

if __name__ == "__main__":
    main()
