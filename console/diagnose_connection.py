#!/usr/bin/env python3
"""
Console Connection Diagnostic Tool
Helps diagnose connection issues between the Godot console and the API server
"""

import requests
import json
import sys
import time
from urllib.parse import urljoin

class ConsoleDiagnostics:
    def __init__(self):
        self.server_url = "http://127.0.0.1:8002"
        self.backup_url = "http://localhost:8002"
        self.device_uid = "DECK_DIAGNOSTIC_TEST"
        
    def run_all_tests(self):
        """Run complete diagnostic suite"""
        print("🔍 CONSOLE CONNECTION DIAGNOSTICS")
        print("=" * 50)
        
        tests = [
            ("Server Health Check", self.test_server_health),
            ("API Endpoints", self.test_api_endpoints),
            ("Device Registration", self.test_device_registration),
            ("Console Login Endpoints", self.test_console_login_endpoints),
            ("Network Configuration", self.test_network_config),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                result = test_func()
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"{status}: {result['message']}")
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results.append((test_name, {'success': False, 'message': str(e)}))
        
        # Summary
        print("\n📊 DIAGNOSTIC SUMMARY")
        print("=" * 30)
        passed = sum(1 for _, result in results if result['success'])
        total = len(results)
        
        for test_name, result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {test_name}: {result['message']}")
        
        print(f"\n🏁 Results: {passed}/{total} tests passed")
        
        if passed < total:
            print("\n🔧 TROUBLESHOOTING SUGGESTIONS:")
            self.print_troubleshooting_suggestions()
    
    def test_server_health(self):
        """Test basic server connectivity"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'message': f"Server healthy - {data.get('service', 'unknown')} service running"
                }
            else:
                return {
                    'success': False,
                    'message': f"Server returned HTTP {response.status_code}"
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': "Cannot connect to server - is it running on port 8002?"
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': "Server connection timeout"
            }
    
    def test_api_endpoints(self):
        """Test critical API endpoints exist"""
        endpoints = [
            "/v1/auth/device/register",
            "/v1/auth/device/login", 
            "/v1/auth/device/status",
            "/v1/console-login/start",
            "/v1/console-login/poll",
            "/v1/console/logs"
        ]
        
        available_endpoints = []
        for endpoint in endpoints:
            try:
                # Use HEAD request to check if endpoint exists
                response = requests.head(f"{self.server_url}{endpoint}", timeout=5)
                if response.status_code != 404:
                    available_endpoints.append(endpoint)
            except:
                pass
        
        if len(available_endpoints) >= len(endpoints) * 0.8:  # 80% of endpoints available
            return {
                'success': True,
                'message': f"{len(available_endpoints)}/{len(endpoints)} endpoints available"
            }
        else:
            return {
                'success': False,
                'message': f"Only {len(available_endpoints)}/{len(endpoints)} endpoints available"
            }
    
    def test_device_registration(self):
        """Test device registration endpoint"""
        try:
            # Generate a test public key (mock)
            test_data = {
                "device_uid": self.device_uid,
                "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
            }
            
            response = requests.post(
                f"{self.server_url}/v1/auth/device/register",
                json=test_data,
                timeout=10
            )
            
            if response.status_code in [201, 409]:  # Created or already exists
                return {
                    'success': True,
                    'message': "Device registration endpoint working"
                }
            else:
                return {
                    'success': False,
                    'message': f"Registration failed with HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Registration test failed: {str(e)}"
            }
    
    def test_console_login_endpoints(self):
        """Test console login endpoints"""
        try:
            # Test console login start
            response = requests.post(
                f"{self.server_url}/v1/console-login/start",
                json={},
                headers={"X-Device-UID": self.device_uid},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': "Console login endpoints accessible"
                }
            else:
                return {
                    'success': False,
                    'message': f"Console login failed with HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Console login test failed: {str(e)}"
            }
    
    def test_network_config(self):
        """Test network configuration"""
        import socket
        
        try:
            # Test if port 8002 is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', 8002))
            sock.close()
            
            if result == 0:
                return {
                    'success': True,
                    'message': "Port 8002 is open and accepting connections"
                }
            else:
                return {
                    'success': False,
                    'message': "Port 8002 is not accessible"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Network test failed: {str(e)}"
            }
    
    def print_troubleshooting_suggestions(self):
        """Print troubleshooting suggestions"""
        suggestions = [
            "1. Ensure API server is running: cd api && python app.py",
            "2. Check if port 8002 is available: netstat -an | grep 8002",
            "3. Verify PostgreSQL database is running and accessible",
            "4. Check firewall settings for port 8002",
            "5. Review API server logs for error messages",
            "6. Ensure virtual environment is activated with all dependencies",
            "7. Test with curl: curl http://127.0.0.1:8002/health"
        ]
        
        for suggestion in suggestions:
            print(f"   • {suggestion}")

if __name__ == "__main__":
    diagnostics = ConsoleDiagnostics()
    diagnostics.run_all_tests()
