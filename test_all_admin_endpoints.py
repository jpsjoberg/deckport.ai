#!/usr/bin/env python3
"""
Comprehensive Admin Endpoints Test
Tests all admin endpoints to verify they're working correctly
"""

import sys
import json
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

def test_all_admin_endpoints():
    """Test all admin endpoints comprehensively"""
    
    base_url = "http://127.0.0.1:8002"
    
    print("🔍 COMPREHENSIVE ADMIN ENDPOINTS TEST")
    print("=" * 80)
    
    # First authenticate
    print("\n🔑 AUTHENTICATING AS ADMIN")
    print("-" * 40)
    
    auth_response = requests.post(
        f"{base_url}/v1/auth/admin/login",
        json={"email": "admin@deckport.ai", "password": "admin123"},
        timeout=5
    )
    
    if auth_response.status_code != 200:
        print("❌ Authentication failed!")
        return False
    
    token_data = auth_response.json()
    access_token = token_data.get('access_token')
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"✅ Authenticated as: {token_data.get('admin', {}).get('username')}")
    
    # Define all admin endpoints to test
    admin_endpoints = [
        # Analytics Endpoints
        ("/v1/admin/analytics/revenue", "GET", "Revenue Analytics"),
        ("/v1/admin/analytics/revenue?days=7", "GET", "Revenue Analytics (7 days)"),
        ("/v1/admin/analytics/revenue?days=30", "GET", "Revenue Analytics (30 days)"),
        ("/v1/admin/analytics/player-behavior", "GET", "Player Behavior Analytics"),
        ("/v1/admin/analytics/player-behavior?days=7", "GET", "Player Behavior (7 days)"),
        ("/v1/admin/analytics/card-usage", "GET", "Card Usage Analytics"),
        ("/v1/admin/analytics/system-metrics", "GET", "System Metrics"),
        ("/v1/admin/analytics/dashboard-summary", "GET", "Dashboard Summary"),
        
        # Dashboard Endpoints
        ("/v1/admin/dashboard/stats", "GET", "Dashboard Stats"),
        ("/v1/admin/dashboard/live-data", "GET", "Dashboard Live Data"),
        
        # Player Management
        ("/v1/admin/players", "GET", "List Players"),
        ("/v1/admin/players/stats", "GET", "Player Statistics"),
        ("/v1/admin/players/search?q=test", "GET", "Search Players"),
        
        # Device Management
        ("/v1/admin/devices", "GET", "List Devices"),
        ("/v1/admin/devices/pending", "GET", "Pending Devices"),
        ("/v1/admin/devices/stats", "GET", "Device Statistics"),
        
        # Communications
        ("/v1/admin/communications/announcements", "GET", "List Announcements"),
        ("/v1/admin/communications/campaigns", "GET", "Email Campaigns"),
        
        # Shop Management
        ("/v1/admin/shop/stats", "GET", "Shop Statistics"),
        ("/v1/admin/shop/products", "GET", "Shop Products"),
        ("/v1/admin/shop/orders", "GET", "Shop Orders"),
        
        # Tournament Management
        ("/v1/admin/tournaments", "GET", "List Tournaments"),
        ("/v1/admin/tournaments/stats", "GET", "Tournament Statistics"),
        
        # Arena Management
        ("/v1/admin/arenas", "GET", "List Arenas"),
        ("/v1/admin/arenas/stats", "GET", "Arena Statistics"),
        
        # Alerts and Notifications
        ("/v1/admin/alerts", "GET", "System Alerts"),
        
        # NFC Card Management
        ("/v1/nfc-cards/admin/stats", "GET", "NFC Card Statistics"),
        
        # User Profile Management
        ("/v1/admin/profiles", "GET", "User Profiles"),
        
        # Game Operations
        ("/v1/admin/game-operations/matches", "GET", "Active Matches"),
        ("/v1/admin/game-operations/analytics/player-activity", "GET", "Game Analytics"),
    ]
    
    print(f"\n📊 TESTING {len(admin_endpoints)} ADMIN ENDPOINTS")
    print("=" * 80)
    
    results = {
        'working': [],
        'auth_required': [],
        'not_found': [],
        'server_error': [],
        'other_error': []
    }
    
    for endpoint, method, description in admin_endpoints:
        print(f"\n🔍 Testing: {description}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(f"{base_url}{endpoint}", headers=headers, json={}, timeout=10)
            else:
                response = requests.request(method, f"{base_url}{endpoint}", headers=headers, timeout=10)
            
            status = response.status_code
            print(f"   Status: {status}")
            
            if status == 200:
                print(f"   ✅ SUCCESS")
                try:
                    data = response.json()
                    print(f"   📄 Response type: {type(data)}")
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]  # Show first 5 keys
                        print(f"   🔑 Keys: {keys}")
                except:
                    print(f"   📄 Non-JSON response")
                results['working'].append((endpoint, description, status))
                
            elif status == 401:
                print(f"   🔒 AUTH REQUIRED (unexpected - we have token)")
                results['auth_required'].append((endpoint, description, status))
                
            elif status == 404:
                print(f"   ❌ NOT FOUND")
                results['not_found'].append((endpoint, description, status))
                
            elif status >= 500:
                print(f"   💥 SERVER ERROR")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    print(f"   📄 Error: {error_msg[:100]}...")
                except:
                    print(f"   📄 Raw error: {response.text[:100]}...")
                results['server_error'].append((endpoint, description, status))
                
            else:
                print(f"   ⚠️  OTHER ERROR")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    print(f"   📄 Error: {error_msg[:100]}...")
                except:
                    print(f"   📄 Raw response: {response.text[:100]}...")
                results['other_error'].append((endpoint, description, status))
                
        except requests.exceptions.RequestException as e:
            print(f"   💥 CONNECTION ERROR: {e}")
            results['other_error'].append((endpoint, description, "CONNECTION_ERROR"))
        except Exception as e:
            print(f"   💥 UNEXPECTED ERROR: {e}")
            results['other_error'].append((endpoint, description, "UNEXPECTED_ERROR"))
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("📋 ADMIN ENDPOINTS TEST SUMMARY")
    print("=" * 80)
    
    total_endpoints = len(admin_endpoints)
    working_count = len(results['working'])
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total Endpoints Tested: {total_endpoints}")
    print(f"   ✅ Working: {working_count}")
    print(f"   🔒 Auth Issues: {len(results['auth_required'])}")
    print(f"   ❌ Not Found: {len(results['not_found'])}")
    print(f"   💥 Server Errors: {len(results['server_error'])}")
    print(f"   ⚠️  Other Errors: {len(results['other_error'])}")
    print(f"   📈 Success Rate: {(working_count/total_endpoints)*100:.1f}%")
    
    if results['working']:
        print(f"\n✅ WORKING ENDPOINTS ({len(results['working'])}):")
        for endpoint, desc, status in results['working']:
            print(f"   • {desc} - {endpoint}")
    
    if results['auth_required']:
        print(f"\n🔒 AUTH REQUIRED ({len(results['auth_required'])}):")
        for endpoint, desc, status in results['auth_required']:
            print(f"   • {desc} - {endpoint}")
    
    if results['not_found']:
        print(f"\n❌ NOT FOUND ({len(results['not_found'])}):")
        for endpoint, desc, status in results['not_found']:
            print(f"   • {desc} - {endpoint}")
    
    if results['server_error']:
        print(f"\n💥 SERVER ERRORS ({len(results['server_error'])}):")
        for endpoint, desc, status in results['server_error']:
            print(f"   • {desc} - {endpoint} ({status})")
    
    if results['other_error']:
        print(f"\n⚠️  OTHER ERRORS ({len(results['other_error'])}):")
        for endpoint, desc, status in results['other_error']:
            print(f"   • {desc} - {endpoint} ({status})")
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATIONS:")
    
    if results['not_found']:
        print("   1. Implement missing endpoints or update routing")
    if results['server_error']:
        print("   2. Fix server errors in failing endpoints")
    if results['auth_required']:
        print("   3. Check authentication/authorization logic")
    if working_count == total_endpoints:
        print("   🎉 ALL ENDPOINTS WORKING! System is ready for production!")
    
    return results

if __name__ == "__main__":
    test_all_admin_endpoints()
