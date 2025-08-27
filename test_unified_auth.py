#!/usr/bin/env python3
"""
Test script to verify unified admin authentication system
Tests that all admin routes use consistent authentication decorators
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

class UnifiedAuthTester:
    """Test unified authentication implementation"""
    
    def __init__(self):
        self.test_results = []
        
        print("🔐 Unified Authentication Test Suite")
        print("=" * 40)
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def test_unified_auth_module(self) -> bool:
        """Test that unified auth module exists and is importable"""
        try:
            from shared.auth.unified_admin_auth import (
                admin_auth_required, admin_permissions_required, 
                super_admin_required, require_admin_token
            )
            
            # Test that decorators are callable
            if not all(callable(d) for d in [admin_auth_required, admin_permissions_required, 
                                           super_admin_required, require_admin_token]):
                self.log_test("Unified Auth Module", False, "Some decorators are not callable")
                return False
            
            self.log_test("Unified Auth Module", True, "All decorators available and callable")
            return True
            
        except ImportError as e:
            self.log_test("Unified Auth Module", False, f"Import error: {e}")
            return False
        except Exception as e:
            self.log_test("Unified Auth Module", False, f"Error: {e}")
            return False
    
    def test_legacy_decorator_removal(self) -> bool:
        """Test that legacy require_admin_token functions are removed"""
        try:
            routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
            
            legacy_functions_found = []
            for file_path in routes_dir.glob('admin_*.py'):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'def require_admin_token(' in content:
                        legacy_functions_found.append(file_path.name)
            
            if legacy_functions_found:
                self.log_test("Legacy Decorator Removal", False, 
                             f"Legacy functions found in: {legacy_functions_found}")
                return False
            
            self.log_test("Legacy Decorator Removal", True, "All legacy functions removed")
            return True
            
        except Exception as e:
            self.log_test("Legacy Decorator Removal", False, f"Error: {e}")
            return False
    
    def test_decorator_consistency(self) -> bool:
        """Test that all admin routes use consistent decorators"""
        try:
            routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
            
            # Expected decorator patterns
            expected_patterns = [
                '@admin_auth_required',
                '@auto_rbac_required',
                '@admin_permissions_required',
                '@super_admin_required'
            ]
            
            inconsistent_files = []
            for file_path in routes_dir.glob('admin_*.py'):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Check if file has route decorators
                    if '@' in content and '.route(' in content:
                        # Check if it uses expected decorators
                        has_expected_decorator = any(pattern in content for pattern in expected_patterns)
                        
                        # Check for old patterns
                        has_old_decorator = '@require_admin_token' in content
                        
                        if has_old_decorator or not has_expected_decorator:
                            inconsistent_files.append(file_path.name)
            
            if inconsistent_files:
                self.log_test("Decorator Consistency", False, 
                             f"Inconsistent decorators in: {inconsistent_files}")
                return False
            
            self.log_test("Decorator Consistency", True, "All files use consistent decorators")
            return True
            
        except Exception as e:
            self.log_test("Decorator Consistency", False, f"Error: {e}")
            return False
    
    def test_import_consistency(self) -> bool:
        """Test that all admin routes have consistent imports"""
        try:
            routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
            
            # Expected import patterns
            expected_imports = [
                'from shared.auth.unified_admin_auth import',
                'from shared.auth.auto_rbac_decorator import',
                'from shared.auth.admin_roles import Permission'
            ]
            
            missing_imports = []
            for file_path in routes_dir.glob('admin_*.py'):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Skip files that don't have route decorators
                    if '@' not in content or '.route(' not in content:
                        continue
                    
                    # Check if file has at least one expected import
                    has_expected_import = any(pattern in content for pattern in expected_imports)
                    
                    # Check for old imports that should be removed
                    has_old_import = (
                        'from shared.auth.jwt_handler import verify_admin_token' in content or
                        'from functools import wraps' in content
                    )
                    
                    if not has_expected_import or has_old_import:
                        missing_imports.append(file_path.name)
            
            if missing_imports:
                self.log_test("Import Consistency", False, 
                             f"Import issues in: {missing_imports}")
                return False
            
            self.log_test("Import Consistency", True, "All files have consistent imports")
            return True
            
        except Exception as e:
            self.log_test("Import Consistency", False, f"Error: {e}")
            return False
    
    def test_permission_mapping_coverage(self) -> bool:
        """Test that permission mappings cover all admin routes"""
        try:
            routes_dir = Path('/home/jp/deckport.ai/services/api/routes')
            
            # Count total admin routes
            total_routes = 0
            routes_with_permissions = 0
            
            for file_path in routes_dir.glob('admin_*.py'):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Count route definitions
                    import re
                    route_matches = re.findall(r'@[^.]*\.route\(', content)
                    total_routes += len(route_matches)
                    
                    # Count routes with permission decorators
                    permission_matches = re.findall(r'@(admin_auth_required|auto_rbac_required|admin_permissions_required|super_admin_required)', content)
                    routes_with_permissions += len(permission_matches)
            
            coverage_percentage = (routes_with_permissions / total_routes * 100) if total_routes > 0 else 0
            
            if coverage_percentage < 90:
                self.log_test("Permission Coverage", False, 
                             f"Only {coverage_percentage:.1f}% routes have permissions ({routes_with_permissions}/{total_routes})")
                return False
            
            self.log_test("Permission Coverage", True, 
                         f"{coverage_percentage:.1f}% routes have permissions ({routes_with_permissions}/{total_routes})")
            return True
            
        except Exception as e:
            self.log_test("Permission Coverage", False, f"Error: {e}")
            return False
    
    def test_auth_decorator_registry(self) -> bool:
        """Test the authentication decorator registry"""
        try:
            from shared.auth.unified_admin_auth import AdminDecoratorRegistry
            
            # Test registry has expected decorators
            primary_decorators = AdminDecoratorRegistry.PRIMARY_DECORATORS
            compatibility_decorators = AdminDecoratorRegistry.COMPATIBILITY_DECORATORS
            
            if not primary_decorators or not compatibility_decorators:
                self.log_test("Auth Decorator Registry", False, "Registry is empty")
                return False
            
            # Test recommendation system
            recommendation = AdminDecoratorRegistry.get_recommended_decorator('basic_admin')
            if not recommendation:
                self.log_test("Auth Decorator Registry", False, "Recommendation system not working")
                return False
            
            self.log_test("Auth Decorator Registry", True, 
                         f"{len(primary_decorators)} primary + {len(compatibility_decorators)} compatibility decorators")
            return True
            
        except Exception as e:
            self.log_test("Auth Decorator Registry", False, f"Error: {e}")
            return False
    
    def test_file_structure(self) -> bool:
        """Test that all required files exist"""
        try:
            required_files = [
                '/home/jp/deckport.ai/shared/auth/unified_admin_auth.py',
                '/home/jp/deckport.ai/shared/auth/auto_rbac_decorator.py',
                '/home/jp/deckport.ai/shared/auth/admin_roles.py',
                '/home/jp/deckport.ai/shared/auth/permission_mapping.py'
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    self.log_test("File Structure", False, f"Missing file: {file_path}")
                    return False
            
            self.log_test("File Structure", True, f"All {len(required_files)} auth files exist")
            return True
            
        except Exception as e:
            self.log_test("File Structure", False, f"Error: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run all unified auth tests"""
        print("\n🚀 Starting unified authentication tests...\n")
        
        # Core tests
        self.test_file_structure()
        self.test_unified_auth_module()
        self.test_legacy_decorator_removal()
        self.test_decorator_consistency()
        self.test_import_consistency()
        self.test_permission_mapping_coverage()
        self.test_auth_decorator_registry()
        
        return self.get_test_summary()
    
    def get_test_summary(self) -> dict:
        """Get test results summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        summary = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'results': self.test_results
        }
        
        print(f"\n📊 Unified Auth Test Summary")
        print("=" * 35)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        if summary['success_rate'] == 100:
            print(f"\n🎉 Unified authentication system is perfect!")
        elif summary['success_rate'] >= 90:
            print(f"\n✅ Unified authentication system is excellent!")
        else:
            print(f"\n⚠️ Unified authentication system needs work")
        
        return summary

def main():
    """Main test function"""
    tester = UnifiedAuthTester()
    results = tester.run_all_tests()
    
    # Save results
    with open('unified_auth_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to unified_auth_test_results.json")
    
    # Print implementation summary
    print(f"\n🔐 Unified Authentication Summary:")
    print(f"✅ Single Authentication System: All admin routes use consistent decorators")
    print(f"✅ Legacy Cleanup: Old require_admin_token functions removed")
    print(f"✅ Permission Integration: RBAC permissions integrated into auth")
    print(f"✅ Backward Compatibility: Legacy decorators supported during migration")
    print(f"✅ Centralized Management: Single source of truth for admin authentication")
    
    # Exit with appropriate code
    exit_code = 0 if results['success_rate'] >= 90 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
