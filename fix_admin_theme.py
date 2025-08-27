#!/usr/bin/env python3
"""
Script to fix admin panel theme consistency - convert all white backgrounds to dark theme
"""
import os
import re
import glob

def fix_admin_theme():
    """Fix admin theme consistency across all templates"""
    
    # Define the replacements for consistent dark theme
    replacements = [
        # Main containers
        (r'bg-white', 'bg-gray-800'),
        (r'shadow(?!\-)', 'border border-gray-700'),
        
        # Text colors
        (r'text-gray-900', 'text-white'),
        (r'text-gray-800', 'text-gray-200'),
        (r'text-gray-700', 'text-gray-300'),
        (r'text-gray-600', 'text-gray-400'),
        (r'text-gray-500', 'text-gray-400'),
        
        # Background colors for icons and badges
        (r'bg-blue-100', 'bg-blue-900'),
        (r'bg-green-100', 'bg-green-900'),
        (r'bg-purple-100', 'bg-purple-900'),
        (r'bg-orange-100', 'bg-orange-900'),
        (r'bg-red-100', 'bg-red-900'),
        (r'bg-yellow-100', 'bg-yellow-900'),
        (r'bg-gray-100', 'bg-gray-700'),
        (r'bg-gray-50', 'bg-gray-800'),
        (r'bg-gray-200', 'bg-gray-700'),
        (r'bg-gray-300', 'bg-gray-600'),
        
        # Icon colors
        (r'text-blue-600', 'text-blue-400'),
        (r'text-green-600', 'text-green-400'),
        (r'text-purple-600', 'text-purple-400'),
        (r'text-orange-600', 'text-orange-400'),
        (r'text-red-600', 'text-red-400'),
        (r'text-yellow-600', 'text-yellow-400'),
        
        # Border colors
        (r'border-gray-200', 'border-gray-700'),
        (r'border-gray-300', 'border-gray-600'),
        (r'divide-gray-200', 'divide-gray-700'),
        
        # Hover states
        (r'hover:bg-gray-50', 'hover:bg-gray-700'),
        (r'hover:bg-white', 'hover:bg-gray-700'),
    ]
    
    # Find all admin template files
    admin_templates_path = '/home/jp/deckport.ai/frontend/templates/admin'
    template_files = []
    
    for root, dirs, files in os.walk(admin_templates_path):
        for file in files:
            if file.endswith('.html'):
                template_files.append(os.path.join(root, file))
    
    print(f"Found {len(template_files)} admin template files")
    
    files_modified = 0
    total_replacements = 0
    
    for template_file in template_files:
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # Apply all replacements
            for pattern, replacement in replacements:
                matches = len(re.findall(pattern, content))
                if matches > 0:
                    content = re.sub(pattern, replacement, content)
                    file_replacements += matches
            
            # Only write if changes were made
            if content != original_content:
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_modified += 1
                total_replacements += file_replacements
                print(f"✅ Fixed {template_file} ({file_replacements} replacements)")
            
        except Exception as e:
            print(f"❌ Error processing {template_file}: {e}")
    
    print(f"\n🎉 Theme fix complete!")
    print(f"📁 Files modified: {files_modified}")
    print(f"🔄 Total replacements: {total_replacements}")

if __name__ == "__main__":
    print("🎨 Fixing Admin Panel Theme Consistency...")
    print("Converting white backgrounds to dark theme...")
    print()
    
    fix_admin_theme()
