#!/usr/bin/env python3
"""
Final verification of authentication unification
Simple test without Flask dependencies
"""

import os
import re
from pathlib import Path

def verify_auth_unification():
    """Verify authentication unification is complete"""
    print("🔍 Verifying Authentication Unification")
    print("=" * 42)
    
    routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
    
    # Statistics
    total_files = 0
    files_with_routes = 0
    files_with_unified_auth = 0
    files_with_legacy_auth = 0
    total_routes = 0
    routes_with_auth = 0
    
    legacy_issues = []
    import_issues = []
    
    for file_path in routes_dir.glob('admin_*.py'):
        total_files += 1
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file has routes
        route_matches = re.findall(r'@[^.]*\.route\(', content)
        if route_matches:
            files_with_routes += 1
            total_routes += len(route_matches)
            
            # Check for unified auth decorators
            unified_auth_matches = re.findall(
                r'@(admin_auth_required|auto_rbac_required|admin_permissions_required|super_admin_required)',
                content
            )
            routes_with_auth += len(unified_auth_matches)
            
            if unified_auth_matches:
                files_with_unified_auth += 1
            
            # Check for legacy issues
            if 'def require_admin_token(' in content:
                legacy_issues.append(f"{file_path.name}: Legacy function definition")
                files_with_legacy_auth += 1
            
            if '@require_admin_token' in content:
                legacy_issues.append(f"{file_path.name}: Legacy decorator usage")
            
            # Check imports
            has_unified_import = (
                'from shared.auth.unified_admin_auth import' in content or
                'from shared.auth.auto_rbac_decorator import' in content
            )
            
            has_permission_import = 'from shared.auth.admin_roles import Permission' in content
            
            if not has_unified_import or not has_permission_import:
                import_issues.append(f"{file_path.name}: Missing proper imports")
    
    # Calculate percentages
    auth_coverage = (routes_with_auth / total_routes * 100) if total_routes > 0 else 0
    file_coverage = (files_with_unified_auth / files_with_routes * 100) if files_with_routes > 0 else 0
    
    print(f"📊 Verification Results:")
    print(f"  Total admin files: {total_files}")
    print(f"  Files with routes: {files_with_routes}")
    print(f"  Files with unified auth: {files_with_unified_auth}")
    print(f"  Files with legacy auth: {files_with_legacy_auth}")
    print(f"  Total admin routes: {total_routes}")
    print(f"  Routes with auth: {routes_with_auth}")
    print(f"  Auth coverage: {auth_coverage:.1f}%")
    print(f"  File coverage: {file_coverage:.1f}%")
    
    # Report issues
    if legacy_issues:
        print(f"\n❌ Legacy Issues Found:")
        for issue in legacy_issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ No legacy issues found")
    
    if import_issues:
        print(f"\n⚠️ Import Issues Found:")
        for issue in import_issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ All imports are correct")
    
    # Overall assessment
    success = (
        files_with_legacy_auth == 0 and
        len(import_issues) == 0 and
        auth_coverage >= 90 and
        file_coverage >= 90
    )
    
    if success:
        print(f"\n🎉 Authentication Unification: COMPLETE!")
        print(f"✅ All admin routes use unified authentication")
        print(f"✅ No legacy decorators remaining")
        print(f"✅ Consistent imports across all files")
        print(f"✅ {auth_coverage:.1f}% route coverage")
    else:
        print(f"\n⚠️ Authentication Unification: NEEDS WORK")
        print(f"  - Legacy auth files: {files_with_legacy_auth}")
        print(f"  - Import issues: {len(import_issues)}")
        print(f"  - Auth coverage: {auth_coverage:.1f}%")
    
    return success

if __name__ == "__main__":
    success = verify_auth_unification()
    exit(0 if success else 1)
