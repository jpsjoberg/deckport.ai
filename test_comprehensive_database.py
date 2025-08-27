#!/usr/bin/env python3
"""
Comprehensive Database Testing Suite
Tests all models, relationships, and data integrity
"""

import sys
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import text, func, and_, or_
from sqlalchemy.exc import IntegrityError

# Add project root to path
sys.path.insert(0, '/home/jp/deckport.ai')

from shared.database.connection import engine, SessionLocal, create_tables
from shared.models.base import *
from shared.models.tournaments import *
from shared.models.shop import *
from shared.models.nfc_trading_system import *
from shared.models.player_moderation import *
from shared.models.communications import *

class DatabaseTestSuite:
    def __init__(self):
        self.session = None
        self.test_data = {}
        self.unique_id = str(uuid.uuid4())[:8]
        
    def setup(self):
        """Initialize database and session"""
        try:
            create_tables()
            self.session = SessionLocal()
            print("✅ Database setup complete")
            return True
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test session"""
        if self.session:
            self.session.close()
    
    def test_connection_and_basic_queries(self):
        """Test 1: Database connection and basic queries"""
        print("\n🔌 Test 1: Database Connection & Basic Queries")
        try:
            # Test connection
            result = self.session.execute(text("SELECT 1 as test")).scalar()
            assert result == 1, "Basic query failed"
            
            # Test table existence
            tables = self.session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name
            """)).fetchall()
            
            table_names = [t[0] for t in tables]
            required_tables = [
                'admins', 'players', 'consoles', 'card_catalog', 'nfc_cards',
                'player_cards', 'shop_orders', 'player_wallets', 'announcements',
                'email_campaigns', 'player_activity_logs'
            ]
            
            missing_tables = [t for t in required_tables if t not in table_names]
            if missing_tables:
                print(f"⚠️  Missing tables: {missing_tables}")
            
            print(f"✅ Found {len(table_names)} tables in database")
            print(f"✅ Required tables present: {len(required_tables) - len(missing_tables)}/{len(required_tables)}")
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def test_model_creation_and_relationships(self):
        """Test 2: Model creation and relationships"""
        print("\n🏗️  Test 2: Model Creation & Relationships")
        try:
            # Create admin
            admin = Admin(
                username=f"test_admin_{self.unique_id}",
                email=f"admin_{self.unique_id}@test.com",
                password_hash="test_hash_123",
                role="admin",
                is_active=True
            )
            self.session.add(admin)
            self.session.flush()
            self.test_data['admin'] = admin
            print(f"✅ Created Admin: {admin.username}")
            
            # Create player with all fields
            player = Player(
                email=f"player_{self.unique_id}@test.com",
                username=f"test_player_{self.unique_id}",
                display_name=f"Test Player {self.unique_id}",
                status="active",
                is_verified=True,
                is_premium=False,
                elo_rating=1200,
                last_login_ip="127.0.0.1",
                warning_count=0,
                is_banned=False
            )
            self.session.add(player)
            self.session.flush()
            self.test_data['player'] = player
            print(f"✅ Created Player: {player.username}")
            
            # Create console
            console = Console(
                device_uid=f"console_{self.unique_id}",
                status="active",
                location="Test Location"
            )
            self.session.add(console)
            self.session.flush()
            self.test_data['console'] = console
            print(f"✅ Created Console: {console.device_uid}")
            
            # Create card catalog
            card = CardCatalog(
                product_sku=f"CARD-{self.unique_id}",
                name=f"Test Card {self.unique_id}",
                rarity="RARE",
                category="CREATURE",
                description="Test card for comprehensive testing"
            )
            self.session.add(card)
            self.session.flush()
            self.test_data['card'] = card
            print(f"✅ Created Card: {card.name}")
            
            # Create NFC card
            nfc_card = NFCCard(
                uid=f"nfc_{self.unique_id}",
                card_id=card.id,
                status="active"
            )
            self.session.add(nfc_card)
            self.session.flush()
            self.test_data['nfc_card'] = nfc_card
            print(f"✅ Created NFC Card: {nfc_card.uid}")
            
            # Create player card
            player_card = PlayerCard(
                player_id=player.id,
                card_id=card.id,
                quantity=5
            )
            self.session.add(player_card)
            self.session.flush()
            print(f"✅ Created PlayerCard: {player.username} owns {player_card.quantity}x {card.name}")
            
            # Create wallet
            wallet = PlayerWallet(
                player_id=player.id,
                balance=Decimal('150.00')
            )
            self.session.add(wallet)
            self.session.flush()
            self.test_data['wallet'] = wallet
            print(f"✅ Created Wallet: ${wallet.balance}")
            
            # Create wallet transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                transaction_type="DEPOSIT",
                amount=Decimal('50.00'),
                description="Test deposit"
            )
            self.session.add(transaction)
            self.session.flush()
            print(f"✅ Created Transaction: {transaction.transaction_type} ${transaction.amount}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Model creation failed: {e}")
            self.session.rollback()
            return False
    
    def test_shop_and_commerce(self):
        """Test 3: Shop and commerce functionality"""
        print("\n🛒 Test 3: Shop & Commerce")
        try:
            player = self.test_data['player']
            
            # Create shop products
            product1 = ShopProduct(
                sku=f"SKU-{self.unique_id}-1",
                name=f"Test Product 1 {self.unique_id}",
                description="Test product for commerce testing",
                price=Decimal('29.99'),
                product_type="CARD_PACK",
                stock_quantity=100
            )
            
            product2 = ShopProduct(
                sku=f"SKU-{self.unique_id}-2",
                name=f"Test Product 2 {self.unique_id}",
                description="Another test product",
                price=Decimal('49.99'),
                product_type="ACCESSORY",
                stock_quantity=50
            )
            
            self.session.add_all([product1, product2])
            self.session.flush()
            print(f"✅ Created {2} shop products")
            
            # Create shop orders
            order1 = ShopOrder(
                order_number=f"ORDER-{self.unique_id}-001",
                player_id=player.id,
                subtotal=Decimal('29.99'),
                tax_amount=Decimal('2.40'),
                total_amount=Decimal('32.39'),
                payment_method="STRIPE",
                status="COMPLETED"
            )
            
            order2 = ShopOrder(
                order_number=f"ORDER-{self.unique_id}-002",
                player_id=player.id,
                subtotal=Decimal('49.99'),
                tax_amount=Decimal('4.00'),
                total_amount=Decimal('53.99'),
                payment_method="PAYPAL",
                status="PENDING"
            )
            
            self.session.add_all([order1, order2])
            self.session.flush()
            print(f"✅ Created {2} shop orders")
            
            # Create order items
            order_item1 = ShopOrderItem(
                order_id=order1.id,
                product_id=product1.id,
                quantity=1,
                unit_price=product1.price,
                total_price=product1.price
            )
            
            order_item2 = ShopOrderItem(
                order_id=order2.id,
                product_id=product2.id,
                quantity=1,
                unit_price=product2.price,
                total_price=product2.price
            )
            
            self.session.add_all([order_item1, order_item2])
            self.session.flush()
            print(f"✅ Created order items")
            
            # Test revenue calculation
            total_revenue = self.session.query(func.sum(ShopOrder.total_amount)).filter(
                ShopOrder.status == 'COMPLETED'
            ).scalar() or Decimal('0.00')
            
            print(f"✅ Total completed order revenue: ${total_revenue}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Shop test failed: {e}")
            self.session.rollback()
            return False
    
    def test_player_activity_and_moderation(self):
        """Test 4: Player activity and moderation"""
        print("\n👥 Test 4: Player Activity & Moderation")
        try:
            player = self.test_data['player']
            admin = self.test_data['admin']
            
            # Create activity logs
            activities = [
                PlayerActivityLog(
                    player_id=player.id,
                    activity_type="LOGIN",
                    description="Player logged in",
                    ip_address="127.0.0.1"
                ),
                PlayerActivityLog(
                    player_id=player.id,
                    activity_type="MATCH_START",
                    description="Started a match",
                    ip_address="127.0.0.1"
                ),
                PlayerActivityLog(
                    player_id=player.id,
                    activity_type="CARD_TRADE",
                    description="Traded a card",
                    ip_address="127.0.0.1"
                )
            ]
            
            self.session.add_all(activities)
            self.session.flush()
            print(f"✅ Created {len(activities)} activity logs")
            
            # Create player warning
            warning = PlayerWarning(
                player_id=player.id,
                admin_id=admin.id,
                reason="Test warning for inappropriate behavior",
                severity="MEDIUM",
                is_active=True
            )
            self.session.add(warning)
            self.session.flush()
            print(f"✅ Created player warning")
            
            # Create player report
            report = PlayerReport(
                reported_player_id=player.id,
                reporter_id=player.id,  # Self-report for testing
                reason="INAPPROPRIATE_BEHAVIOR",
                description="Test report for comprehensive testing",
                status="PENDING"
            )
            self.session.add(report)
            self.session.flush()
            print(f"✅ Created player report")
            
            # Test activity aggregation
            activity_counts = self.session.query(
                PlayerActivityLog.activity_type,
                func.count(PlayerActivityLog.id)
            ).filter(
                PlayerActivityLog.player_id == player.id
            ).group_by(PlayerActivityLog.activity_type).all()
            
            print("✅ Activity breakdown:")
            for activity_type, count in activity_counts:
                print(f"   - {activity_type}: {count}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Activity test failed: {e}")
            self.session.rollback()
            return False
    
    def test_communications_system(self):
        """Test 5: Communications system"""
        print("\n📢 Test 5: Communications System")
        try:
            admin = self.test_data['admin']
            
            # Create announcement
            announcement = Announcement(
                title=f"Test Announcement {self.unique_id}",
                message="This is a comprehensive test announcement",
                type="GENERAL",
                priority="HIGH",
                status="PUBLISHED",
                created_by_admin_id=admin.id,
                target_audience="ALL_PLAYERS",
                channels=["IN_GAME", "EMAIL"]
            )
            self.session.add(announcement)
            self.session.flush()
            print(f"✅ Created announcement: {announcement.title}")
            
            # Create email campaign
            campaign = EmailCampaign(
                name=f"Test Campaign {self.unique_id}",
                subject="Test Email Subject",
                content="Test email content for comprehensive testing",
                campaign_type="PROMOTIONAL",
                status="DRAFT",
                created_by_admin_id=admin.id,
                target_audience="ACTIVE_PLAYERS"
            )
            self.session.add(campaign)
            self.session.flush()
            print(f"✅ Created email campaign: {campaign.name}")
            
            # Create email logs
            email_log = EmailLog(
                campaign_id=campaign.id,
                recipient_email="test@example.com",
                status="SENT",
                sent_at=datetime.utcnow()
            )
            self.session.add(email_log)
            self.session.flush()
            print(f"✅ Created email log")
            
            # Create social media post
            social_post = SocialMediaPost(
                platform="DISCORD",
                content=f"Test Discord post {self.unique_id}",
                post_type="ANNOUNCEMENT",
                status="PUBLISHED",
                created_by_admin_id=admin.id
            )
            self.session.add(social_post)
            self.session.flush()
            print(f"✅ Created social media post")
            
            # Test communication metrics
            active_announcements = self.session.query(func.count(Announcement.id)).filter(
                Announcement.status == 'PUBLISHED'
            ).scalar()
            
            campaign_count = self.session.query(func.count(EmailCampaign.id)).scalar()
            
            print(f"✅ Active announcements: {active_announcements}")
            print(f"✅ Total email campaigns: {campaign_count}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Communications test failed: {e}")
            self.session.rollback()
            return False
    
    def test_complex_queries_and_analytics(self):
        """Test 6: Complex queries and analytics"""
        print("\n📊 Test 6: Complex Queries & Analytics")
        try:
            # Player statistics
            player_stats = self.session.query(
                func.count(Player.id).label('total_players'),
                func.count(Player.id).filter(Player.status == 'active').label('active_players'),
                func.count(Player.id).filter(Player.is_verified == True).label('verified_players'),
                func.avg(Player.elo_rating).label('avg_elo')
            ).first()
            
            print(f"✅ Player Statistics:")
            print(f"   - Total: {player_stats.total_players}")
            print(f"   - Active: {player_stats.active_players}")
            print(f"   - Verified: {player_stats.verified_players}")
            print(f"   - Avg ELO: {player_stats.avg_elo:.1f}" if player_stats.avg_elo else "   - Avg ELO: N/A")
            
            # Revenue analytics
            revenue_stats = self.session.query(
                func.count(ShopOrder.id).label('total_orders'),
                func.sum(ShopOrder.total_amount).filter(ShopOrder.status == 'COMPLETED').label('completed_revenue'),
                func.avg(ShopOrder.total_amount).label('avg_order_value')
            ).first()
            
            print(f"✅ Revenue Statistics:")
            print(f"   - Total Orders: {revenue_stats.total_orders}")
            print(f"   - Completed Revenue: ${revenue_stats.completed_revenue or 0}")
            print(f"   - Avg Order Value: ${revenue_stats.avg_order_value or 0}")
            
            # Card statistics
            card_stats = self.session.query(
                func.count(CardCatalog.id).label('total_cards'),
                func.sum(PlayerCard.quantity).label('total_owned'),
                func.count(func.distinct(PlayerCard.player_id)).label('players_with_cards')
            ).outerjoin(PlayerCard).first()
            
            print(f"✅ Card Statistics:")
            print(f"   - Total Card Types: {card_stats.total_cards}")
            print(f"   - Total Cards Owned: {card_stats.total_owned or 0}")
            print(f"   - Players with Cards: {card_stats.players_with_cards or 0}")
            
            # Activity analytics
            recent_activity = self.session.query(
                func.count(PlayerActivityLog.id)
            ).filter(
                PlayerActivityLog.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).scalar()
            
            print(f"✅ Activity Statistics:")
            print(f"   - Recent Activity (7 days): {recent_activity}")
            
            return True
            
        except Exception as e:
            print(f"❌ Analytics test failed: {e}")
            return False
    
    def test_data_integrity_and_constraints(self):
        """Test 7: Data integrity and constraints"""
        print("\n🔒 Test 7: Data Integrity & Constraints")
        try:
            # Test unique constraints
            try:
                duplicate_admin = Admin(
                    username=self.test_data['admin'].username,  # Duplicate username
                    email="different@email.com",
                    password_hash="hash",
                    role="admin"
                )
                self.session.add(duplicate_admin)
                self.session.commit()
                print("❌ Unique constraint test failed - duplicate allowed")
                return False
            except IntegrityError:
                self.session.rollback()
                print("✅ Username unique constraint working")
            
            # Test foreign key constraints
            try:
                invalid_player_card = PlayerCard(
                    player_id=99999,  # Non-existent player
                    card_id=self.test_data['card'].id,
                    quantity=1
                )
                self.session.add(invalid_player_card)
                self.session.commit()
                print("❌ Foreign key constraint test failed - invalid reference allowed")
                return False
            except IntegrityError:
                self.session.rollback()
                print("✅ Foreign key constraints working")
            
            # Test data validation
            player = self.test_data['player']
            original_elo = player.elo_rating
            
            # Update player stats
            player.elo_rating = 1500
            player.login_count = 10
            
            self.session.commit()
            self.session.refresh(player)
            
            assert player.elo_rating == 1500, "ELO update failed"
            assert player.login_count == 10, "Login count update failed"
            
            print("✅ Data validation and updates working")
            
            return True
            
        except Exception as e:
            print(f"❌ Integrity test failed: {e}")
            self.session.rollback()
            return False
    
    def run_all_tests(self):
        """Run all database tests"""
        print("🧪 COMPREHENSIVE DATABASE TEST SUITE")
        print("=" * 50)
        
        if not self.setup():
            return False
        
        tests = [
            self.test_connection_and_basic_queries,
            self.test_model_creation_and_relationships,
            self.test_shop_and_commerce,
            self.test_player_activity_and_moderation,
            self.test_communications_system,
            self.test_complex_queries_and_analytics,
            self.test_data_integrity_and_constraints
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
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL DATABASE TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False

if __name__ == "__main__":
    test_suite = DatabaseTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
