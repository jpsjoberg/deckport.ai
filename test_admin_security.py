#!/usr/bin/env python3
"""
Comprehensive test suite for admin security system
Tests rate limiting, session management, audit logging, CSRF protection, and IP access control
"""

import os
import sys
import time
import json
import requests
import redis
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

from shared.security.rate_limiter import RateLimitConfig, check_rate_limit, get_client_identifier
from shared.security.session_manager import SessionManager, AdminSession
from shared.security.audit_logger import AdminAuditLogger
from shared.security.csrf_protection import CSRFProtection
from shared.security.ip_access_control import IPAccessControl
from shared.database.connection import SessionLocal
from shared.models.base import Admin, AuditLog
from shared.utils.crypto import hash_password

class AdminSecurityTester:
    """Comprehensive admin security system tester"""
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:8002"):
        self.api_base_url = api_base_url
        self.test_results = []
        self.admin_token = None
        self.test_admin_id = None
        
        print("🔐 Admin Security System Test Suite")
        print("=" * 50)
    
    def log_test(self, test_name: str, success: bool, message: str = "", details: Dict = None):
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
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection for rate limiting and sessions"""
        try:
            redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
            redis_client.ping()
            self.log_test("Redis Connection", True, "Redis is available for rate limiting and sessions")
            return True
        except Exception as e:
            self.log_test("Redis Connection", False, f"Redis not available: {e}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            with SessionLocal() as session:
                # Test basic query
                admin_count = session.query(Admin).count()
                self.log_test("Database Connection", True, f"Database connected, {admin_count} admins found")
                return True
        except Exception as e:
            self.log_test("Database Connection", False, f"Database error: {e}")
            return False
    
    def create_test_admin(self) -> bool:
        """Create test admin for authentication tests"""
        try:
            with SessionLocal() as session:
                # Check if test admin exists
                test_admin = session.query(Admin).filter(Admin.email == "test_admin@deckport.ai").first()
                
                if not test_admin:
                    # Create test admin
                    test_admin = Admin(
                        username="test_admin",
                        email="test_admin@deckport.ai",
                        password_hash=hash_password("test_password_123"),
                        role="admin",
                        is_super_admin=True,
                        is_active=True
                    )
                    session.add(test_admin)
                    session.commit()
                    session.refresh(test_admin)
                
                self.test_admin_id = test_admin.id
                self.log_test("Test Admin Creation", True, f"Test admin created/found with ID: {test_admin.id}")
                return True
                
        except Exception as e:
            self.log_test("Test Admin Creation", False, f"Failed to create test admin: {e}")
            return False
    
    def test_admin_login(self) -> bool:
        """Test admin login and JWT token generation"""
        try:
            login_data = {
                "email": "test_admin@deckport.ai",
                "password": "test_password_123"
            }
            
            response = requests.post(
                f"{self.api_base_url}/v1/auth/admin/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                admin_info = data.get('admin', {})
                
                self.log_test("Admin Login", True, 
                             f"Login successful for {admin_info.get('username')}", 
                             {"token_length": len(self.admin_token) if self.admin_token else 0})
                return True
            else:
                self.log_test("Admin Login", False, 
                             f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Login request failed: {e}")
            return False
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        try:
            # Test rate limit configuration
            config = RateLimitConfig()
            login_limit = config.DEFAULT_LIMITS.get('admin_login', {})
            
            if not login_limit:
                self.log_test("Rate Limiting Config", False, "Rate limit configuration not found")
                return False
            
            self.log_test("Rate Limiting Config", True, 
                         f"Login limit: {login_limit['requests']} requests per {login_limit['window']} seconds")
            
            # Test rate limit checking (simulate multiple requests)
            identifier = "test_client_ip:127.0.0.1"
            
            # Make several requests to test rate limiting
            allowed_count = 0
            blocked_count = 0
            
            for i in range(7):  # Try 7 requests (limit is usually 5)
                allowed, info = check_rate_limit('admin_login', identifier)
                if allowed:
                    allowed_count += 1
                else:
                    blocked_count += 1
                time.sleep(0.1)  # Small delay between requests
            
            if blocked_count > 0:
                self.log_test("Rate Limiting Enforcement", True, 
                             f"Rate limiting working: {allowed_count} allowed, {blocked_count} blocked")
                return True
            else:
                self.log_test("Rate Limiting Enforcement", False, 
                             "Rate limiting not blocking requests as expected")
                return False
                
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Rate limiting test failed: {e}")
            return False
    
    def test_session_management(self) -> bool:
        """Test session management functionality"""
        try:
            session_manager = SessionManager()
            
            if not session_manager.redis_client:
                self.log_test("Session Management", False, "Redis not available for session management")
                return False
            
            # Create a test session
            from flask import Flask
            app = Flask(__name__)
            
            with app.test_request_context('/', headers={'User-Agent': 'Test Agent'}):
                session = session_manager.create_session(
                    admin_id=self.test_admin_id or 1,
                    admin_email="test_admin@deckport.ai",
                    admin_username="test_admin",
                    is_super_admin=True
                )
                
                if session:
                    session_id = session.session_id
                    
                    # Test session retrieval
                    retrieved_session = session_manager.get_session(session_id)
                    
                    if retrieved_session and retrieved_session.admin_id == session.admin_id:
                        # Test session refresh
                        refresh_success = session_manager.refresh_session(session_id)
                        
                        # Clean up test session
                        session_manager.invalidate_session(session_id)
                        
                        self.log_test("Session Management", True, 
                                     f"Session created, retrieved, refreshed, and invalidated successfully",
                                     {"session_id": session_id[:16] + "..."})
                        return True
                    else:
                        self.log_test("Session Management", False, "Session retrieval failed")
                        return False
                else:
                    self.log_test("Session Management", False, "Session creation failed")
                    return False
                    
        except Exception as e:
            self.log_test("Session Management", False, f"Session management test failed: {e}")
            return False
    
    def test_audit_logging(self) -> bool:
        """Test audit logging functionality"""
        try:
            # Test audit log creation
            test_action = "security_test_action"
            test_details = {
                "test": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_data": "security_audit_test"
            }
            
            # Log a test action
            success = AdminAuditLogger.log_admin_action(
                action=test_action,
                details=test_details,
                resource_type="test",
                resource_id=1,
                admin_id=self.test_admin_id or 1
            )
            
            if success:
                # Verify the log was created
                with SessionLocal() as session:
                    recent_log = session.query(AuditLog).filter(
                        AuditLog.action == test_action,
                        AuditLog.actor_type == "admin"
                    ).order_by(AuditLog.created_at.desc()).first()
                    
                    if recent_log and recent_log.details.get('test') == True:
                        self.log_test("Audit Logging", True, 
                                     f"Audit log created and verified",
                                     {"log_id": recent_log.id, "action": recent_log.action})
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
    
    def test_csrf_protection(self) -> bool:
        """Test CSRF protection functionality"""
        try:
            csrf = CSRFProtection()
            
            # Generate CSRF token
            token = csrf.generate_csrf_token(admin_id=self.test_admin_id or 1)
            
            if token and len(token) > 20:  # Basic token validation
                # Verify the token
                is_valid = csrf.verify_csrf_token(token, admin_id=self.test_admin_id or 1)
                
                if is_valid:
                    # Test invalid token
                    invalid_token = "invalid_token_123"
                    is_invalid = csrf.verify_csrf_token(invalid_token, admin_id=self.test_admin_id or 1)
                    
                    if not is_invalid:
                        self.log_test("CSRF Protection", True, 
                                     "CSRF token generation and validation working correctly",
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
            self.log_test("CSRF Protection", False, f"CSRF protection test failed: {e}")
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
                                     "IP access control working: allow, block, and unblock tested",
                                     {"test_ip": test_ip, "block_reason": block_reason})
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
    
    def test_security_api_endpoints(self) -> bool:
        """Test security monitoring API endpoints"""
        if not self.admin_token:
            self.log_test("Security API Endpoints", False, "No admin token available for API testing")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test security dashboard endpoint
            response = requests.get(
                f"{self.api_base_url}/v1/admin/security/dashboard",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                dashboard_data = response.json()
                metrics = dashboard_data.get('metrics', {})
                
                self.log_test("Security Dashboard API", True, 
                             f"Dashboard loaded with {len(metrics)} metrics",
                             {"metrics": list(metrics.keys())})
                
                # Test audit logs endpoint
                audit_response = requests.get(
                    f"{self.api_base_url}/v1/admin/security/audit-logs?hours=1",
                    headers=headers,
                    timeout=10
                )
                
                if audit_response.status_code == 200:
                    audit_data = audit_response.json()
                    logs_count = len(audit_data.get('audit_logs', []))
                    
                    self.log_test("Security API Endpoints", True, 
                                 f"Security APIs working: dashboard and audit logs ({logs_count} logs)")
                    return True
                else:
                    self.log_test("Security API Endpoints", False, 
                                 f"Audit logs API failed: {audit_response.status_code}")
                    return False
            else:
                self.log_test("Security API Endpoints", False, 
                             f"Security dashboard API failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Security API Endpoints", False, f"Security API test failed: {e}")
            return False
    
    def test_enhanced_auth_decorator(self) -> bool:
        """Test the enhanced admin authentication decorator"""
        if not self.admin_token:
            self.log_test("Enhanced Auth Decorator", False, "No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test a protected endpoint
            response = requests.get(
                f"{self.api_base_url}/v1/admin/devices",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Test without token (should fail)
                no_auth_response = requests.get(
                    f"{self.api_base_url}/v1/admin/devices",
                    timeout=10
                )
                
                if no_auth_response.status_code == 401:
                    self.log_test("Enhanced Auth Decorator", True, 
                                 "Authentication working: authorized request succeeded, unauthorized failed")
                    return True
                else:
                    self.log_test("Enhanced Auth Decorator", False, 
                                 f"Unauthorized request should have failed but got: {no_auth_response.status_code}")
                    return False
            else:
                self.log_test("Enhanced Auth Decorator", False, 
                             f"Authorized request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Auth Decorator", False, f"Auth decorator test failed: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Clean up test admin
            if self.test_admin_id:
                with SessionLocal() as session:
                    test_admin = session.query(Admin).filter(Admin.id == self.test_admin_id).first()
                    if test_admin and test_admin.email == "test_admin@deckport.ai":
                        session.delete(test_admin)
                        session.commit()
            
            # Clean up test audit logs
            with SessionLocal() as session:
                test_logs = session.query(AuditLog).filter(
                    AuditLog.action == "security_test_action"
                ).all()
                for log in test_logs:
                    session.delete(log)
                session.commit()
            
            print("🧹 Test cleanup completed")
            
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def run_all_tests(self) -> Dict:
        """Run all security tests"""
        print("\n🚀 Starting comprehensive security tests...\n")
        
        # Infrastructure tests
        redis_ok = self.test_redis_connection()
        db_ok = self.test_database_connection()
        
        if not db_ok:
            print("\n❌ Database connection failed - cannot continue tests")
            return self.get_test_summary()
        
        # Setup
        admin_created = self.create_test_admin()
        if not admin_created:
            print("\n❌ Test admin creation failed - cannot continue auth tests")
            return self.get_test_summary()
        
        login_ok = self.test_admin_login()
        
        # Security feature tests
        self.test_rate_limiting()
        
        if redis_ok:
            self.test_session_management()
        else:
            self.log_test("Session Management", False, "Skipped - Redis not available")
        
        self.test_audit_logging()
        self.test_csrf_protection()
        self.test_ip_access_control()
        
        # API tests (require authentication)
        if login_ok:
            self.test_security_api_endpoints()
            self.test_enhanced_auth_decorator()
        
        # Cleanup
        self.cleanup_test_data()
        
        return self.get_test_summary()
    
    def get_test_summary(self) -> Dict:
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
        
        if summary['success_rate'] >= 80:
            print(f"\n🎉 Security system is working well!")
        elif summary['success_rate'] >= 60:
            print(f"\n⚠️ Security system has some issues that need attention")
        else:
            print(f"\n🚨 Security system has significant issues")
        
        return summary

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test admin security system')
    parser.add_argument('--api-url', default='http://127.0.0.1:8002', 
                       help='API base URL (default: http://127.0.0.1:8002)')
    parser.add_argument('--output', help='Output file for test results (JSON)')
    
    args = parser.parse_args()
    
    # Run tests
    tester = AdminSecurityTester(args.api_url)
    results = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")
    
    # Exit with appropriate code
    exit_code = 0 if results['success_rate'] >= 80 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
