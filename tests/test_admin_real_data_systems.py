"""
Comprehensive Tests for Real Database Implementation
Tests analytics, player management, and communications systems with actual data
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

# Test framework setup
import sys
import os
sys.path.append('/home/jp/deckport.ai')

from flask import Flask
from shared.database.connection import SessionLocal, engine
from shared.models.base import Base, Player, Admin, Console, Match, MatchParticipant, CardCatalog, NFCCard, PlayerCard
from shared.models.tournaments import WalletTransaction, PlayerWallet
from shared.models.shop import ShopOrder, ShopOrderItem
from shared.models.nfc_trading_system import TradingHistory
from shared.models.player_moderation import PlayerActivityLog, PlayerBan, PlayerWarning
from shared.models.communications import Announcement, EmailCampaign, EmailLog

# Import the routes we're testing
from services.api.routes.admin_analytics import admin_analytics_bp
from services.api.routes.admin_players import admin_players_bp
from services.api.routes.admin_communications import admin_communications_bp


class TestConfig:
    """Test configuration"""
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"  # In-memory database for testing
    SECRET_KEY = "test-secret-key"


@pytest.fixture(scope="function")
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    
    # Register blueprints
    app.register_blueprint(admin_analytics_bp)
    app.register_blueprint(admin_players_bp)
    app.register_blueprint(admin_communications_bp)
    
    return app


@pytest.fixture(scope="function")
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_admin(db_session):
    """Create a sample admin for testing"""
    admin = Admin(
        username="test_admin",
        email="admin@test.com",
        password_hash="hashed_password",
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def sample_players(db_session):
    """Create sample players for testing"""
    players = []
    for i in range(5):
        player = Player(
            email=f"player{i}@test.com",
            username=f"player_{i}",
            display_name=f"Player {i}",
            status="active",
            is_verified=True,
            elo_rating=1000 + (i * 100),
            created_at=datetime.utcnow() - timedelta(days=30-i*5)
        )
        db_session.add(player)
        players.append(player)
    
    db_session.commit()
    for player in players:
        db_session.refresh(player)
    return players


@pytest.fixture
def sample_data(db_session, sample_admin, sample_players):
    """Create comprehensive sample data for testing"""
    
    # Create card catalog
    card = CardCatalog(
        product_sku="TEST-001",
        name="Test Card",
        rarity="COMMON",
        category="CREATURE"
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    
    # Create shop orders
    for i, player in enumerate(sample_players[:3]):
        order = ShopOrder(
            order_number=f"ORD-{1000+i}",
            player_id=player.id,
            subtotal=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            payment_method="stripe",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=i+1)
        )
        db_session.add(order)
    
    # Create player cards
    for i, player in enumerate(sample_players):
        player_card = PlayerCard(
            player_id=player.id,
            card_template_id=card.id,
            quantity=i+1
        )
        db_session.add(player_card)
    
    # Create activity logs
    for i, player in enumerate(sample_players):
        activity = PlayerActivityLog(
            player_id=player.id,
            activity_type="LOGIN",
            description="User logged in",
            timestamp=datetime.utcnow() - timedelta(hours=i)
        )
        db_session.add(activity)
    
    # Create consoles
    for i in range(3):
        console = Console(
            device_uid=f"console_{i}",
            status="active" if i < 2 else "pending"
        )
        db_session.add(console)
    
    # Create announcements
    announcement = Announcement(
        title="Test Announcement",
        message="This is a test announcement",
        type="info",
        priority="normal",
        target_audience="all",
        channels=["in_app", "email"],
        status="active",
        created_by_admin_id=sample_admin.id
    )
    db_session.add(announcement)
    
    db_session.commit()
    
    return {
        'admin': sample_admin,
        'players': sample_players,
        'card': card,
        'announcement': announcement
    }


def mock_admin_auth(admin_id=1, admin_email="admin@test.com"):
    """Mock admin authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            with patch('flask.g') as mock_g:
                mock_g.admin_id = admin_id
                mock_g.admin_email = admin_email
                mock_g.is_admin = True
                return f(*args, **kwargs)
        return wrapper
    return decorator


class TestAnalyticsSystem:
    """Test the analytics system with real data"""
    
    @mock_admin_auth()
    def test_revenue_analytics_real_data(self, client, sample_data):
        """Test revenue analytics with real shop order data"""
        response = client.get('/v1/admin/analytics/revenue?days=30')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have real revenue data
        assert 'total_revenue' in data
        assert 'growth_rate' in data
        assert 'daily_data' in data
        assert 'breakdown' in data
        
        # Should have shop and trading revenue breakdown
        assert 'shop_revenue' in data['breakdown']
        assert 'trading_revenue' in data['breakdown']
        
        # Should have actual revenue from our test orders
        assert data['total_revenue'] > 0  # We created orders with real amounts
    
    @mock_admin_auth()
    def test_player_behavior_analytics(self, client, sample_data):
        """Test player behavior analytics with real data"""
        response = client.get('/v1/admin/analytics/player-behavior?days=30')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have real player data
        assert 'total_players' in data
        assert 'active_players_week' in data
        assert 'retention_rate' in data
        assert 'registration_trend' in data
        assert 'activity_trend' in data
        
        # Should reflect our test data
        assert data['total_players'] == 5  # We created 5 players
        assert len(data['registration_trend']) == 30  # 30 days of data
        assert len(data['activity_trend']) == 30
    
    @mock_admin_auth()
    def test_card_usage_analytics(self, client, sample_data):
        """Test card usage analytics with real data"""
        response = client.get('/v1/admin/analytics/card-usage')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have card statistics
        assert 'product_statistics' in data
        assert 'popular_products' in data
        assert 'trading_statistics' in data
        
        # Should have our test card
        assert len(data['product_statistics']) >= 1
        test_card = next((card for card in data['product_statistics'] if card['product_sku'] == 'TEST-001'), None)
        assert test_card is not None
        assert test_card['name'] == 'Test Card'
    
    @mock_admin_auth()
    def test_system_metrics(self, client, sample_data):
        """Test system metrics with real data"""
        response = client.get('/v1/admin/analytics/system-metrics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have system metrics
        assert 'console_metrics' in data
        assert 'system_health' in data
        
        # Should reflect our test consoles
        assert data['console_metrics']['total_consoles'] == 3
        assert data['console_metrics']['active_consoles'] == 2
        assert data['console_metrics']['uptime_percentage'] > 0
    
    @mock_admin_auth()
    def test_dashboard_summary(self, client, sample_data):
        """Test dashboard summary with real data"""
        response = client.get('/v1/admin/analytics/dashboard-summary')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have comprehensive summary
        assert 'revenue' in data
        assert 'players' in data
        assert 'cards' in data
        assert 'system' in data
        assert 'timestamp' in data
        
        # Revenue should have breakdown
        assert 'breakdown' in data['revenue']
        assert 'shop_daily' in data['revenue']['breakdown']


class TestPlayerManagementSystem:
    """Test the player management system with real data"""
    
    @mock_admin_auth()
    def test_get_players_list(self, client, sample_data):
        """Test getting paginated player list"""
        response = client.get('/v1/admin/players/?page=1&per_page=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have players and pagination
        assert 'players' in data
        assert 'pagination' in data
        assert 'filters' in data
        
        # Should have our test players
        assert len(data['players']) == 5
        assert data['pagination']['total'] == 5
        
        # Check player data structure
        player = data['players'][0]
        assert 'id' in player
        assert 'username' in player
        assert 'email' in player
        assert 'status' in player
        assert 'card_count' in player
        assert 'trade_count' in player
    
    @mock_admin_auth()
    def test_player_search(self, client, sample_data):
        """Test player search functionality"""
        response = client.get('/v1/admin/players/?search=player_0')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should find the specific player
        assert len(data['players']) == 1
        assert data['players'][0]['username'] == 'player_0'
    
    @mock_admin_auth()
    def test_player_stats(self, client, sample_data):
        """Test player statistics endpoint"""
        response = client.get('/v1/admin/players/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have comprehensive stats
        assert 'total_players' in data
        assert 'active_players' in data
        assert 'new_registrations' in data
        assert 'engagement_metrics' in data
        
        # Should reflect our test data
        assert data['total_players'] == 5
        assert 'today' in data['new_registrations']
        assert 'this_week' in data['new_registrations']
        assert 'this_month' in data['new_registrations']
    
    @mock_admin_auth()
    def test_player_filtering(self, client, sample_data):
        """Test player filtering by status"""
        response = client.get('/v1/admin/players/?status=active')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should only return active players
        assert len(data['players']) == 5  # All our test players are active
        for player in data['players']:
            assert player['status'] == 'active'


class TestCommunicationsSystem:
    """Test the communications system with real data"""
    
    @mock_admin_auth()
    def test_get_announcements(self, client, sample_data):
        """Test getting announcements list"""
        response = client.get('/v1/admin/communications/announcements')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have announcements and pagination
        assert 'announcements' in data
        assert 'pagination' in data
        
        # Should have our test announcement
        assert len(data['announcements']) == 1
        announcement = data['announcements'][0]
        assert announcement['title'] == 'Test Announcement'
        assert announcement['type'] == 'info'
        assert announcement['status'] == 'active'
    
    @mock_admin_auth()
    def test_create_announcement(self, client, sample_data):
        """Test creating a new announcement"""
        announcement_data = {
            'title': 'New Test Announcement',
            'message': 'This is a new test announcement',
            'type': 'warning',
            'priority': 'high',
            'target_audience': 'all',
            'channels': ['in_app', 'email']
        }
        
        response = client.post(
            '/v1/admin/communications/announcements',
            data=json.dumps(announcement_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # Should create successfully
        assert data['success'] is True
        assert 'announcement' in data
        assert data['announcement']['title'] == 'New Test Announcement'
        assert data['announcement']['type'] == 'warning'
    
    @mock_admin_auth()
    def test_announcement_validation(self, client, sample_data):
        """Test announcement validation"""
        # Test missing required fields
        response = client.post(
            '/v1/admin/communications/announcements',
            data=json.dumps({'title': 'Test'}),  # Missing message and type
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @mock_admin_auth()
    def test_announcement_filtering(self, client, sample_data):
        """Test announcement filtering"""
        response = client.get('/v1/admin/communications/announcements?status=active')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should filter by status
        for announcement in data['announcements']:
            assert announcement['status'] == 'active'


class TestDataIntegrity:
    """Test data integrity and relationships"""
    
    def test_database_relationships(self, sample_data):
        """Test that database relationships work correctly"""
        with SessionLocal() as session:
            # Test player-card relationship
            player = session.query(Player).first()
            assert player is not None
            
            # Test admin-announcement relationship
            announcement = session.query(Announcement).first()
            assert announcement is not None
            assert announcement.created_by_admin is not None
            assert announcement.created_by_admin.username == "test_admin"
    
    def test_data_consistency(self, sample_data):
        """Test data consistency across tables"""
        with SessionLocal() as session:
            # Check that all created data exists
            players_count = session.query(Player).count()
            assert players_count == 5
            
            orders_count = session.query(ShopOrder).count()
            assert orders_count == 3
            
            consoles_count = session.query(Console).count()
            assert consoles_count == 3


class TestPerformance:
    """Test performance of the new implementations"""
    
    @mock_admin_auth()
    def test_analytics_performance(self, client, sample_data):
        """Test that analytics endpoints respond quickly"""
        import time
        
        start_time = time.time()
        response = client.get('/v1/admin/analytics/dashboard-summary')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds
    
    @mock_admin_auth()
    def test_player_list_performance(self, client, sample_data):
        """Test that player listing performs well"""
        import time
        
        start_time = time.time()
        response = client.get('/v1/admin/players/?page=1&per_page=50')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v', '--tb=short'])
