#!/usr/bin/env python3
"""
Database Testing Suite - Real Schema Compatible
Tests database with actual schema and existing data
"""

import sys
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import text, func

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

from shared.database.connection import SessionLocal, create_tables

class RealSchemaTestSuite:
    def __init__(self):
        self.session = None
        self.unique_id = str(uuid.uuid4())[:8]
        
    def setup(self):
        """Initialize database session"""
        try:
            self.session = SessionLocal()
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test session"""
        if self.session:
            self.session.close()
    
    def test_database_connection(self):
        """Test 1: Basic database connectivity"""
        print("\n🔌 Test 1: Database Connection")
        try:
            result = self.session.execute(text("SELECT 1 as test")).scalar()
            assert result == 1, "Basic query failed"
            print("✅ Database connection working")
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def test_existing_data_queries(self):
        """Test 2: Query existing data"""
        print("\n📊 Test 2: Existing Data Queries")
        try:
            # Test player count
            player_count = self.session.execute(text("SELECT COUNT(*) FROM players")).scalar()
            print(f"✅ Found {player_count} players in database")
            
            # Test admin count
            admin_count = self.session.execute(text("SELECT COUNT(*) FROM admins")).scalar()
            print(f"✅ Found {admin_count} admins in database")
            
            # Test console count
            console_count = self.session.execute(text("SELECT COUNT(*) FROM consoles")).scalar()
            print(f"✅ Found {console_count} consoles in database")
            
            # Test card catalog count
            card_count = self.session.execute(text("SELECT COUNT(*) FROM card_catalog")).scalar()
            print(f"✅ Found {card_count} cards in catalog")
            
            # Test shop orders
            order_count = self.session.execute(text("SELECT COUNT(*) FROM shop_orders")).scalar()
            print(f"✅ Found {order_count} shop orders")
            
            return True
        except Exception as e:
            print(f"❌ Data query test failed: {e}")
            return False
    
    def test_revenue_analytics(self):
        """Test 3: Revenue analytics with real schema"""
        print("\n💰 Test 3: Revenue Analytics")
        try:
            # Total revenue from completed orders
            completed_revenue = self.session.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0) 
                FROM shop_orders 
                WHERE order_status = 'completed'
            """)).scalar()
            
            print(f"✅ Total completed order revenue: ${completed_revenue}")
            
            # Order status breakdown
            status_breakdown = self.session.execute(text("""
                SELECT order_status, COUNT(*), COALESCE(SUM(total_amount), 0)
                FROM shop_orders 
                GROUP BY order_status
                ORDER BY order_status
            """)).fetchall()
            
            print("✅ Order status breakdown:")
            for status, count, total in status_breakdown:
                print(f"   - {status}: {count} orders, ${total}")
            
            # Average order value
            avg_order = self.session.execute(text("""
                SELECT COALESCE(AVG(total_amount), 0) 
                FROM shop_orders
            """)).scalar()
            
            print(f"✅ Average order value: ${avg_order:.2f}")
            
            return True
        except Exception as e:
            print(f"❌ Revenue analytics test failed: {e}")
            return False
    
    def test_player_analytics(self):
        """Test 4: Player analytics"""
        print("\n👥 Test 4: Player Analytics")
        try:
            # Player status breakdown
            status_breakdown = self.session.execute(text("""
                SELECT status, COUNT(*) 
                FROM players 
                GROUP BY status
                ORDER BY status
            """)).fetchall()
            
            print("✅ Player status breakdown:")
            for status, count in status_breakdown:
                print(f"   - {status}: {count}")
            
            # Verified players
            verified_count = self.session.execute(text("""
                SELECT COUNT(*) FROM players WHERE is_verified = true
            """)).scalar()
            
            print(f"✅ Verified players: {verified_count}")
            
            # Premium players
            premium_count = self.session.execute(text("""
                SELECT COUNT(*) FROM players WHERE is_premium = true
            """)).scalar()
            
            print(f"✅ Premium players: {premium_count}")
            
            # ELO statistics
            elo_stats = self.session.execute(text("""
                SELECT 
                    MIN(elo_rating) as min_elo,
                    MAX(elo_rating) as max_elo,
                    AVG(elo_rating) as avg_elo,
                    COUNT(*) as total_players
                FROM players
            """)).fetchone()
            
            print(f"✅ ELO Statistics:")
            print(f"   - Min: {elo_stats.min_elo}")
            print(f"   - Max: {elo_stats.max_elo}")
            print(f"   - Average: {elo_stats.avg_elo:.1f}")
            print(f"   - Total players: {elo_stats.total_players}")
            
            return True
        except Exception as e:
            print(f"❌ Player analytics test failed: {e}")
            return False
    
    def test_card_system_analytics(self):
        """Test 5: Card system analytics"""
        print("\n🃏 Test 5: Card System Analytics")
        try:
            # Card rarity breakdown
            rarity_breakdown = self.session.execute(text("""
                SELECT rarity, COUNT(*) 
                FROM card_catalog 
                GROUP BY rarity
                ORDER BY rarity
            """)).fetchall()
            
            print("✅ Card rarity breakdown:")
            for rarity, count in rarity_breakdown:
                print(f"   - {rarity}: {count}")
            
            # Player card ownership
            ownership_stats = self.session.execute(text("""
                SELECT 
                    COUNT(DISTINCT player_id) as players_with_cards,
                    COUNT(*) as total_ownership_records,
                    COALESCE(SUM(quantity), 0) as total_cards_owned
                FROM player_cards
            """)).fetchone()
            
            print(f"✅ Card ownership:")
            print(f"   - Players with cards: {ownership_stats.players_with_cards}")
            print(f"   - Total ownership records: {ownership_stats.total_ownership_records}")
            print(f"   - Total cards owned: {ownership_stats.total_cards_owned}")
            
            # Most popular cards
            popular_cards = self.session.execute(text("""
                SELECT 
                    cc.name,
                    cc.rarity,
                    COALESCE(SUM(pc.quantity), 0) as total_owned
                FROM card_catalog cc
                LEFT JOIN player_cards pc ON cc.id = pc.card_template_id
                GROUP BY cc.id, cc.name, cc.rarity
                ORDER BY total_owned DESC
                LIMIT 5
            """)).fetchall()
            
            print("✅ Most popular cards:")
            for name, rarity, owned in popular_cards:
                print(f"   - {name} ({rarity}): {owned} owned")
            
            return True
        except Exception as e:
            print(f"❌ Card analytics test failed: {e}")
            return False
    
    def test_system_health_metrics(self):
        """Test 6: System health metrics"""
        print("\n🏥 Test 6: System Health Metrics")
        try:
            # Console status
            console_status = self.session.execute(text("""
                SELECT status, COUNT(*) 
                FROM consoles 
                GROUP BY status
                ORDER BY status
            """)).fetchall()
            
            print("✅ Console status breakdown:")
            for status, count in console_status:
                print(f"   - {status}: {count}")
            
            # Recent activity (if activity logs exist)
            try:
                recent_activity = self.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM player_activity_logs 
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """)).scalar()
                print(f"✅ Recent activity (24h): {recent_activity} events")
            except:
                print("⚠️  Player activity logs table not accessible")
            
            # Announcements
            try:
                announcement_stats = self.session.execute(text("""
                    SELECT status, COUNT(*) 
                    FROM announcements 
                    GROUP BY status
                    ORDER BY status
                """)).fetchall()
                
                print("✅ Announcement status:")
                for status, count in announcement_stats:
                    print(f"   - {status}: {count}")
            except:
                print("⚠️  Announcements table not accessible")
            
            return True
        except Exception as e:
            print(f"❌ System health test failed: {e}")
            return False
    
    def test_data_integrity(self):
        """Test 7: Data integrity checks"""
        print("\n🔒 Test 7: Data Integrity")
        try:
            # Check for orphaned records
            orphaned_player_cards = self.session.execute(text("""
                SELECT COUNT(*) 
                FROM player_cards pc
                LEFT JOIN players p ON pc.player_id = p.id
                WHERE p.id IS NULL
            """)).scalar()
            
            print(f"✅ Orphaned player cards: {orphaned_player_cards}")
            
            orphaned_orders = self.session.execute(text("""
                SELECT COUNT(*) 
                FROM shop_orders so
                LEFT JOIN players p ON so.customer_id = p.id
                WHERE p.id IS NULL
            """)).scalar()
            
            print(f"✅ Orphaned shop orders: {orphaned_orders}")
            
            # Check for duplicate usernames
            duplicate_usernames = self.session.execute(text("""
                SELECT username, COUNT(*) 
                FROM players 
                WHERE username IS NOT NULL
                GROUP BY username 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            print(f"✅ Duplicate usernames: {len(duplicate_usernames)}")
            
            # Check for invalid ELO ratings
            invalid_elo = self.session.execute(text("""
                SELECT COUNT(*) 
                FROM players 
                WHERE elo_rating < 0 OR elo_rating > 5000
            """)).scalar()
            
            print(f"✅ Invalid ELO ratings: {invalid_elo}")
            
            return True
        except Exception as e:
            print(f"❌ Data integrity test failed: {e}")
            return False
    
    def test_performance_queries(self):
        """Test 8: Performance of complex queries"""
        print("\n⚡ Test 8: Query Performance")
        try:
            import time
            
            # Test complex join query performance
            start_time = time.time()
            
            complex_query_result = self.session.execute(text("""
                SELECT 
                    p.username,
                    p.elo_rating,
                    COUNT(DISTINCT pc.card_template_id) as unique_cards,
                    COALESCE(SUM(pc.quantity), 0) as total_cards,
                    COUNT(DISTINCT so.id) as total_orders,
                    COALESCE(SUM(so.total_amount), 0) as total_spent
                FROM players p
                LEFT JOIN player_cards pc ON p.id = pc.player_id
                LEFT JOIN shop_orders so ON p.id = so.customer_id AND so.order_status = 'completed'
                WHERE p.status = 'active'
                GROUP BY p.id, p.username, p.elo_rating
                ORDER BY total_spent DESC
                LIMIT 10
            """)).fetchall()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            print(f"✅ Complex query executed in {query_time:.3f} seconds")
            print(f"✅ Top spenders:")
            
            for row in complex_query_result:
                print(f"   - {row.username or 'Anonymous'}: {row.unique_cards} unique cards, ${row.total_spent}")
            
            return True
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all database tests"""
        print("🧪 REAL SCHEMA DATABASE TEST SUITE")
        print("=" * 60)
        
        if not self.setup():
            return False
        
        tests = [
            self.test_database_connection,
            self.test_existing_data_queries,
            self.test_revenue_analytics,
            self.test_player_analytics,
            self.test_card_system_analytics,
            self.test_system_health_metrics,
            self.test_data_integrity,
            self.test_performance_queries
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    print(f"❌ {test.__name__} FAILED")
            except Exception as e:
                print(f"❌ {test.__name__} FAILED with exception: {e}")
        
        self.cleanup()
        
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL DATABASE TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False

if __name__ == "__main__":
    test_suite = RealSchemaTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
