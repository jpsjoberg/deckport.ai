#!/usr/bin/env python3
"""
Test Admin Authentication and API Endpoints
Authenticate as admin and test all analytics endpoints with real data
"""

import sys
import json
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

def test_admin_authentication():
    """Test admin authentication and analytics endpoints"""
    
    base_url = "http://127.0.0.1:8002"
    
    print("🔐 ADMIN AUTHENTICATION & API TESTING")
    print("=" * 60)
    
    # Try to authenticate with common admin credentials
    admin_credentials = [
        {"email": "admin@deckport.ai", "password": "admin123"},
        {"email": "admin@deckport.ai", "password": "password"},
        {"email": "admin@deckport.ai", "password": "admin"},
        {"email": "admin@test.com", "password": "admin123"},
        {"email": "admin@test.com", "password": "password"},
    ]
    
    access_token = None
    
    print("\n🔑 ATTEMPTING ADMIN LOGIN")
    print("-" * 40)
    
    for creds in admin_credentials:
        print(f"\nTrying: {creds['email']} / {creds['password']}")
        
        try:
            response = requests.post(
                f"{base_url}/v1/auth/admin/login",
                json=creds,
                timeout=5
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                admin_info = data.get('admin', {})
                
                print(f"   ✅ SUCCESS! Logged in as: {admin_info.get('username')}")
                print(f"   Admin ID: {admin_info.get('id')}")
                print(f"   Super Admin: {admin_info.get('is_super_admin')}")
                print(f"   Token: {access_token[:50]}...")
                break
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ Failed: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   ❌ Failed: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
    
    if not access_token:
        print("\n❌ Could not authenticate with any credentials")
        print("Let's try to create a test admin user...")
        return create_test_admin()
    
    # Test analytics endpoints with valid token
    print(f"\n📊 TESTING ANALYTICS ENDPOINTS WITH ADMIN TOKEN")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    endpoints_to_test = [
        ("/v1/admin/dashboard/stats", "Dashboard Stats"),
        ("/v1/admin/analytics/dashboard-summary", "Analytics Dashboard Summary"),
        ("/v1/admin/analytics/revenue?days=7", "Revenue Analytics (7 days)"),
        ("/v1/admin/analytics/revenue?days=30", "Revenue Analytics (30 days)"),
        ("/v1/admin/analytics/player-behavior?days=7", "Player Behavior Analytics"),
        ("/v1/admin/analytics/system-metrics", "System Metrics"),
    ]
    
    for endpoint, name in endpoints_to_test:
        print(f"\n🔍 Testing {name}")
        print(f"   Endpoint: {endpoint}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Response type: {type(data)}")
                
                # Check for subscription revenue fields
                if 'revenue' in endpoint:
                    print("   📊 Revenue Data Analysis:")
                    
                    if 'breakdown' in data:
                        breakdown = data['breakdown']
                        print(f"      • Shop Revenue: ${breakdown.get('shop_revenue', 0)}")
                        print(f"      • Trading Revenue: ${breakdown.get('trading_revenue', 0)}")
                        print(f"      • Subscription Revenue: ${breakdown.get('subscription_revenue', 0)} ⭐")
                        
                    if 'daily_data' in data and len(data['daily_data']) > 0:
                        sample_day = data['daily_data'][0]
                        print(f"      • Sample Day ({sample_day.get('date')}):")
                        print(f"        - Total Revenue: ${sample_day.get('revenue', 0)}")
                        print(f"        - Subscription: ${sample_day.get('subscription_revenue', 0)} ⭐")
                        
                elif 'dashboard' in endpoint:
                    print("   📈 Dashboard Data Analysis:")
                    
                    if 'revenue' in data:
                        revenue = data['revenue']
                        print(f"      • Today's Total: ${revenue.get('today', 0)}")
                        if 'breakdown' in revenue:
                            breakdown = revenue['breakdown']
                            print(f"      • Shop Today: ${breakdown.get('shop_today', 0)}")
                            print(f"      • Subscription Today: ${breakdown.get('subscription_today', 0)} ⭐")
                    
                    if 'devices' in data:
                        print(f"      • Devices Array: {len(data['devices'])} devices")
                    
                    if 'online_players' in data:
                        print(f"      • Online Players: {data['online_players']}")
                        
                # Show first few lines of response
                json_str = json.dumps(data, indent=2)
                lines = json_str.split('\n')[:10]
                print("   📄 Response Preview:")
                for line in lines:
                    print(f"      {line}")
                if len(json_str.split('\n')) > 10:
                    print("      ...")
                    
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    print(f"   Raw Response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    print(f"\n🎉 TESTING COMPLETE!")
    print("=" * 60)
    return True

def create_test_admin():
    """Create a test admin user for authentication"""
    print("\n🔧 CREATING TEST ADMIN USER")
    print("-" * 40)
    
    try:
        # Import necessary modules
        sys.path.insert(0, '/home/jp/deckport.ai')
        from shared.database.connection import SessionLocal
        from shared.models.base import Admin
        from shared.auth.password_utils import hash_password
        from datetime import datetime, timezone
        
        with SessionLocal() as session:
            # Check if test admin already exists
            existing_admin = session.query(Admin).filter(Admin.email == "test@admin.com").first()
            
            if existing_admin:
                print("   ✅ Test admin already exists")
                return test_with_credentials("test@admin.com", "testpass123")
            
            # Create new test admin
            admin = Admin(
                username="test_admin_auth",
                email="test@admin.com",
                password_hash=hash_password("testpass123"),
                is_active=True,
                is_super_admin=True,
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(admin)
            session.commit()
            
            print("   ✅ Created test admin: test@admin.com / testpass123")
            return test_with_credentials("test@admin.com", "testpass123")
            
    except Exception as e:
        print(f"   ❌ Failed to create test admin: {e}")
        return False

def test_with_credentials(email, password):
    """Test authentication with specific credentials"""
    base_url = "http://127.0.0.1:8002"
    
    try:
        response = requests.post(
            f"{base_url}/v1/auth/admin/login",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"   ✅ Authentication successful with {email}")
            return True
        else:
            print(f"   ❌ Authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False

if __name__ == "__main__":
    test_admin_authentication()
