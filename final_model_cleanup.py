#!/usr/bin/env python3
"""
Final comprehensive cleanup of all model syntax issues
"""

import re
from pathlib import Path

def completely_fix_file(file_path: str) -> bool:
    """Completely fix all syntax issues in a model file"""
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix bracket mismatches in relationships
        content = re.sub(r'relationship\(foreign_keys=\[([^\]]+)\]\)\)', r'relationship(foreign_keys=[\1])', content)
        content = re.sub(r'relationship\(foreign_keys=\[([^\]]+)\)\)', r'relationship(foreign_keys=[\1])', content)
        
        # Fix malformed Mapped type annotations
        content = re.sub(r'Mapped\[([^\]]+)\]\)', r'Mapped[\1]', content)
        
        # Fix specific patterns
        patterns_to_fix = [
            # Fix closing bracket/parenthesis mismatches
            (r'\]\)', ']'),
            (r'\)\]', ')'),
            
            # Fix malformed relationship calls
            (r'relationship\(foreign_keys=\[([^\]]+)\]\)', r'relationship(foreign_keys=[\1])'),
            
            # Fix DateTime column definitions
            (r'mapped_column\(DateTime\(timezone=True\)\)', r'mapped_column(DateTime(timezone=True))'),
        ]
        
        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content)
        
        # Clean up the file line by line
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip completely malformed lines
            if line.strip() and (
                line.count('(') != line.count(')') or 
                line.count('[') != line.count(']') or
                line.count('"') % 2 != 0
            ):
                # Try to fix simple bracket issues
                if ')' in line and '[' in line and ']' not in line:
                    line = line.replace(')', ']')
                elif ']' in line and '(' in line and ')' not in line:
                    line = line.replace(']', ')')
            
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Final cleanup
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Completely fixed: {file_path}")
            return True
        else:
            print(f"⏭️  Already clean: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all remaining model files"""
    
    model_files = [
        "shared/models/player_moderation.py",
        "shared/models/tournaments.py",
        "shared/models/card_templates.py",
        "shared/models/nfc_trading_system.py", 
        "shared/models/shop.py"
    ]
    
    print("🔧 Final comprehensive model cleanup...")
    
    for file_path in model_files:
        completely_fix_file(file_path)
    
    print("✅ Cleanup complete!")

if __name__ == "__main__":
    main()

