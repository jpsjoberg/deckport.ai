#!/usr/bin/env python3
"""
Professional SQLAlchemy 2.0+ Model Converter
Converts all models to use proper SQLAlchemy 2.0 syntax with Mapped[] and mapped_column()
"""

import os
import re
import sys
from pathlib import Path

class SQLAlchemy2Converter:
    """Convert SQLAlchemy models to 2.0+ syntax"""
    
    def __init__(self):
        self.converted_files = []
        self.errors = []
    
    def convert_file(self, file_path: str) -> bool:
        """Convert a single file to SQLAlchemy 2.0 syntax"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Step 1: Fix imports
            content = self.fix_imports(content)
            
            # Step 2: Convert Column() to mapped_column() with proper typing
            content = self.convert_columns(content)
            
            # Step 3: Fix relationships
            content = self.fix_relationships(content)
            
            # Step 4: Clean up any remaining issues
            content = self.cleanup_syntax(content)
            
            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                
                self.converted_files.append(file_path)
                print(f"✅ Converted: {file_path}")
            else:
                print(f"⏭️  No changes needed: {file_path}")
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Error converting {file_path}: {e}"
            self.errors.append(error_msg)
            print(error_msg)
            return False
    
    def fix_imports(self, content: str) -> str:
        """Fix SQLAlchemy imports to use 2.0 syntax"""
        
        # Remove old-style imports
        content = re.sub(r'from sqlalchemy\.ext\.declarative import declarative_base\n', '', content)
        content = re.sub(r'from sqlalchemy import Column\n', '', content)
        
        # Ensure proper 2.0 imports exist
        if 'from sqlalchemy.orm import' in content:
            # Update existing import to include all needed components
            content = re.sub(
                r'from sqlalchemy\.orm import ([^\n]+)',
                lambda m: self.build_orm_import(m.group(1)),
                content
            )
        else:
            # Add new import if none exists
            if 'from sqlalchemy import' in content:
                content = re.sub(
                    r'(from sqlalchemy import[^\n]+\n)',
                    r'\1from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship\n',
                    content,
                    count=1
                )
        
        # Fix Base class definition
        content = re.sub(r'Base = declarative_base\(\)', 'class Base(DeclarativeBase):\n    pass', content)
        
        return content
    
    def build_orm_import(self, existing_imports: str) -> str:
        """Build comprehensive ORM import statement"""
        imports = set()
        
        # Parse existing imports
        for imp in existing_imports.split(','):
            imp = imp.strip()
            if imp:
                imports.add(imp)
        
        # Add required 2.0 imports
        required = {'DeclarativeBase', 'Mapped', 'mapped_column', 'relationship'}
        imports.update(required)
        
        # Sort and format
        sorted_imports = sorted(imports)
        return f"from sqlalchemy.orm import {', '.join(sorted_imports)}"
    
    def convert_columns(self, content: str) -> str:
        """Convert Column() definitions to mapped_column() with proper typing"""
        
        # Pattern to match Column definitions
        column_pattern = r'(\w+)\s*=\s*Column\(([^)]+)\)'
        
        def convert_column_match(match):
            field_name = match.group(1)
            column_args = match.group(2)
            
            # Determine the type annotation based on the column definition
            type_annotation = self.determine_type_annotation(column_args)
            
            return f"{field_name}: Mapped[{type_annotation}] = mapped_column({column_args})"
        
        content = re.sub(column_pattern, convert_column_match, content)
        
        return content
    
    def determine_type_annotation(self, column_args: str) -> str:
        """Determine the appropriate Mapped[] type annotation for a column"""
        
        # Check for primary key
        is_primary_key = 'primary_key=True' in column_args
        
        # Check for nullable
        is_nullable = 'nullable=False' not in column_args and 'primary_key=True' not in column_args
        
        # Determine base type
        if 'Integer' in column_args:
            base_type = 'int'
        elif 'String(' in column_args:
            base_type = 'str'
        elif 'Text' in column_args:
            base_type = 'str'
        elif 'Boolean' in column_args:
            base_type = 'bool'
        elif 'DateTime' in column_args:
            base_type = 'datetime'
        elif 'JSON' in column_args or 'JSONB' in column_args:
            base_type = 'Dict[str, Any]'
        elif 'Numeric' in column_args:
            base_type = 'Decimal'
        elif 'Float' in column_args:
            base_type = 'float'
        elif 'ForeignKey' in column_args:
            base_type = 'int'
        elif 'SQLEnum' in column_args or 'SAEnum' in column_args:
            # Extract enum type from the column args
            enum_match = re.search(r'(?:SQLEnum|SAEnum)\((\w+)\)', column_args)
            if enum_match:
                base_type = enum_match.group(1)
            else:
                base_type = 'str'
        else:
            base_type = 'Any'
        
        # Wrap in Optional if nullable
        if is_nullable and not is_primary_key:
            return f'Optional[{base_type}]'
        else:
            return base_type
    
    def fix_relationships(self, content: str) -> str:
        """Fix relationship definitions to use proper typing"""
        
        # Pattern for relationships without proper typing
        rel_patterns = [
            # relationship() without typing
            (r'(\w+)\s*=\s*relationship\(([^)]*)\)', r'\1: Mapped["\2"] = relationship(\2)'),
            
            # Fix common relationship patterns
            (r'(\w+): Mapped\[([^\]]+)\] = relationship\(\)', r'\1: Mapped[\2] = relationship("\2")'),
            
            # Fix foreign key relationships
            (r'relationship\(foreign_keys=\[([^\]]+)\]\)', r'relationship(foreign_keys=[\1])'),
        ]
        
        for pattern, replacement in rel_patterns:
            content = re.sub(pattern, replacement, content)
        
        # Fix specific relationship issues
        content = re.sub(
            r'relationship\("([^"]+)", foreign_keys=\[([^\]]+)\]\)',
            r'relationship("\1", foreign_keys=[\2])',
            content
        )
        
        return content
    
    def cleanup_syntax(self, content: str) -> str:
        """Clean up any remaining syntax issues"""
        
        # Fix spacing issues
        content = re.sub(r'status=\s*Column', 'status = Column', content)
        
        # Fix malformed Text columns
        content = re.sub(r'Column\(Text[a-z_]*\)', 'Column(Text)', content)
        
        # Fix enum imports if needed
        if 'SAEnum' in content and 'from sqlalchemy import' in content:
            content = re.sub(
                r'(from sqlalchemy import[^\n]+)',
                lambda m: m.group(1) + ', Enum as SAEnum' if 'Enum as SAEnum' not in m.group(1) else m.group(1),
                content
            )
        
        return content
    
    def convert_all_models(self, models_dir: str = "shared/models") -> dict:
        """Convert all model files in the directory"""
        
        models_path = Path(models_dir)
        if not models_path.exists():
            print(f"❌ Models directory not found: {models_dir}")
            return {'success': False, 'error': 'Directory not found'}
        
        # Get all Python files except __init__.py and test files
        model_files = [
            f for f in models_path.glob("*.py") 
            if f.name != "__init__.py" and not f.name.startswith("test_")
        ]
        
        print(f"🔄 Converting {len(model_files)} model files to SQLAlchemy 2.0+...")
        print("=" * 60)
        
        for model_file in model_files:
            self.convert_file(str(model_file))
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Conversion Summary:")
        print(f"✅ Successfully converted: {len(self.converted_files)} files")
        print(f"❌ Errors: {len(self.errors)} files")
        
        if self.converted_files:
            print(f"\n📝 Converted files:")
            for file in self.converted_files:
                print(f"  - {file}")
        
        if self.errors:
            print(f"\n⚠️  Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        return {
            'success': len(self.errors) == 0,
            'converted_files': self.converted_files,
            'errors': self.errors,
            'total_files': len(model_files)
        }

def main():
    """Main conversion function"""
    converter = SQLAlchemy2Converter()
    
    print("🔧 Professional SQLAlchemy 2.0+ Model Converter")
    print("=" * 50)
    
    result = converter.convert_all_models()
    
    if result['success']:
        print(f"\n🎉 All {result['total_files']} model files successfully converted to SQLAlchemy 2.0+!")
        return 0
    else:
        print(f"\n⚠️  Conversion completed with {len(result['errors'])} errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
