#!/usr/bin/env python3
"""
Convert SQLAlchemy 2.0 syntax to 1.4 syntax
"""

import re
import sys

def convert_sqlalchemy_syntax(file_path):
    """Convert SQLAlchemy 2.0 syntax to 1.4 syntax"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Convert imports
    content = re.sub(
        r'from sqlalchemy\.orm import DeclarativeBase, Mapped, mapped_column, relationship',
        'from sqlalchemy.ext.declarative import declarative_base\nfrom sqlalchemy.orm import relationship\nfrom sqlalchemy import Column',
        content
    )
    
    # Convert base class
    content = re.sub(
        r'class Base\(DeclarativeBase\):\s*pass',
        'Base = declarative_base()',
        content
    )
    
    # Convert field definitions - this is the tricky part
    # Pattern: field_name: Mapped[type] = mapped_column(...)
    
    # First, handle simple cases
    patterns = [
        # Basic types
        (r'(\w+): Mapped\[int\] = mapped_column\(Integer, primary_key=True\)', r'\1 = Column(Integer, primary_key=True)'),
        (r'(\w+): Mapped\[str\] = mapped_column\(String\((\d+)\), ([^)]+)\)', r'\1 = Column(String(\2), \3)'),
        (r'(\w+): Mapped\[Optional\[str\]\] = mapped_column\(String\((\d+)\)([^)]*)\)', r'\1 = Column(String(\2)\3)'),
        (r'(\w+): Mapped\[bool\] = mapped_column\(Boolean, ([^)]+)\)', r'\1 = Column(Boolean, \2)'),
        (r'(\w+): Mapped\[int\] = mapped_column\(Integer, ([^)]+)\)', r'\1 = Column(Integer, \2)'),
        (r'(\w+): Mapped\[datetime\] = mapped_column\(DateTime\(timezone=True\), ([^)]+)\)', r'\1 = Column(DateTime(timezone=True), \2)'),
        (r'(\w+): Mapped\[Optional\[datetime\]\] = mapped_column\(DateTime\(timezone=True\)([^)]*)\)', r'\1 = Column(DateTime(timezone=True)\2)'),
        
        # Enum types
        (r'(\w+): Mapped\[(\w+)\] = mapped_column\(SQLEnum\(\2\), ([^)]+)\)', r'\1 = Column(SQLEnum(\2), \3)'),
        
        # Foreign keys
        (r'(\w+): Mapped\[int\] = mapped_column\(ForeignKey\(([^)]+)\), ([^)]+)\)', r'\1 = Column(ForeignKey(\2), \3)'),
        (r'(\w+): Mapped\[Optional\[int\]\] = mapped_column\(ForeignKey\(([^)]+)\)([^)]*)\)', r'\1 = Column(ForeignKey(\2)\3)'),
        
        # JSON and Text
        (r'(\w+): Mapped\[Optional\[Dict\[str, Any\]\]\] = mapped_column\(JSON\)([^)]*)', r'\1 = Column(JSON)\2'),
        (r'(\w+): Mapped\[Optional\[str\]\] = mapped_column\(Text([^)]*)\)', r'\1 = Column(Text\1)'),
        (r'(\w+): Mapped\[str\] = mapped_column\(Text, ([^)]+)\)', r'\1 = Column(Text, \2)'),
        
        # List types (for JSON)
        (r'(\w+): Mapped\[Optional\[List\[str\]\]\] = mapped_column\(JSON\)([^)]*)', r'\1 = Column(JSON)\2'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Handle relationships - remove Mapped[] type hints
    content = re.sub(
        r'(\w+): Mapped\["?(\w+)"?\] = relationship\(([^)]+)\)',
        r'\1 = relationship(\3)',
        content
    )
    content = re.sub(
        r'(\w+): Mapped\[Optional\["?(\w+)"?\]\] = relationship\(([^)]+)\)',
        r'\1 = relationship(\3)',
        content
    )
    content = re.sub(
        r'(\w+): Mapped\[List\["?(\w+)"?\]\] = relationship\(([^)]+)\)',
        r'\1 = relationship(\3)',
        content
    )
    
    return content

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_sqlalchemy_syntax.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        converted_content = convert_sqlalchemy_syntax(file_path)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(converted_content)
        
        print(f"✅ Converted {file_path} from SQLAlchemy 2.0 to 1.4 syntax")
        
    except Exception as e:
        print(f"❌ Error converting {file_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
