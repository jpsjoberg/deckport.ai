#!/usr/bin/env python3
"""
Video Streaming System Test Suite
Tests battle streaming, admin surveillance, and security logging
"""

import requests
import json
import time
import sys
from datetime import datetime

class VideoStreamingTester:
    def __init__(self, base_url="http://127.0.0.1:8002"):
        self.base_url = base_url
        self.admin_token = None
        self.device_uid = "DECK_TEST_CONSOLE_01"
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if details:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def setup_admin_auth(self):
        """Setup admin authentication"""
        print("\n🔐 Setting up admin authentication...")
        
        # This would typically use your admin login endpoint
        # For testing, we'll simulate having an admin token
        self.admin_token = "test_admin_token_123"  # Replace with actual token
        
        self.log_test("Admin Authentication Setup", True, "Admin token configured")
    
    def test_arena_system(self):
        """Test arena system functionality"""
        print("\n🏟️ Testing Arena System...")
        
        try:
            # Test arena list endpoint
            response = requests.get(f"{self.base_url}/v1/arenas/list")
            
            if response.status_code == 200:
                data = response.json()
                arena_count = len(data.get('arenas', []))
                self.log_test("Arena List", True, f"Retrieved {arena_count} arenas", data)
            else:
                self.log_test("Arena List", False, f"HTTP {response.status_code}: {response.text}")
                
            # Test weighted arena selection
            preferences = {
                "preferred_themes": ["nature", "crystal"],
                "preferred_rarities": ["rare", "epic"],
                "difficulty_preference": 5,
                "player_level": 10
            }
            
            response = requests.post(f"{self.base_url}/v1/arenas/weighted", json=preferences)
            
            if response.status_code == 200:
                arena_data = response.json()
                self.log_test("Weighted Arena Selection", True, f"Selected arena: {arena_data.get('name')}", arena_data)
            else:
                self.log_test("Weighted Arena Selection", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Arena System", False, f"Exception: {str(e)}")
    
    def test_battle_streaming(self):
        """Test battle video streaming"""
        print("\n⚔️ Testing Battle Video Streaming...")
        
        try:
            # Test starting a battle stream
            battle_data = {
                "opponent_console_id": 999,  # Test opponent
                "battle_id": f"test_battle_{int(time.time())}",
                "enable_camera": False,
                "enable_screen_share": True,
                "enable_audio": False
            }
            
            headers = {
                "X-Device-UID": self.device_uid,
                "Content-Type": "application/json"
            }
            
            response = requests.post(f"{self.base_url}/v1/video/battle/start", 
                                   json=battle_data, headers=headers)
            
            if response.status_code == 200:
                stream_data = response.json()
                stream_id = stream_data.get('stream_id')
                self.log_test("Battle Stream Start", True, f"Stream started: {stream_id}", stream_data)
                
                # Test stream status
                time.sleep(1)
                status_response = requests.get(f"{self.base_url}/v1/video/{stream_id}/status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    self.log_test("Battle Stream Status", True, f"Status: {status_data.get('status')}", status_data)
                else:
                    self.log_test("Battle Stream Status", False, f"HTTP {status_response.status_code}")
                
                # Test ending the stream
                end_response = requests.post(f"{self.base_url}/v1/video/{stream_id}/end")
                
                if end_response.status_code == 200:
                    end_data = end_response.json()
                    self.log_test("Battle Stream End", True, f"Stream ended after {end_data.get('duration_seconds')}s", end_data)
                else:
                    self.log_test("Battle Stream End", False, f"HTTP {end_response.status_code}")
                    
            else:
                self.log_test("Battle Stream Start", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Battle Streaming", False, f"Exception: {str(e)}")
    
    def test_admin_surveillance(self):
        """Test admin surveillance system"""
        print("\n👁️ Testing Admin Surveillance...")
        
        if not self.admin_token:
            self.log_test("Admin Surveillance", False, "No admin token available")
            return
        
        try:
            # Test starting surveillance
            surveillance_data = {
                "console_id": 1,  # Test console ID
                "reason": "Automated testing of surveillance system",
                "enable_audio": True
            }
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(f"{self.base_url}/v1/video/admin/surveillance/start",
                                   json=surveillance_data, headers=headers)
            
            if response.status_code == 200:
                surveillance_data = response.json()
                stream_id = surveillance_data.get('stream_id')
                self.log_test("Admin Surveillance Start", True, f"Surveillance started: {stream_id}", surveillance_data)
                
                # Test viewing surveillance
                time.sleep(1)
                view_response = requests.get(f"{self.base_url}/v1/video/admin/surveillance/{stream_id}/view",
                                           headers=headers)
                
                if view_response.status_code == 200:
                    view_data = view_response.json()
                    self.log_test("Admin Surveillance View", True, f"Surveillance accessible", view_data)
                else:
                    self.log_test("Admin Surveillance View", False, f"HTTP {view_response.status_code}")
                
                # Test getting active streams
                active_response = requests.get(f"{self.base_url}/v1/video/admin/active-streams",
                                             headers=headers)
                
                if active_response.status_code == 200:
                    active_data = active_response.json()
                    stream_count = len(active_data.get('active_streams', []))
                    self.log_test("Active Streams List", True, f"Found {stream_count} active streams", active_data)
                else:
                    self.log_test("Active Streams List", False, f"HTTP {active_response.status_code}")
                
                # Test ending surveillance
                end_response = requests.post(f"{self.base_url}/v1/video/{stream_id}/end", headers=headers)
                
                if end_response.status_code == 200:
                    end_data = end_response.json()
                    self.log_test("Admin Surveillance End", True, f"Surveillance ended", end_data)
                else:
                    self.log_test("Admin Surveillance End", False, f"HTTP {end_response.status_code}")
                    
            else:
                self.log_test("Admin Surveillance Start", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Surveillance", False, f"Exception: {str(e)}")
    
    def test_security_logging(self):
        """Test security logging functionality"""
        print("\n📊 Testing Security Logging...")
        
        if not self.admin_token:
            self.log_test("Security Logging", False, "No admin token available")
            return
        
        try:
            # Create a test stream first
            battle_data = {
                "opponent_console_id": 888,
                "battle_id": f"log_test_battle_{int(time.time())}",
                "enable_camera": True,
                "enable_screen_share": True,
                "enable_audio": True
            }
            
            headers = {
                "X-Device-UID": self.device_uid,
                "Content-Type": "application/json"
            }
            
            response = requests.post(f"{self.base_url}/v1/video/battle/start", 
                                   json=battle_data, headers=headers)
            
            if response.status_code == 200:
                stream_data = response.json()
                stream_id = stream_data.get('stream_id')
                
                # Wait a moment for logs to be generated
                time.sleep(2)
                
                # Test getting stream logs
                admin_headers = {
                    "Authorization": f"Bearer {self.admin_token}"
                }
                
                logs_response = requests.get(f"{self.base_url}/v1/video/{stream_id}/logs",
                                           headers=admin_headers)
                
                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    log_count = len(logs_data.get('logs', []))
                    self.log_test("Security Logging", True, f"Retrieved {log_count} log entries", logs_data)
                else:
                    self.log_test("Security Logging", False, f"HTTP {logs_response.status_code}")
                
                # Clean up - end the stream
                requests.post(f"{self.base_url}/v1/video/{stream_id}/end")
                
            else:
                self.log_test("Security Logging", False, f"Failed to create test stream: {response.status_code}")
                
        except Exception as e:
            self.log_test("Security Logging", False, f"Exception: {str(e)}")
    
    def test_api_endpoints(self):
        """Test all API endpoints for basic connectivity"""
        print("\n🔗 Testing API Endpoints...")
        
        endpoints = [
            ("GET", "/v1/arenas/list", None, None),
            ("GET", "/v1/arenas/random", None, None),
            ("POST", "/v1/arenas/weighted", {"player_level": 5}, None),
        ]
        
        for method, endpoint, data, headers in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, headers=headers)
                elif method == "POST":
                    response = requests.post(url, json=data, headers=headers)
                else:
                    continue
                
                if response.status_code in [200, 201]:
                    self.log_test(f"API {method} {endpoint}", True, f"HTTP {response.status_code}")
                else:
                    self.log_test(f"API {method} {endpoint}", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"API {method} {endpoint}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Video Streaming System Tests")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run tests
        self.setup_admin_auth()
        self.test_api_endpoints()
        self.test_arena_system()
        self.test_battle_streaming()
        self.test_admin_surveillance()
        self.test_security_logging()
        
        # Generate report
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print("🧪 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100,
                    'duration_seconds': duration,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: test_results.json")
        
        return failed_tests == 0

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:8002"
    
    print(f"🎯 Testing against: {base_url}")
    
    tester = VideoStreamingTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
