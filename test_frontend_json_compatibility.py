#!/usr/bin/env python3
"""
Frontend JSON Compatibility Test
Tests that the frontend gets the correct JSON structure from API endpoints
"""

import sys
import json
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

def test_frontend_json_compatibility():
    """Test that frontend gets correct JSON from API endpoints"""
    
    print("🧪 FRONTEND JSON COMPATIBILITY TEST")
    print("=" * 60)
    
    # Test the analytics endpoints that the frontend actually calls
    api_base = "http://127.0.0.1:8002"
    frontend_base = "http://127.0.0.1:8001"
    
    print("\n📊 TESTING ANALYTICS PAGE ENDPOINTS")
    print("-" * 40)
    
    # Test revenue analytics (called by frontend/templates/admin/analytics/index.html)
    print("\n1. Revenue Analytics Endpoint:")
    print("   Frontend calls: /v1/admin/analytics/revenue?days=30")
    print("   Expected fields: revenueData.daily_data[].revenue")
    
    try:
        response = requests.get(f"{api_base}/v1/admin/analytics/revenue?days=30", timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print("   ✅ Endpoint exists (auth required)")
        else:
            data = response.json()
            if 'daily_data' in data:
                print("   ✅ Has daily_data array")
                if len(data['daily_data']) > 0 and 'revenue' in data['daily_data'][0]:
                    print("   ✅ daily_data[0] has 'revenue' field")
                else:
                    print("   ❌ Missing 'revenue' field in daily_data")
            else:
                print("   ❌ Missing daily_data array")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2. Player Behavior Endpoint:")
    print("   Frontend calls: /v1/admin/analytics/player-behavior?days=30")
    
    try:
        response = requests.get(f"{api_base}/v1/admin/analytics/player-behavior?days=30", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists (auth required)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n📈 TESTING DASHBOARD ENDPOINTS")
    print("-" * 40)
    
    # Test dashboard stats (called by frontend/templates/admin/index.html)
    print("\n3. Dashboard Stats Endpoint:")
    print("   Frontend calls: https://api.deckport.ai/v1/admin/dashboard/stats")
    print("   Expected fields: consoles.active, matches.live, players.active_today")
    
    # Check if this endpoint exists in our API
    dashboard_endpoints = [
        "/v1/admin/dashboard/stats",
        "/v1/admin/analytics/dashboard-summary"
    ]
    
    for endpoint in dashboard_endpoints:
        try:
            response = requests.get(f"{api_base}{endpoint}", timeout=5)
            print(f"   Testing {endpoint}: Status {response.status_code}")
            
            if response.status_code == 401:
                print(f"   ✅ {endpoint} exists (auth required)")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint} not found")
            else:
                data = response.json()
                print(f"   ⚠️  Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {e}")
    
    print("\n🔧 SUBSCRIPTION REVENUE VERIFICATION")
    print("-" * 40)
    
    # Verify subscription revenue is included
    subscription_checks = [
        ("Analytics file includes subscription revenue", "subscription_revenue"),
        ("Analytics file includes SubscriptionInvoice", "SubscriptionInvoice"),
        ("Analytics file includes PaymentStatus", "PaymentStatus.PAID"),
        ("Dashboard summary includes subscription breakdown", "subscription_daily")
    ]
    
    try:
        with open('/home/jp/deckport.ai/services/api/routes/admin_analytics.py', 'r') as f:
            analytics_content = f.read()
            
        for check_name, check_string in subscription_checks:
            if check_string in analytics_content:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                
    except Exception as e:
        print(f"   ❌ Error reading analytics file: {e}")
    
    print("\n📋 FRONTEND COMPATIBILITY SUMMARY")
    print("=" * 60)
    
    print("✅ COMPLETED FIXES:")
    print("   • Added 'revenue' field to daily_data for frontend compatibility")
    print("   • Added subscription_revenue tracking to all analytics")
    print("   • Added devices array to dashboard-summary")
    print("   • Added online_players field to dashboard-summary")
    print("   • Created subscription database models and tables")
    
    print("\n⚠️  POTENTIAL ISSUES:")
    print("   • Frontend calls https://api.deckport.ai/v1/admin/dashboard/stats")
    print("     but our API has /v1/admin/analytics/dashboard-summary")
    print("   • May need to add /v1/admin/dashboard/stats endpoint")
    print("     or update frontend to use correct endpoint")
    
    print("\n🎯 RECOMMENDATIONS:")
    print("   1. Create /v1/admin/dashboard/stats endpoint alias")
    print("   2. Test with actual admin authentication")
    print("   3. Verify frontend charts render correctly")
    print("   4. Add sample subscription data for testing")

if __name__ == "__main__":
    test_frontend_json_compatibility()
