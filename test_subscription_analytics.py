#!/usr/bin/env python3
"""
Test Subscription Analytics Integration
Tests that subscription revenue is properly included in analytics endpoints
"""

import sys
import json
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

def test_analytics_endpoints():
    """Test analytics endpoints for subscription revenue and frontend compatibility"""
    base_url = "http://127.0.0.1:8002"
    
    print("🧪 TESTING SUBSCRIPTION ANALYTICS INTEGRATION")
    print("=" * 60)
    
    # Test endpoints without authentication first (should get auth errors)
    endpoints_to_test = [
        "/v1/admin/analytics/revenue",
        "/v1/admin/analytics/dashboard-summary",
        "/v1/admin/analytics/player-behavior"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n📊 Testing {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 401:
                print(f"✅ Endpoint exists (returns 401 auth error as expected)")
            elif response.status_code == 404:
                print(f"❌ Endpoint not found (404)")
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                
            # Try to parse JSON response
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Raw response: {response.text[:100]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 SUBSCRIPTION REVENUE STRUCTURE VERIFICATION")
    print("=" * 60)
    
    # Check if the analytics code includes subscription revenue
    try:
        with open('/home/jp/deckport.ai/services/api/routes/admin_analytics.py', 'r') as f:
            content = f.read()
            
        checks = [
            ('subscription_revenue', 'Subscription revenue field in daily data'),
            ('SubscriptionInvoice', 'Subscription invoice model import'),
            ('PaymentStatus.PAID', 'Payment status filtering'),
            ('subscription_daily', 'Daily subscription revenue breakdown'),
            ('devices', 'Devices array for frontend compatibility'),
            ('online_players', 'Online players field for frontend compatibility')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                
    except Exception as e:
        print(f"❌ Error reading analytics file: {e}")
    
    print("\n" + "=" * 60)
    print("🔧 SUBSCRIPTION MODEL VERIFICATION")
    print("=" * 60)
    
    # Check if subscription models exist
    try:
        with open('/home/jp/deckport.ai/shared/models/subscriptions.py', 'r') as f:
            content = f.read()
            
        models = [
            ('class Subscription(Base)', 'Main subscription model'),
            ('class SubscriptionInvoice(Base)', 'Subscription invoice model'),
            ('class SubscriptionUsage(Base)', 'Subscription usage tracking'),
            ('SubscriptionStatus', 'Subscription status enum'),
            ('PaymentStatus', 'Payment status enum'),
            ('BillingInterval', 'Billing interval enum')
        ]
        
        for model, description in models:
            if model in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                
    except Exception as e:
        print(f"❌ Error reading subscription models: {e}")

if __name__ == "__main__":
    test_analytics_endpoints()
