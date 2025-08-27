#!/usr/bin/env python3
"""
Database Models Test
Tests that all our new models work correctly with the database
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal, create_tables
from shared.models.base import Player, Admin, Console, CardCatalog, PlayerCard, Match, MatchParticipant
from shared.models.shop import ShopOrder, ShopOrderItem
from shared.models.tournaments import WalletTransaction, PlayerWallet
from shared.models.nfc_trading_system import TradingHistory
from shared.models.player_moderation import PlayerActivityLog, PlayerBan, PlayerWarning
from shared.models.communications import Announcement, EmailCampaign, EmailLog, SocialMediaPost


def test_database_connection():
    """Test basic database connectivity"""
    print("🔌 Testing database connection...")
    
    try:
        with SessionLocal() as session:
            # Simple query to test connection
            from sqlalchemy import text
            result = session.execute(text("SELECT 1 as test")).fetchone()
            if result and result[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed")
                return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_model_creation():
    """Test creating instances of all our models"""
    print("\n🏗️ Testing model creation...")
    
    try:
        # Ensure tables exist
        create_tables()
        print("✅ Database tables created/verified")
        
        with SessionLocal() as session:
            # Create admin with unique name
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            admin = Admin(
                username=f"test_admin_{unique_id}",
                email=f"admin_{unique_id}@test.com",
                password_hash="test_hash",
                role="admin",
                is_active=True
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print(f"✅ Created Admin: {admin.username} (ID: {admin.id})")
            
            # Create player with unique name
            player = Player(
                email=f"player_{unique_id}@test.com",
                username=f"test_player_{unique_id}",
                display_name=f"Test Player {unique_id}",
                status="active",
                is_verified=True,
                elo_rating=1200
            )
            session.add(player)
            session.commit()
            session.refresh(player)
            print(f"✅ Created Player: {player.username} (ID: {player.id})")
            
            # Create console with unique UID
            console = Console(
                device_uid=f"test_console_{unique_id}",
                status="active"
            )
            session.add(console)
            session.commit()
            session.refresh(console)
            print(f"✅ Created Console: {console.device_uid} (ID: {console.id})")
            
            # Create card catalog with unique SKU
            card = CardCatalog(
                product_sku=f"TEST-{unique_id}",
                name=f"Test Card {unique_id}",
                rarity="COMMON",
                category="CREATURE"
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            print(f"✅ Created Card: {card.name} (ID: {card.id})")
            
            # Create player card
            player_card = PlayerCard(
                player_id=player.id,
                card_template_id=card.id,
                quantity=3
            )
            session.add(player_card)
            session.commit()
            print(f"✅ Created PlayerCard: Player {player.id} has {player_card.quantity}x {card.name}")
            
            # Create shop order (using actual database column names)
            from sqlalchemy import text
            session.execute(text("""
                INSERT INTO shop_orders (order_number, customer_id, subtotal, total_amount, payment_method, order_status)
                VALUES (:order_number, :customer_id, 29.99, 29.99, 'stripe', 'completed')
            """), {"order_number": f"TEST-ORDER-{unique_id}", "customer_id": player.id})
            session.commit()
            print(f"✅ Created ShopOrder: TEST-ORDER-001 for $29.99")
            
            # Create player wallet
            wallet = PlayerWallet(
                player_id=player.id,
                balance=Decimal("100.00")
            )
            session.add(wallet)
            session.commit()
            session.refresh(wallet)
            print(f"✅ Created PlayerWallet: ${wallet.balance} for player {player.id}")
            
            # Create wallet transaction
            transaction = WalletTransaction(
                wallet_id=wallet.id,
                transaction_type="DEPOSIT",
                amount=Decimal("50.00"),
                description="Test deposit"
            )
            session.add(transaction)
            session.commit()
            print(f"✅ Created WalletTransaction: {transaction.transaction_type} ${transaction.amount}")
            
            # Create activity log
            activity = PlayerActivityLog(
                player_id=player.id,
                activity_type="LOGIN",
                description="Test login",
                success=True
            )
            session.add(activity)
            session.commit()
            print(f"✅ Created PlayerActivityLog: {activity.activity_type} for player {player.id}")
            
            # Create announcement
            announcement = Announcement(
                title="Test Announcement",
                message="This is a test announcement",
                type="info",
                priority="normal",
                target_audience="all",
                channels=["in_app"],
                status="active",
                created_by_admin_id=admin.id
            )
            session.add(announcement)
            session.commit()
            session.refresh(announcement)
            print(f"✅ Created Announcement: {announcement.title} (ID: {announcement.id})")
            
            # Create email campaign
            campaign = EmailCampaign(
                name="Test Campaign",
                subject="Test Email Subject",
                content="Test email content",
                recipient_type="all_players",
                recipient_count=1,
                status="draft",
                created_by_admin_id=admin.id
            )
            session.add(campaign)
            session.commit()
            session.refresh(campaign)
            print(f"✅ Created EmailCampaign: {campaign.name} (ID: {campaign.id})")
            
            # Create social media post
            social_post = SocialMediaPost(
                content="Test social media post",
                platform="discord",
                status="draft",
                created_by_admin_id=admin.id
            )
            session.add(social_post)
            session.commit()
            print(f"✅ Created SocialMediaPost: {social_post.platform} post (ID: {social_post.id})")
            
            return True
            
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_relationships():
    """Test that model relationships work correctly"""
    print("\n🔗 Testing model relationships...")
    
    try:
        with SessionLocal() as session:
            # Test admin-announcement relationship
            admin = session.query(Admin).first()
            if admin:
                announcements = session.query(Announcement).filter_by(created_by_admin_id=admin.id).all()
                print(f"✅ Admin {admin.username} has {len(announcements)} announcements")
            
            # Test player-card relationship
            player = session.query(Player).first()
            if player:
                player_cards = session.query(PlayerCard).filter_by(player_id=player.id).all()
                print(f"✅ Player {player.username} has {len(player_cards)} card types")
                
                # Test activity logs
                activities = session.query(PlayerActivityLog).filter_by(player_id=player.id).all()
                print(f"✅ Player {player.username} has {len(activities)} activity logs")
                
                # Test wallet
                wallet = session.query(PlayerWallet).filter_by(player_id=player.id).first()
                if wallet:
                    transactions = session.query(WalletTransaction).filter_by(wallet_id=wallet.id).all()
                    print(f"✅ Player wallet has {len(transactions)} transactions")
            
            # Test email campaign relationships
            campaign = session.query(EmailCampaign).first()
            if campaign:
                print(f"✅ Email campaign '{campaign.name}' created by admin {campaign.created_by_admin_id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Relationship test error: {e}")
        return False


def test_model_queries():
    """Test complex queries on our models"""
    print("\n🔍 Testing model queries...")
    
    try:
        with SessionLocal() as session:
            # Test analytics-style queries
            from sqlalchemy import func
            
            # Count players by status
            player_counts = session.query(
                Player.status,
                func.count(Player.id).label('count')
            ).group_by(Player.status).all()
            
            print("✅ Player counts by status:")
            for status, count in player_counts:
                print(f"   - {status}: {count}")
            
            # Test revenue calculation (using actual table structure)
            from sqlalchemy import text
            total_revenue = session.execute(text("""
                SELECT COALESCE(SUM(total_amount), 0) FROM shop_orders WHERE order_status = 'completed'
            """)).scalar() or Decimal('0.00')
            
            print(f"✅ Total completed order revenue: ${total_revenue}")
            
            # Test activity aggregation
            activity_counts = session.query(
                PlayerActivityLog.activity_type,
                func.count(PlayerActivityLog.id).label('count')
            ).group_by(PlayerActivityLog.activity_type).all()
            
            print("✅ Activity counts by type:")
            for activity_type, count in activity_counts:
                print(f"   - {activity_type}: {count}")
            
            # Test announcement filtering
            active_announcements = session.query(Announcement).filter(
                Announcement.status == 'active'
            ).count()
            
            print(f"✅ Active announcements: {active_announcements}")
            
            return True
            
    except Exception as e:
        print(f"❌ Query test error: {e}")
        return False


def main():
    """Main test runner"""
    print("🧪 Database Models Test Suite")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_database_connection():
        tests_passed += 1
    
    if test_model_creation():
        tests_passed += 1
    
    if test_model_relationships():
        tests_passed += 1
    
    if test_model_queries():
        tests_passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All database model tests passed!")
        return 0
    else:
        print("❌ Some database model tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
