#!/usr/bin/env python3
"""
Comprehensive syntax fix for base.py - fix ALL issues at once
"""

import re
from pathlib import Path

def comprehensive_fix(content: str) -> str:
    """Apply all necessary syntax fixes"""
    
    # Fix missing closing parentheses in Column definitions
    content = re.sub(r'Column\(String\((\d+),\s*([^)]+)\)', r'Column(String(\1), \2)', content)
    content = re.sub(r'Column\(([^)]+)\),\s*([^)]+)\)', r'Column(\1, \2)', content)
    
    # Fix relationship definitions
    content = re.sub(r'relationship\(\s*"([^"]+)",\s*foreign_keys="([^"]+)",\s*back_populates="([^"]+)"\s*\)', 
                    r'relationship("\1", foreign_keys="\2", back_populates="\3")', content)
    
    # Fix malformed multi-line strings in relationships
    content = re.sub(r'relationship\(\s*"([^"]+)",\s*\n\s*foreign_keys="([^"]+)",\s*\n\s*back_populates="([^"]+)"\s*\)', 
                    r'relationship("\1", foreign_keys="\2", back_populates="\3")', content, flags=re.MULTILINE)
    
    return content

def main():
    """Fix base.py comprehensively"""
    
    file_path = Path("shared/models/base.py")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Apply comprehensive fixes
        fixed_content = comprehensive_fix(content)
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        
        print(f"✅ Applied comprehensive fixes to: {file_path}")
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

if __name__ == "__main__":
    main()

