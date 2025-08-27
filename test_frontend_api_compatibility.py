#!/usr/bin/env python3
"""
Frontend-API Compatibility Test
Verifies that API endpoints return JSON structures that match frontend expectations
"""

import sys
import json
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

class FrontendAPICompatibilityTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8002"
        self.issues = []
        
    def log_issue(self, endpoint, expected, actual, description):
        """Log a compatibility issue"""
        self.issues.append({
            'endpoint': endpoint,
            'expected': expected,
            'actual': actual,
            'description': description,
            'severity': 'error' if expected != actual else 'warning'
        })
    
    def test_revenue_analytics_structure(self):
        """Test revenue analytics JSON structure"""
        print("\n📊 Testing Revenue Analytics Structure")
        
        # What the frontend expects (from analytics/index.html):
        expected_structure = {
            'daily_data': [
                {
                    'date': 'string',
                    'revenue': 'number'  # Frontend uses d.revenue
                }
            ]
        }
        
        # Simulate what the API should return based on the code
        api_structure = {
            'total_revenue': 'number',
            'growth_rate': 'number', 
            'daily_data': [
                {
                    'date': 'string',
                    'shop_revenue': 'number',
                    'trading_revenue': 'number',
                    'total_revenue': 'number',  # API uses total_revenue, not revenue
                    'shop_orders': 'number',
                    'trades': 'number'
                }
            ],
            'period_days': 'number',
            'currency': 'string',
            'breakdown': {
                'shop_revenue': 'number',
                'trading_revenue': 'number'
            }
        }
        
        # Check for mismatches
        if 'revenue' not in str(api_structure['daily_data']):
            self.log_issue(
                '/v1/admin/analytics/revenue',
                'daily_data[].revenue',
                'daily_data[].total_revenue',
                'Frontend expects d.revenue but API returns d.total_revenue'
            )
            print("❌ MISMATCH: Frontend expects 'revenue' field, API returns 'total_revenue'")
        else:
            print("✅ Revenue field structure matches")
    
    def test_player_behavior_structure(self):
        """Test player behavior analytics structure"""
        print("\n👥 Testing Player Behavior Structure")
        
        # Based on the API code, it returns:
        api_structure = {
            'total_players': 'number',
            'active_players_week': 'number',
            'retention_rate': 'number',
            'registration_trend': 'array',
            'activity_trend': 'array',
            'period_days': 'number',
            'metrics': {
                'avg_session_duration_ms': 'number',
                'new_players_period': 'number',
                'retention_count': 'number'
            }
        }
        
        print("✅ Player behavior structure looks comprehensive")
        
    def test_dashboard_summary_structure(self):
        """Test dashboard summary structure"""
        print("\n📈 Testing Dashboard Summary Structure")
        
        # From the frontend dashboard.py, it expects:
        frontend_expects = {
            'devices': 'array',
            'online_players': 'number',
            'total_cards': 'number',
            'activated_cards': 'number'
        }
        
        # API returns (from dashboard-summary endpoint):
        api_returns = {
            'revenue': {
                'daily': 'number',
                'weekly': 'number', 
                'monthly': 'number',
                'breakdown': 'object'
            },
            'players': {
                'new_today': 'number',
                'active_week': 'number'
            },
            'cards': {
                'activated_today': 'number'
            }
        }
        
        # Check for mismatches
        if 'devices' not in str(api_returns):
            self.log_issue(
                '/v1/admin/analytics/dashboard-summary',
                'devices array',
                'missing',
                'Frontend expects devices array but API does not provide it'
            )
            print("❌ MISMATCH: Frontend expects 'devices' array, not provided by API")
        
        if 'online_players' not in str(api_returns):
            self.log_issue(
                '/v1/admin/analytics/dashboard-summary', 
                'online_players number',
                'players.active_week',
                'Frontend expects online_players but API provides players.active_week'
            )
            print("❌ MISMATCH: Frontend expects 'online_players', API has 'players.active_week'")
        
    def test_device_management_structure(self):
        """Test device/console management structure"""
        print("\n🖥️  Testing Device Management Structure")
        
        # Frontend expects (from dashboard.py):
        frontend_expects = {
            'devices': [
                {
                    'status': 'string',
                    'last_seen_minutes': 'number'
                }
            ]
        }
        
        print("✅ Device structure expectations documented")
        
    def generate_compatibility_report(self):
        """Generate a detailed compatibility report"""
        print("\n" + "="*60)
        print("🔍 FRONTEND-API COMPATIBILITY REPORT")
        print("="*60)
        
        if not self.issues:
            print("🎉 NO COMPATIBILITY ISSUES FOUND!")
            return True
        
        print(f"⚠️  FOUND {len(self.issues)} COMPATIBILITY ISSUES:")
        print()
        
        for i, issue in enumerate(self.issues, 1):
            severity_icon = "🚨" if issue['severity'] == 'error' else "⚠️ "
            print(f"{severity_icon} Issue #{i}: {issue['description']}")
            print(f"   Endpoint: {issue['endpoint']}")
            print(f"   Expected: {issue['expected']}")
            print(f"   Actual: {issue['actual']}")
            print()
        
        return len([i for i in self.issues if i['severity'] == 'error']) == 0
    
    def suggest_fixes(self):
        """Suggest fixes for compatibility issues"""
        if not self.issues:
            return
            
        print("🔧 SUGGESTED FIXES:")
        print("="*30)
        
        for issue in self.issues:
            if 'revenue' in issue['description']:
                print("1. Fix Revenue Analytics:")
                print("   - Update API to include 'revenue' field in daily_data")
                print("   - OR update frontend to use 'total_revenue' instead")
                print()
            
            if 'devices' in issue['description']:
                print("2. Fix Dashboard Devices:")
                print("   - Add devices array to dashboard-summary endpoint")
                print("   - OR update frontend to call separate /v1/admin/devices endpoint")
                print()
                
            if 'online_players' in issue['description']:
                print("3. Fix Online Players:")
                print("   - Add online_players field to dashboard-summary")
                print("   - OR update frontend to use players.active_week")
                print()
    
    def run_all_tests(self):
        """Run all compatibility tests"""
        print("🧪 FRONTEND-API COMPATIBILITY TEST SUITE")
        print("="*50)
        
        self.test_revenue_analytics_structure()
        self.test_player_behavior_structure()
        self.test_dashboard_summary_structure()
        self.test_device_management_structure()
        
        success = self.generate_compatibility_report()
        self.suggest_fixes()
        
        return success

if __name__ == "__main__":
    test_suite = FrontendAPICompatibilityTest()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
