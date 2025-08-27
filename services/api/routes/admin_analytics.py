

"""
Admin Analytics API Routes - Real Database Implementation
Provides real-time analytics data for the admin panel
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from shared.auth.unified_admin_auth import admin_auth_required
from shared.auth.admin_roles import Permission
from shared.database.connection import SessionLocal
from shared.models.base import Player, Match, MatchParticipant, Console, AuditLog
from shared.models.tournaments import WalletTransaction, PlayerWallet
from shared.models.shop import ShopOrder, ShopOrderItem
from shared.models.nfc_trading_system import TradingHistory
from shared.models.player_moderation import PlayerActivityLog
from shared.models.subscriptions import Subscription, SubscriptionInvoice
import logging

logger = logging.getLogger(__name__)

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/v1/admin/analytics')

@admin_analytics_bp.route('/revenue', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_REVENUE])
def get_revenue_analytics():
    """Get revenue analytics data from real transactions"""
    try:
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        with SessionLocal() as session:
            # Get shop order revenue by day
            shop_revenue = session.query(
                func.date(ShopOrder.created_at).label('date'),
                func.sum(ShopOrder.total_amount).label('revenue'),
                func.count(ShopOrder.id).label('order_count')
            ).filter(
                and_(
                    ShopOrder.created_at >= start_date,
                    ShopOrder.order_status.in_(['completed', 'fulfilled'])
                )
            ).group_by(func.date(ShopOrder.created_at)).all()
            
            # Get trading revenue by day
            trading_revenue = session.query(
                func.date(TradingHistory.traded_at).label('date'),
                func.sum(TradingHistory.price).label('revenue'),
                func.count(TradingHistory.id).label('trade_count')
            ).filter(
                TradingHistory.traded_at >= start_date
            ).group_by(func.date(TradingHistory.traded_at)).all()
            
            # Get subscription revenue by day (from paid invoices) - TEMPORARILY DISABLED
            subscription_revenue = []  # TODO: Fix enum issue
            
            # Combine revenue data by date
            revenue_by_date = {}
            total_revenue = Decimal('0.00')
            
            # Process shop orders
            for row in shop_revenue:
                date_str = row.date.isoformat()
                revenue_by_date[date_str] = {
                    'date': date_str,
                    'shop_revenue': float(row.revenue or 0),
                    'shop_orders': row.order_count,
                    'trading_revenue': 0.0,
                    'trades': 0,
                    'subscription_revenue': 0.0,
                    'subscription_payments': 0
                }
                total_revenue += (row.revenue or Decimal('0.00'))
            
            # Process trading data
            for row in trading_revenue:
                date_str = row.date.isoformat()
                if date_str in revenue_by_date:
                    revenue_by_date[date_str]['trading_revenue'] = float(row.revenue or 0)
                    revenue_by_date[date_str]['trades'] = row.trade_count
                else:
                    revenue_by_date[date_str] = {
                        'date': date_str,
                        'shop_revenue': 0.0,
                        'shop_orders': 0,
                        'trading_revenue': float(row.revenue or 0),
                        'trades': row.trade_count,
                        'subscription_revenue': 0.0,
                        'subscription_payments': 0
                    }
                total_revenue += (row.revenue or Decimal('0.00'))
            
            # Process subscription data
            for row in subscription_revenue:
                date_str = row.date.isoformat()
                if date_str in revenue_by_date:
                    revenue_by_date[date_str]['subscription_revenue'] = float(row.revenue or 0)
                    revenue_by_date[date_str]['subscription_payments'] = row.invoice_count
                else:
                    revenue_by_date[date_str] = {
                        'date': date_str,
                        'shop_revenue': 0.0,
                        'shop_orders': 0,
                        'trading_revenue': 0.0,
                        'trades': 0,
                        'subscription_revenue': float(row.revenue or 0),
                        'subscription_payments': row.invoice_count
                    }
                total_revenue += (row.revenue or Decimal('0.00'))
            
            # Calculate total revenue per day and sort by date
            daily_data = []
            for date_str in sorted(revenue_by_date.keys()):
                data = revenue_by_date[date_str]
                data['total_revenue'] = data['shop_revenue'] + data['trading_revenue'] + data['subscription_revenue']
                # Add 'revenue' field for frontend compatibility
                data['revenue'] = data['total_revenue']
                daily_data.append(data)
            
            # Calculate growth rate (compare to previous period)
            previous_start = start_date - timedelta(days=days)
            previous_revenue = session.query(
                func.sum(ShopOrder.total_amount)
            ).filter(
                and_(
                    ShopOrder.created_at >= previous_start,
                    ShopOrder.created_at < start_date,
                    ShopOrder.order_status.in_(['completed', 'fulfilled'])
                )
            ).scalar() or Decimal('0.00')
            
            previous_trading = session.query(
                func.sum(TradingHistory.price)
            ).filter(
                and_(
                    TradingHistory.traded_at >= previous_start,
                    TradingHistory.traded_at < start_date
                )
            ).scalar() or Decimal('0.00')
            
            previous_subscription = Decimal('0.00')  # TODO: Fix enum issue
            
            previous_total = previous_revenue + previous_trading + previous_subscription
            growth_rate = 0.0
            if previous_total > 0:
                growth_rate = float((total_revenue - previous_total) / previous_total * 100)
            
            return jsonify({
                'total_revenue': float(total_revenue),
                'growth_rate': round(growth_rate, 2),
                'daily_data': daily_data,
                'period_days': days,
                'currency': 'USD',
                'breakdown': {
                    'shop_revenue': float(sum(row.revenue or 0 for row in shop_revenue)),
                    'trading_revenue': float(sum(row.revenue or 0 for row in trading_revenue)),
                    'subscription_revenue': float(sum(row.revenue or 0 for row in subscription_revenue))
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting revenue analytics: {e}")
        return jsonify({'error': f'Failed to get revenue analytics: {str(e)}'}), 500

@admin_analytics_bp.route('/player-behavior', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_PLAYERS])
def get_player_behavior():
    """Get player behavior analytics from real data"""
    try:
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        with SessionLocal() as session:
            # Get player registrations by day
            registrations = session.query(
                func.date(Player.created_at).label('date'),
                func.count(Player.id).label('registrations')
            ).filter(
                Player.created_at >= start_date
            ).group_by(func.date(Player.created_at)).all()
            
            # Get daily active players (players who logged in each day)
            activity_logs = session.query(
                func.date(PlayerActivityLog.timestamp).label('date'),
                func.count(func.distinct(PlayerActivityLog.player_id)).label('active_players')
            ).filter(
                and_(
                    PlayerActivityLog.timestamp >= start_date,
                    PlayerActivityLog.activity_type == 'LOGIN'
                )
            ).group_by(func.date(PlayerActivityLog.timestamp)).all()
            
            # Get total players
            total_players = session.query(func.count(Player.id)).scalar() or 0
            
            # Get active players in the last week
            week_ago = end_date - timedelta(days=7)
            active_players_week = session.query(
                func.count(func.distinct(PlayerActivityLog.player_id))
            ).filter(
                and_(
                    PlayerActivityLog.timestamp >= week_ago,
                    PlayerActivityLog.activity_type == 'LOGIN'
                )
            ).scalar() or 0
            
            # Calculate retention rate (players who logged in within 7 days of registration)
            retention_query = session.query(
                func.count(func.distinct(Player.id)).label('retained')
            ).join(
                PlayerActivityLog, Player.id == PlayerActivityLog.player_id
            ).filter(
                and_(
                    Player.created_at >= start_date,
                    PlayerActivityLog.activity_type == 'LOGIN',
                    PlayerActivityLog.timestamp <= Player.created_at + timedelta(days=7)
                )
            ).scalar() or 0
            
            new_players_period = session.query(
                func.count(Player.id)
            ).filter(Player.created_at >= start_date).scalar() or 0
            
            retention_rate = 0.0
            if new_players_period > 0:
                retention_rate = (retention_query / new_players_period) * 100
            
            # Format registration data
            registration_data = []
            reg_dict = {row.date.isoformat(): row.registrations for row in registrations}
            
            # Format activity data
            activity_data = []
            activity_dict = {row.date.isoformat(): row.active_players for row in activity_logs}
            
            # Fill in missing days with zero values
            for i in range(days):
                date = (start_date + timedelta(days=i)).date()
                date_str = date.isoformat()
                
                registration_data.append({
                    'date': date_str,
                    'registrations': reg_dict.get(date_str, 0)
                })
                
                activity_data.append({
                    'date': date_str,
                    'active_players': activity_dict.get(date_str, 0)
                })
            
            # Get additional metrics (duration_ms field doesn't exist, use placeholder)
            avg_session_duration = 0  # TODO: Add duration tracking to PlayerActivityLog model
            
            return jsonify({
                'total_players': total_players,
                'active_players_week': active_players_week,
                'retention_rate': round(retention_rate, 2),
                'registration_trend': registration_data,
                'activity_trend': activity_data,
                'period_days': days,
                'metrics': {
                    'avg_session_duration_ms': int(avg_session_duration or 0),
                    'new_players_period': new_players_period,
                    'retention_count': retention_query
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting player behavior analytics: {e}")
        return jsonify({'error': f'Failed to get player behavior: {str(e)}'}), 500

@admin_analytics_bp.route('/card-usage', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_SYSTEM])
def get_card_usage():
    """Get card usage analytics from real data"""
    try:
        with SessionLocal() as session:
            # Import card-related models
            from shared.models.base import CardCatalog, NFCCard, PlayerCard
            
            # Get card statistics by product SKU - simplified approach
            card_stats = session.query(
                CardCatalog.product_sku,
                CardCatalog.name,
                func.count(NFCCard.id).label('total_nfc_cards'),
                func.sum(PlayerCard.quantity).label('digital_cards')
            ).outerjoin(
                NFCCard, CardCatalog.id == NFCCard.card_template_id
            ).outerjoin(
                PlayerCard, CardCatalog.id == PlayerCard.card_template_id
            ).group_by(
                CardCatalog.id, CardCatalog.product_sku, CardCatalog.name
            ).all()
            
            # Get activated cards separately
            activated_stats = session.query(
                CardCatalog.product_sku,
                func.count(NFCCard.id).label('activated_count')
            ).join(
                NFCCard, CardCatalog.id == NFCCard.card_template_id
            ).filter(
                NFCCard.status == 'activated'
            ).group_by(
                CardCatalog.product_sku
            ).all()
            
            # Create lookup for activated counts
            activated_lookup = {row.product_sku: row.activated_count for row in activated_stats}
            
            # Calculate activation rates and format data
            product_statistics = []
            for row in card_stats:
                total_cards = row.total_nfc_cards or 0
                activated_cards = activated_lookup.get(row.product_sku, 0)
                digital_cards = row.digital_cards or 0
                
                activation_rate = 0.0
                if total_cards > 0:
                    activation_rate = (activated_cards / total_cards) * 100
                
                product_statistics.append({
                    'product_sku': row.product_sku,
                    'name': row.name,
                    'total_nfc_cards': total_cards,
                    'activated_cards': activated_cards,
                    'digital_cards': digital_cards,
                    'activation_rate': round(activation_rate, 1)
                })
            
            # Get most traded cards
            popular_cards = session.query(
                CardCatalog.product_sku,
                CardCatalog.name,
                func.count(TradingHistory.id).label('trade_count'),
                func.sum(TradingHistory.price).label('total_value')
            ).join(
                TradingHistory, CardCatalog.id == TradingHistory.card_id
            ).group_by(
                CardCatalog.id, CardCatalog.product_sku, CardCatalog.name
            ).order_by(
                func.count(TradingHistory.id).desc()
            ).limit(10).all()
            
            popular_products = []
            for row in popular_cards:
                popular_products.append({
                    'product_sku': row.product_sku,
                    'name': row.name,
                    'trade_count': row.trade_count,
                    'total_value': float(row.total_value or 0)
                })
            
            # Get trading statistics
            from shared.models.nfc_trading_system import TradeOffer
            
            total_trades = session.query(func.count(TradingHistory.id)).scalar() or 0
            
            # Get trade offers statistics
            pending_trades = session.query(
                func.count(TradeOffer.id)
            ).filter(TradeOffer.status == 'pending').scalar() or 0
            
            completed_trades = session.query(
                func.count(TradeOffer.id)
            ).filter(TradeOffer.status == 'completed').scalar() or 0
            
            total_trade_offers = session.query(func.count(TradeOffer.id)).scalar() or 0
            completion_rate = 0.0
            if total_trade_offers > 0:
                completion_rate = (completed_trades / total_trade_offers) * 100
            
            # Get card transfer statistics - simplified approach
            try:
                from shared.models.base import CardTransfer
                total_transfers = session.query(CardTransfer).count()
                completed_transfers = session.query(CardTransfer).filter(CardTransfer.status == 'claimed').count()
                pending_transfers = session.query(CardTransfer).filter(CardTransfer.status == 'pending').count()
                
                class TransferStats:
                    def __init__(self, total, completed, pending):
                        self.total_transfers = total
                        self.completed_transfers = completed
                        self.pending_transfers = pending
                
                transfer_stats = TransferStats(total_transfers, completed_transfers, pending_transfers)
            except ImportError:
                # CardTransfer model doesn't exist, use defaults
                class TransferStats:
                    def __init__(self):
                        self.total_transfers = 0
                        self.completed_transfers = 0
                        self.pending_transfers = 0
                
                transfer_stats = TransferStats()
            
            return jsonify({
                'product_statistics': product_statistics,
                'popular_products': popular_products,
                'trading_statistics': {
                    'total_trades': total_trades,
                    'pending_trade_offers': pending_trades,
                    'completed_trade_offers': completed_trades,
                    'completion_rate': round(completion_rate, 1),
                    'total_transfers': transfer_stats.total_transfers or 0,
                    'completed_transfers': transfer_stats.completed_transfers or 0,
                    'pending_transfers': transfer_stats.pending_transfers or 0
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting card usage analytics: {e}")
        return jsonify({'error': f'Failed to get card usage: {str(e)}'}), 500

@admin_analytics_bp.route('/system-metrics', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_SYSTEM])
def get_system_metrics():
    """Get system performance metrics from real data"""
    try:
        with SessionLocal() as session:
            # Get console metrics
            total_consoles = session.query(func.count(Console.id)).scalar() or 0
            active_consoles = session.query(
                func.count(Console.id)
            ).filter(Console.status == 'active').scalar() or 0
            
            # Calculate uptime percentage (consoles that are active vs total)
            uptime_percentage = 0.0
            if total_consoles > 0:
                uptime_percentage = (active_consoles / total_consoles) * 100
            
            # Get streaming metrics
            from shared.models.base import VideoStream
            
            active_streams = session.query(
                func.count(VideoStream.id)
            ).filter(VideoStream.status == 'active').scalar() or 0
            
            total_streams_today = session.query(
                func.count(VideoStream.id)
            ).filter(
                func.date(VideoStream.created_at) == datetime.utcnow().date()
            ).scalar() or 0
            
            # Get match metrics
            active_matches = session.query(
                func.count(Match.id)
            ).filter(Match.status == 'active').scalar() or 0
            
            matches_today = session.query(
                func.count(Match.id)
            ).filter(
                func.date(Match.created_at) == datetime.utcnow().date()
            ).scalar() or 0
            
            # Get error/audit metrics for system health
            recent_errors = session.query(
                func.count(AuditLog.id)
            ).filter(
                and_(
                    AuditLog.created_at >= datetime.utcnow() - timedelta(hours=24),
                    AuditLog.action.like('%error%')
                )
            ).scalar() or 0
            
            # Calculate system health score
            health_factors = []
            
            # Console health (weight: 30%)
            console_health = uptime_percentage
            health_factors.append(console_health * 0.3)
            
            # Activity health (weight: 40%) - based on matches and streams
            activity_score = min(100, (matches_today + total_streams_today) * 2)  # Scale appropriately
            health_factors.append(activity_score * 0.4)
            
            # Error rate health (weight: 30%) - fewer errors = better health
            error_penalty = min(50, recent_errors * 5)  # Each error reduces score
            error_health = max(0, 100 - error_penalty)
            health_factors.append(error_health * 0.3)
            
            overall_score = sum(health_factors)
            
            # Determine status based on score
            if overall_score >= 90:
                status = 'excellent'
            elif overall_score >= 75:
                status = 'healthy'
            elif overall_score >= 60:
                status = 'warning'
            else:
                status = 'critical'
            
            # Get database metrics
            player_count = session.query(func.count(Player.id)).scalar() or 0
            
            return jsonify({
                'console_metrics': {
                    'total_consoles': total_consoles,
                    'active_consoles': active_consoles,
                    'uptime_percentage': round(uptime_percentage, 1)
                },
                'streaming_metrics': {
                    'active_streams': active_streams,
                    'streams_today': total_streams_today
                },
                'match_metrics': {
                    'active_matches': active_matches,
                    'matches_today': matches_today
                },
                'system_health': {
                    'overall_score': round(overall_score, 1),
                    'status': status,
                    'factors': {
                        'console_health': round(console_health, 1),
                        'activity_score': round(activity_score, 1),
                        'error_health': round(error_health, 1)
                    }
                },
                'database_metrics': {
                    'total_players': player_count,
                    'recent_errors': recent_errors
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({'error': f'Failed to get system metrics: {str(e)}'}), 500

@admin_analytics_bp.route('/dashboard-summary', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_VIEW])
def get_dashboard_summary():
    """Get summary analytics for the main dashboard from real data"""
    try:
        with SessionLocal() as session:
            now = datetime.utcnow()
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Revenue calculations
            daily_revenue = session.query(
                func.coalesce(func.sum(ShopOrder.total_amount), 0)
            ).filter(
                and_(
                    func.date(ShopOrder.created_at) == today,
                    ShopOrder.order_status.in_(['completed', 'fulfilled'])
                )
            ).scalar() or Decimal('0.00')
            
            weekly_revenue = session.query(
                func.coalesce(func.sum(ShopOrder.total_amount), 0)
            ).filter(
                and_(
                    ShopOrder.created_at >= week_ago,
                    ShopOrder.order_status.in_(['completed', 'fulfilled'])
                )
            ).scalar() or Decimal('0.00')
            
            monthly_revenue = session.query(
                func.coalesce(func.sum(ShopOrder.total_amount), 0)
            ).filter(
                and_(
                    ShopOrder.created_at >= month_ago,
                    ShopOrder.order_status.in_(['completed', 'fulfilled'])
                )
            ).scalar() or Decimal('0.00')
            
            # Add trading revenue
            daily_trading = session.query(
                func.coalesce(func.sum(TradingHistory.price), 0)
            ).filter(
                func.date(TradingHistory.traded_at) == today
            ).scalar() or Decimal('0.00')
            
            weekly_trading = session.query(
                func.coalesce(func.sum(TradingHistory.price), 0)
            ).filter(
                TradingHistory.traded_at >= week_ago
            ).scalar() or Decimal('0.00')
            
            monthly_trading = session.query(
                func.coalesce(func.sum(TradingHistory.price), 0)
            ).filter(
                TradingHistory.traded_at >= month_ago
            ).scalar() or Decimal('0.00')
            
            # Add subscription revenue - TEMPORARILY DISABLED
            daily_subscription = Decimal('0.00')  # TODO: Fix enum issue
            weekly_subscription = Decimal('0.00')  # TODO: Fix enum issue
            monthly_subscription = Decimal('0.00')  # TODO: Fix enum issue
            
            # Player statistics
            new_players_today = session.query(
                func.count(Player.id)
            ).filter(
                func.date(Player.created_at) == today
            ).scalar() or 0
            
            active_players_week = session.query(
                func.count(func.distinct(PlayerActivityLog.player_id))
            ).filter(
                and_(
                    PlayerActivityLog.timestamp >= week_ago,
                    PlayerActivityLog.activity_type == 'LOGIN'
                )
            ).scalar() or 0
            
            # Card statistics
            from shared.models.base import NFCCard
            
            cards_activated_today = session.query(
                func.count(NFCCard.id)
            ).filter(
                and_(
                    func.date(NFCCard.activated_at) == today,
                    NFCCard.status == 'activated'
                )
            ).scalar() or 0
            
            # System activity
            matches_today = session.query(
                func.count(Match.id)
            ).filter(
                func.date(Match.created_at) == today
            ).scalar() or 0
            
            active_consoles = session.query(
                func.count(Console.id)
            ).filter(Console.status == 'active').scalar() or 0
            
            # Get device/console information for frontend compatibility
            devices = session.query(Console).limit(10).all()  # Get sample of devices
            device_list = []
            for device in devices:
                device_list.append({
                    'id': device.id,
                    'uid': device.device_uid,  # Fixed: use device_uid instead of uid
                    'status': device.status,
                    'last_seen_minutes': 0 if device.status == 'active' else 999,  # Mock data for now
                    'location': getattr(device, 'location', 'Unknown'),  # Safe access since location might not exist
                    'created_at': device.registered_at.isoformat() if device.registered_at else None  # Fixed: use registered_at
                })
            
            return jsonify({
                'revenue': {
                    'daily': float(daily_revenue + daily_trading + daily_subscription),
                    'weekly': float(weekly_revenue + weekly_trading + weekly_subscription),
                    'monthly': float(monthly_revenue + monthly_trading + monthly_subscription),
                    'breakdown': {
                        'shop_daily': float(daily_revenue),
                        'trading_daily': float(daily_trading),
                        'subscription_daily': float(daily_subscription)
                    }
                },
                'players': {
                    'new_today': new_players_today,
                    'active_week': active_players_week
                },
                'cards': {
                    'activated_today': cards_activated_today,
                    'total_cards': len(device_list),  # Placeholder - should be actual card count
                    'activated_cards': cards_activated_today
                },
                'system': {
                    'matches_today': matches_today,
                    'active_consoles': active_consoles
                },
                # Frontend compatibility fields
                'devices': device_list,
                'online_players': active_players_week,  # Use active_week as online_players approximation
                'timestamp': now.isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return jsonify({'error': f'Failed to get dashboard summary: {str(e)}'}), 500
