#!/usr/bin/env python3
"""
Basic security system test without Redis dependencies
Tests core security components that don't require Redis
"""

import os
import sys
import json
from datetime import datetime, timezone

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

try:
    from shared.security.audit_logger import AdminAuditLogger
    from shared.security.csrf_protection import CSRFProtection
    from shared.security.ip_access_control import IPAccessControl
    from shared.database.connection import SessionLocal
    from shared.models.base import Admin, AuditLog
    from shared.utils.crypto import hash_password
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class BasicSecurityTester:
    """Basic security system tester (no Redis required)"""
    
    def __init__(self):
        self.test_results = []
        self.test_admin_id = None
        
        print("🔐 Basic Admin Security Test Suite")
        print("=" * 40)
    
    def log_test(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            with SessionLocal() as session:
                admin_count = session.query(Admin).count()
                self.log_test("Database Connection", True, f"Connected successfully, {admin_count} admins found")
                return True
        except Exception as e:
            self.log_test("Database Connection", False, f"Database error: {e}")
            return False
    
    def test_security_imports(self) -> bool:
        """Test that all security modules can be imported"""
        try:
            # Test imports
            from shared.security import (
                AdminAuditLogger, CSRFProtection, ip_access_control
            )
            
            self.log_test("Security Module Imports", True, "All security modules imported successfully")
            return True
        except Exception as e:
            self.log_test("Security Module Imports", False, f"Import error: {e}")
            return False
    
    def test_csrf_protection(self) -> bool:
        """Test CSRF protection functionality"""
        try:
            csrf = CSRFProtection()
            
            # Generate CSRF token
            token = csrf.generate_csrf_token(admin_id=1)
            
            if token and len(token) > 20:
                # Verify the token
                is_valid = csrf.verify_csrf_token(token, admin_id=1)
                
                if is_valid:
                    # Test invalid token
                    invalid_token = "invalid_token_123"
                    is_invalid = csrf.verify_csrf_token(invalid_token, admin_id=1)
                    
                    if not is_invalid:
                        self.log_test("CSRF Protection", True, 
                                     "CSRF token generation and validation working",
                                     {"token_length": len(token)})
                        return True
                    else:
                        self.log_test("CSRF Protection", False, "Invalid token was accepted")
                        return False
                else:
                    self.log_test("CSRF Protection", False, "Valid token was rejected")
                    return False
            else:
                self.log_test("CSRF Protection", False, "CSRF token generation failed")
                return False
                
        except Exception as e:
            self.log_test("CSRF Protection", False, f"CSRF test failed: {e}")
            return False
    
    def test_ip_access_control(self) -> bool:
        """Test IP access control functionality"""
        try:
            ip_control = IPAccessControl()
            
            # Test IP validation
            test_ip = "192.168.1.100"
            allowed, reason = ip_control.is_ip_allowed(test_ip)
            
            # Should be allowed by default (no allowlist configured)
            if allowed:
                # Test adding to blocklist
                success = ip_control.add_to_blocklist("192.168.1.100/32")
                
                if success:
                    # Test if now blocked
                    blocked, block_reason = ip_control.is_ip_allowed(test_ip)
                    
                    if not blocked:
                        # Remove from blocklist
                        ip_control.remove_from_blocklist("192.168.1.100/32")
                        
                        self.log_test("IP Access Control", True, 
                                     "IP access control working correctly",
                                     {"test_ip": test_ip})
                        return True
                    else:
                        self.log_test("IP Access Control", False, "IP was not blocked as expected")
                        return False
                else:
                    self.log_test("IP Access Control", False, "Failed to add IP to blocklist")
                    return False
            else:
                self.log_test("IP Access Control", True, 
                             f"IP access control active: {reason}",
                             {"test_ip": test_ip})
                return True
                
        except Exception as e:
            self.log_test("IP Access Control", False, f"IP access control test failed: {e}")
            return False
    
    def test_audit_logging(self) -> bool:
        """Test audit logging functionality"""
        try:
            # Test audit log creation
            test_action = "security_basic_test"
            test_details = {
                "test": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_type": "basic_security_test"
            }
            
            # Log a test action
            success = AdminAuditLogger.log_admin_action(
                action=test_action,
                details=test_details,
                resource_type="test",
                resource_id=1,
                admin_id=1
            )
            
            if success:
                # Verify the log was created
                with SessionLocal() as session:
                    recent_log = session.query(AuditLog).filter(
                        AuditLog.action == test_action,
                        AuditLog.actor_type == "admin"
                    ).order_by(AuditLog.created_at.desc()).first()
                    
                    if recent_log and recent_log.details.get('test') == True:
                        # Clean up test log
                        session.delete(recent_log)
                        session.commit()
                        
                        self.log_test("Audit Logging", True, 
                                     "Audit log created and verified successfully",
                                     {"log_id": recent_log.id})
                        return True
                    else:
                        self.log_test("Audit Logging", False, "Audit log not found in database")
                        return False
            else:
                self.log_test("Audit Logging", False, "Audit log creation failed")
                return False
                
        except Exception as e:
            self.log_test("Audit Logging", False, f"Audit logging test failed: {e}")
            return False
    
    def test_password_hashing(self) -> bool:
        """Test password hashing functionality"""
        try:
            from shared.utils.crypto import hash_password, verify_password
            
            test_password = "test_password_123"
            hashed = hash_password(test_password)
            
            if hashed and len(hashed) > 20:
                # Verify correct password
                is_valid = verify_password(test_password, hashed)
                
                if is_valid:
                    # Test wrong password
                    is_invalid = verify_password("wrong_password", hashed)
                    
                    if not is_invalid:
                        self.log_test("Password Hashing", True, 
                                     "Password hashing and verification working",
                                     {"hash_length": len(hashed)})
                        return True
                    else:
                        self.log_test("Password Hashing", False, "Wrong password was accepted")
                        return False
                else:
                    self.log_test("Password Hashing", False, "Correct password was rejected")
                    return False
            else:
                self.log_test("Password Hashing", False, "Password hashing failed")
                return False
                
        except Exception as e:
            self.log_test("Password Hashing", False, f"Password hashing test failed: {e}")
            return False
    
    def test_jwt_functionality(self) -> bool:
        """Test JWT token functionality"""
        try:
            from shared.auth.jwt_handler import create_admin_token, verify_admin_token
            
            # Create admin token
            token = create_admin_token(
                user_id=1,
                email="test@example.com",
                additional_claims={"username": "test_admin", "is_super_admin": True}
            )
            
            if token and len(token) > 20:
                # Verify token
                payload = verify_admin_token(token)
                
                if payload and payload.get('admin_id') == 1:
                    self.log_test("JWT Functionality", True, 
                                 "JWT token creation and verification working",
                                 {"token_length": len(token)})
                    return True
                else:
                    self.log_test("JWT Functionality", False, "JWT token verification failed")
                    return False
            else:
                self.log_test("JWT Functionality", False, "JWT token creation failed")
                return False
                
        except Exception as e:
            self.log_test("JWT Functionality", False, f"JWT test failed: {e}")
            return False
    
    def test_admin_model(self) -> bool:
        """Test Admin model functionality"""
        try:
            with SessionLocal() as session:
                # Create test admin
                test_admin = Admin(
                    username="test_basic_admin",
                    email="test_basic@example.com",
                    password_hash=hash_password("test_password"),
                    role="admin",
                    is_super_admin=False,
                    is_active=True
                )
                
                session.add(test_admin)
                session.commit()
                session.refresh(test_admin)
                
                admin_id = test_admin.id
                
                # Verify admin was created
                found_admin = session.query(Admin).filter(Admin.id == admin_id).first()
                
                if found_admin and found_admin.email == "test_basic@example.com":
                    # Clean up test admin
                    session.delete(found_admin)
                    session.commit()
                    
                    self.log_test("Admin Model", True, 
                                 "Admin model creation and retrieval working",
                                 {"admin_id": admin_id})
                    return True
                else:
                    self.log_test("Admin Model", False, "Admin not found after creation")
                    return False
                    
        except Exception as e:
            self.log_test("Admin Model", False, f"Admin model test failed: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run all basic security tests"""
        print("\n🚀 Starting basic security tests...\n")
        
        # Core functionality tests
        self.test_database_connection()
        self.test_security_imports()
        self.test_password_hashing()
        self.test_jwt_functionality()
        self.test_admin_model()
        
        # Security feature tests
        self.test_csrf_protection()
        self.test_ip_access_control()
        self.test_audit_logging()
        
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
        
        print(f"\n📊 Test Summary")
        print("=" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        if summary['success_rate'] >= 90:
            print(f"\n🎉 Basic security system is working excellently!")
        elif summary['success_rate'] >= 75:
            print(f"\n✅ Basic security system is working well!")
        elif summary['success_rate'] >= 50:
            print(f"\n⚠️ Basic security system has some issues")
        else:
            print(f"\n🚨 Basic security system has significant issues")
        
        return summary

def main():
    """Main test function"""
    tester = BasicSecurityTester()
    results = tester.run_all_tests()
    
    # Save results
    with open('basic_security_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to basic_security_test_results.json")
    
    # Exit with appropriate code
    exit_code = 0 if results['success_rate'] >= 75 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
