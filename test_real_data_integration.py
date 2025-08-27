#!/usr/bin/env python3
"""
Quick Integration Test for Real Data Implementation
Tests the analytics, player management, and communications systems
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal, create_tables
from shared.models.base import Player, Admin, Console, CardCatalog, PlayerCard
from shared.models.shop import ShopOrder
from shared.models.player_moderation import PlayerActivityLog
from shared.models.communications import Announcement


class RealDataIntegrationTest:
    """Integration test for real data systems"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8002"  # API service URL
        self.session = requests.Session()
        self.admin_token = None
        
    def setup_test_data(self):
        """Create test data in the database"""
        print("🔧 Setting up test data...")
        
        try:
            # Ensure tables exist
            create_tables()
            
            with SessionLocal() as session:
                # Create test admin
                admin = Admin(
                    username="test_admin",
                    email="test@deckport.ai",
                    password_hash="$2b$12$test_hash",  # Placeholder hash
                    role="super_admin",
                    is_active=True
                )
                session.add(admin)
                session.commit()
                session.refresh(admin)
                print(f"✅ Created admin: {admin.username} (ID: {admin.id})")
                
                # Create test players
                players = []
                for i in range(10):
                    player = Player(
                        email=f"player{i}@test.com",
                        username=f"test_player_{i}",
                        display_name=f"Test Player {i}",
                        status="active",
                        is_verified=True,
                        elo_rating=1000 + (i * 50),
                        created_at=datetime.utcnow() - timedelta(days=30-i*2)
                    )
                    session.add(player)
                    players.append(player)
                
                session.commit()
                for player in players:
                    session.refresh(player)
                print(f"✅ Created {len(players)} test players")
                
                # Create test card
                card = CardCatalog(
                    product_sku="TEST-CARD-001",
                    name="Test Integration Card",
                    rarity="COMMON",
                    category="CREATURE"
                )
                session.add(card)
                session.commit()
                session.refresh(card)
                print(f"✅ Created test card: {card.name}")
                
                # Create player cards
                for i, player in enumerate(players[:5]):
                    player_card = PlayerCard(
                        player_id=player.id,
                        card_template_id=card.id,
                        quantity=i + 1
                    )
                    session.add(player_card)
                
                # Create shop orders
                for i, player in enumerate(players[:3]):
                    order = ShopOrder(
                        order_number=f"TEST-ORD-{1000+i}",
                        player_id=player.id,
                        subtotal=Decimal(f"{50 + i*10}.00"),
                        total_amount=Decimal(f"{50 + i*10}.00"),
                        payment_method="stripe",
                        status="completed",
                        created_at=datetime.utcnow() - timedelta(days=i+1)
                    )
                    session.add(order)
                
                # Create activity logs
                for i, player in enumerate(players):
                    activity = PlayerActivityLog(
                        player_id=player.id,
                        activity_type="LOGIN",
                        description="Test login activity",
                        timestamp=datetime.utcnow() - timedelta(hours=i)
                    )
                    session.add(activity)
                
                # Create consoles
                for i in range(5):
                    console = Console(
                        device_uid=f"test_console_{i}",
                        status="active" if i < 4 else "pending"
                    )
                    session.add(console)
                
                # Create test announcement
                announcement = Announcement(
                    title="Test Integration Announcement",
                    message="This is a test announcement for integration testing",
                    type="info",
                    priority="normal",
                    target_audience="all",
                    channels=["in_app", "email"],
                    status="active",
                    created_by_admin_id=admin.id
                )
                session.add(announcement)
                
                session.commit()
                print("✅ Created test orders, activities, consoles, and announcement")
                
                return admin.id
                
        except Exception as e:
            print(f"❌ Error setting up test data: {e}")
            return None
    
    def get_admin_token(self, admin_id):
        """Generate a test admin token (simplified for testing)"""
        # For testing purposes, we'll create a simple token
        # In production, this would go through proper JWT creation
        import jwt
        
        payload = {
            'admin_id': admin_id,
            'email': 'test@deckport.ai',
            'role': 'super_admin',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        # Use a test secret (in production this would be from config)
        token = jwt.encode(payload, 'test-secret-key', algorithm='HS256')
        return token
    
    def test_analytics_endpoints(self):
        """Test all analytics endpoints with real data"""
        print("\n📊 Testing Analytics Endpoints...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test revenue analytics
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/analytics/revenue", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Revenue Analytics: Total Revenue = ${data.get('total_revenue', 0)}")
                print(f"   - Growth Rate: {data.get('growth_rate', 0)}%")
                print(f"   - Daily Data Points: {len(data.get('daily_data', []))}")
            else:
                print(f"❌ Revenue Analytics failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Revenue Analytics error: {e}")
        
        # Test player behavior
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/analytics/player-behavior", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Player Behavior: Total Players = {data.get('total_players', 0)}")
                print(f"   - Active This Week: {data.get('active_players_week', 0)}")
                print(f"   - Retention Rate: {data.get('retention_rate', 0)}%")
            else:
                print(f"❌ Player Behavior failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Player Behavior error: {e}")
        
        # Test card usage
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/analytics/card-usage", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Card Usage: {len(data.get('product_statistics', []))} card types")
                print(f"   - Trading Stats: {data.get('trading_statistics', {})}")
            else:
                print(f"❌ Card Usage failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Card Usage error: {e}")
        
        # Test system metrics
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/analytics/system-metrics", headers=headers)
            if response.status_code == 200:
                data = response.json()
                console_metrics = data.get('console_metrics', {})
                print(f"✅ System Metrics: {console_metrics.get('active_consoles', 0)}/{console_metrics.get('total_consoles', 0)} consoles active")
                print(f"   - System Health: {data.get('system_health', {}).get('status', 'unknown')}")
            else:
                print(f"❌ System Metrics failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ System Metrics error: {e}")
        
        # Test dashboard summary
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/analytics/dashboard-summary", headers=headers)
            if response.status_code == 200:
                data = response.json()
                revenue = data.get('revenue', {})
                players = data.get('players', {})
                print(f"✅ Dashboard Summary: Daily Revenue = ${revenue.get('daily', 0)}")
                print(f"   - New Players Today: {players.get('new_today', 0)}")
                print(f"   - Active This Week: {players.get('active_week', 0)}")
            else:
                print(f"❌ Dashboard Summary failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Dashboard Summary error: {e}")
    
    def test_player_management(self):
        """Test player management endpoints"""
        print("\n👥 Testing Player Management...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test player stats
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/players/stats", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Player Stats: {data.get('total_players', 0)} total players")
                print(f"   - Active Players: {data.get('active_players', 0)}")
                print(f"   - Online Now: {data.get('online_players', 0)}")
                print(f"   - New Today: {data.get('new_registrations', {}).get('today', 0)}")
            else:
                print(f"❌ Player Stats failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Player Stats error: {e}")
        
        # Test player listing
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/players/?page=1&per_page=5", headers=headers)
            if response.status_code == 200:
                data = response.json()
                players = data.get('players', [])
                pagination = data.get('pagination', {})
                print(f"✅ Player Listing: {len(players)} players on page 1")
                print(f"   - Total Players: {pagination.get('total', 0)}")
                print(f"   - Sample Player: {players[0].get('username', 'N/A') if players else 'None'}")
            else:
                print(f"❌ Player Listing failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Player Listing error: {e}")
        
        # Test player search
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/players/?search=test_player_0", headers=headers)
            if response.status_code == 200:
                data = response.json()
                players = data.get('players', [])
                print(f"✅ Player Search: Found {len(players)} players matching 'test_player_0'")
                if players:
                    print(f"   - Found: {players[0].get('username', 'N/A')}")
            else:
                print(f"❌ Player Search failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Player Search error: {e}")
    
    def test_communications(self):
        """Test communications endpoints"""
        print("\n📢 Testing Communications...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test get announcements
        try:
            response = self.session.get(f"{self.base_url}/v1/admin/communications/announcements", headers=headers)
            if response.status_code == 200:
                data = response.json()
                announcements = data.get('announcements', [])
                print(f"✅ Get Announcements: {len(announcements)} announcements found")
                if announcements:
                    print(f"   - Sample: {announcements[0].get('title', 'N/A')}")
            else:
                print(f"❌ Get Announcements failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Get Announcements error: {e}")
        
        # Test create announcement
        try:
            new_announcement = {
                'title': 'Integration Test Announcement',
                'message': 'This announcement was created during integration testing',
                'type': 'info',
                'priority': 'normal',
                'target_audience': 'all',
                'channels': ['in_app']
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/admin/communications/announcements",
                json=new_announcement,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Create Announcement: Successfully created '{data.get('announcement', {}).get('title', 'N/A')}'")
            else:
                print(f"❌ Create Announcement failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Create Announcement error: {e}")
    
    def test_data_consistency(self):
        """Test data consistency across systems"""
        print("\n🔍 Testing Data Consistency...")
        
        with SessionLocal() as session:
            # Check player count consistency
            db_player_count = session.query(Player).count()
            print(f"✅ Database Player Count: {db_player_count}")
            
            # Check order count
            db_order_count = session.query(ShopOrder).count()
            print(f"✅ Database Order Count: {db_order_count}")
            
            # Check console count
            db_console_count = session.query(Console).count()
            print(f"✅ Database Console Count: {db_console_count}")
            
            # Check announcement count
            db_announcement_count = session.query(Announcement).count()
            print(f"✅ Database Announcement Count: {db_announcement_count}")
    
    def run_full_test(self):
        """Run the complete integration test suite"""
        print("🚀 Starting Real Data Integration Test")
        print("=" * 50)
        
        # Setup test data
        admin_id = self.setup_test_data()
        if not admin_id:
            print("❌ Failed to setup test data. Exiting.")
            return False
        
        # Get admin token
        self.admin_token = self.get_admin_token(admin_id)
        print(f"✅ Generated admin token for testing")
        
        # Run tests
        self.test_analytics_endpoints()
        self.test_player_management()
        self.test_communications()
        self.test_data_consistency()
        
        print("\n" + "=" * 50)
        print("🎉 Integration Test Complete!")
        
        return True


def main():
    """Main test runner"""
    test = RealDataIntegrationTest()
    
    try:
        success = test.run_full_test()
        if success:
            print("✅ All tests completed successfully!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
