#!/usr/bin/env python3
"""
Comprehensive Admin Routes Testing
Tests every admin route with proper authentication to identify and fix all issues
"""

import sys
import requests
import json
from datetime import datetime

# Admin credentials
ADMIN_EMAIL = "admin@deckport.ai"
ADMIN_PASSWORD = "admin123"
BASE_URL = "https://deckport.ai"

class AdminRouteTester:
    """Comprehensive admin route testing system"""
    
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """Log test results"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
        
    def get_admin_token(self):
        """Get admin JWT token for authentication"""
        self.log("Getting admin authentication token...")
        
        try:
            # First get the login page to get CSRF token
            login_page = self.session.get(f"{BASE_URL}/admin/login")
            if login_page.status_code != 200:
                self.log(f"Failed to load login page: {login_page.status_code}", "ERROR")
                return False
            
            # Extract CSRF token from page
            csrf_token = None
            if 'name="csrf"' in login_page.text:
                import re
                csrf_match = re.search(r'name="csrf" value="([^"]+)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
            
            if not csrf_token:
                self.log("Could not extract CSRF token", "ERROR")
                return False
            
            # Attempt login
            login_data = {
                'email': ADMIN_EMAIL,
                'password': ADMIN_PASSWORD,
                'csrf': csrf_token
            }
            
            response = self.session.post(f"{BASE_URL}/admin/login", data=login_data, allow_redirects=False)
            
            if response.status_code == 302:
                # Check if admin_jwt cookie was set
                admin_jwt = None
                for cookie in self.session.cookies:
                    if cookie.name == 'admin_jwt':
                        admin_jwt = cookie.value
                        break
                
                if admin_jwt:
                    self.admin_token = admin_jwt
                    self.log("✅ Admin authentication successful", "SUCCESS")
                    return True
                else:
                    self.log("Login redirect occurred but no admin_jwt cookie set", "ERROR")
                    return False
            else:
                self.log(f"Login failed with status: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"Response: {response.text[:200]}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Authentication error: {e}", "ERROR")
            return False
    
    def test_route(self, route_path, method="GET", description=""):
        """Test a specific admin route"""
        url = f"{BASE_URL}{route_path}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json={}, timeout=10)
            else:
                response = self.session.request(method, url, timeout=10)
            
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            self.log(f"{status} {method} {route_path} - {description}")
            
            result = {
                'route': route_path,
                'method': method,
                'status_code': response.status_code,
                'description': description,
                'success': response.status_code == 200,
                'error': None
            }
            
            if response.status_code != 200:
                # Get error details
                if response.status_code == 500:
                    result['error'] = "Internal Server Error"
                elif response.status_code == 404:
                    result['error'] = "Route not found"
                elif response.status_code == 403:
                    result['error'] = "Permission denied"
                else:
                    result['error'] = f"HTTP {response.status_code}"
                
                # Log error details for debugging
                if response.status_code == 500:
                    self.log(f"  500 Error details: {response.text[:100]}", "ERROR")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            self.log(f"❌ EXCEPTION {method} {route_path} - {e}", "ERROR")
            result = {
                'route': route_path,
                'method': method,
                'status_code': 0,
                'description': description,
                'success': False,
                'error': str(e)
            }
            self.test_results.append(result)
            return result
    
    def test_all_admin_routes(self):
        """Test all admin routes comprehensively"""
        self.log("🔍 Starting comprehensive admin route testing...")
        
        # Core admin routes
        routes_to_test = [
            # Dashboard and main routes
            ("/admin/", "GET", "Main admin dashboard"),
            ("/admin/dashboard", "GET", "Dashboard"),
            
            # Console management
            ("/admin/consoles", "GET", "Console fleet management"),
            
            # Card management  
            ("/admin/cards", "GET", "Card management dashboard"),
            ("/admin/cards/generate", "GET", "Card generation interface"),
            ("/admin/cards/review", "GET", "Card review interface"),
            
            # Game operations
            ("/admin/game-operations", "GET", "Game operations dashboard"),
            
            # Player management
            ("/admin/players", "GET", "Player management"),
            
            # NFC management
            ("/admin/nfc-cards", "GET", "NFC card management"),
            
            # Shop management
            ("/admin/shop", "GET", "Shop management"),
            
            # Analytics
            ("/admin/analytics", "GET", "Analytics dashboard"),
            
            # System administration
            ("/admin/system", "GET", "System administration"),
            
            # Communications
            ("/admin/communications", "GET", "Communications center"),
            
            # API endpoints
            ("/admin/api/dashboard/stats", "GET", "Dashboard stats API"),
            ("/admin/api/alerts", "GET", "Alerts API"),
        ]
        
        # Test each route
        passed = 0
        failed = 0
        
        for route, method, description in routes_to_test:
            result = self.test_route(route, method, description)
            if result['success']:
                passed += 1
            else:
                failed += 1
        
        return passed, failed
    
    def generate_report(self):
        """Generate test report"""
        self.log("=" * 60)
        self.log("📊 ADMIN ROUTES TEST REPORT")
        self.log("=" * 60)
        
        passed = len([r for r in self.test_results if r['success']])
        failed = len([r for r in self.test_results if not r['success']])
        
        self.log(f"Total Routes Tested: {len(self.test_results)}")
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        
        if failed > 0:
            self.log("\n❌ FAILED ROUTES:")
            for result in self.test_results:
                if not result['success']:
                    self.log(f"  {result['method']} {result['route']} - {result['error']}")
        
        self.log("=" * 60)
        
        return passed, failed

def main():
    """Main testing function"""
    print("🎮 Deckport Admin Panel - Comprehensive Route Testing")
    print("=" * 70)
    
    tester = AdminRouteTester()
    
    # Step 1: Authenticate
    if not tester.get_admin_token():
        print("❌ Authentication failed - cannot test admin routes")
        return False
    
    # Step 2: Test all routes
    passed, failed = tester.test_all_admin_routes()
    
    # Step 3: Generate report
    tester.generate_report()
    
    # Step 4: Return overall result
    if failed == 0:
        print("\n🎉 ALL ADMIN ROUTES WORKING - PRODUCTION READY!")
        return True
    else:
        print(f"\n⚠️ {failed} ROUTES NEED FIXING FOR PRODUCTION")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
