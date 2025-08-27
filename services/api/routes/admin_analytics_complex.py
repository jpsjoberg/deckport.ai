

"""
Admin Analytics API Routes
Provides real-time analytics data for the admin panel
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from shared.database.connection import SessionLocal
from shared.models.base import Player, Device, VideoStream, EnhancedNFCCard, CardTrade
from shared.auth.unified_admin_auth import admin_auth_required
from shared.auth.admin_roles import Permission


admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/v1/admin/analytics')

    """Decorator to require admin authentication"""
    
    def decorated_function(*args, **kwargs):
        auth_result = verify_admin_token(request)
        if not auth_result['valid']:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_analytics_bp.route('/revenue', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_REVENUE])
def get_revenue_analytics():
    """Get revenue analytics data"""
    try:
        # Get time range from query params
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Calculate revenue from card trades (placeholder - would integrate with payment system)
        with SessionLocal() as session:
            trade_revenue = session.query(
                func.date(CardTrade.created_at).label('date'),
                func.count(CardTrade.id).label('trades'),
                func.sum(CardTrade.trade_value).label('revenue')
            ).filter(
                and_(
                    CardTrade.created_at >= start_date,
                    CardTrade.created_at <= end_date,
                    CardTrade.status == 'completed'
                )
            ).group_by(func.date(CardTrade.created_at)).all()
        
        # Format revenue data for charts
        revenue_data = []
        total_revenue = 0
        for trade in trade_revenue:
            daily_revenue = float(trade.revenue or 0)
            total_revenue += daily_revenue
            revenue_data.append({
                'date': trade.date.isoformat(),
                'trades': trade.trades,
                'revenue': daily_revenue
            })
        
        # Calculate growth metrics
        previous_period_end = start_date
        previous_period_start = previous_period_end - timedelta(days=days)
        
        previous_revenue = db.session.query(
            func.sum(CardTrade.trade_value)
        ).filter(
            and_(
                CardTrade.created_at >= previous_period_start,
                CardTrade.created_at < previous_period_end,
                CardTrade.status == 'completed'
            )
        ).scalar() or 0
        
        growth_rate = 0
        if previous_revenue > 0:
            growth_rate = ((total_revenue - previous_revenue) / previous_revenue) * 100
        
        return jsonify({
            'total_revenue': total_revenue,
            'growth_rate': round(growth_rate, 2),
            'daily_data': revenue_data,
            'period_days': days,
            'currency': 'USD'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get revenue analytics: {str(e)}'}), 500

@admin_analytics_bp.route('/player-behavior', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_PLAYERS])
def get_player_behavior():
    """Get player behavior analytics"""
    try:
        # Get time range
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Player registration trends
        new_players = db.session.query(
            func.date(Player.created_at).label('date'),
            func.count(Player.id).label('registrations')
        ).filter(
            and_(
                Player.created_at >= start_date,
                Player.created_at <= end_date
            )
        ).group_by(func.date(Player.created_at)).all()
        
        # Active players (players who activated cards recently)
        active_players = db.session.query(
            func.date(EnhancedNFCCard.activated_at).label('date'),
            func.count(func.distinct(EnhancedNFCCard.owner_player_id)).label('active_players')
        ).filter(
            and_(
                EnhancedNFCCard.activated_at >= start_date,
                EnhancedNFCCard.activated_at <= end_date,
                EnhancedNFCCard.status == 'activated'
            )
        ).group_by(func.date(EnhancedNFCCard.activated_at)).all()
        
        # Player retention (simplified)
        total_players = db.session.query(func.count(Player.id)).scalar()
        active_this_week = db.session.query(
            func.count(func.distinct(EnhancedNFCCard.owner_player_id))
        ).filter(
            and_(
                EnhancedNFCCard.last_used_at >= end_date - timedelta(days=7),
                EnhancedNFCCard.status == 'activated'
            )
        ).scalar() or 0
        
        retention_rate = (active_this_week / total_players * 100) if total_players > 0 else 0
        
        # Format data
        registration_data = [
            {
                'date': reg.date.isoformat(),
                'registrations': reg.registrations
            } for reg in new_players
        ]
        
        activity_data = [
            {
                'date': activity.date.isoformat(),
                'active_players': activity.active_players
            } for activity in active_players
        ]
        
        return jsonify({
            'total_players': total_players,
            'active_players_week': active_this_week,
            'retention_rate': round(retention_rate, 2),
            'registration_trend': registration_data,
            'activity_trend': activity_data,
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get player behavior: {str(e)}'}), 500

@admin_analytics_bp.route('/card-usage', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_SYSTEM])
def get_card_usage():
    """Get card usage analytics"""
    try:
        # Card activation rates by product
        card_stats = db.session.query(
            EnhancedNFCCard.product_sku,
            func.count(EnhancedNFCCard.id).label('total_cards'),
            func.sum(func.case([(EnhancedNFCCard.status == 'activated', 1)], else_=0)).label('activated_cards'),
            func.sum(EnhancedNFCCard.tap_counter).label('total_taps')
        ).group_by(EnhancedNFCCard.product_sku).all()
        
        # Most popular cards (by usage)
        popular_cards = db.session.query(
            EnhancedNFCCard.product_sku,
            func.sum(EnhancedNFCCard.tap_counter).label('total_usage')
        ).filter(
            EnhancedNFCCard.status == 'activated'
        ).group_by(EnhancedNFCCard.product_sku).order_by(
            func.sum(EnhancedNFCCard.tap_counter).desc()
        ).limit(10).all()
        
        # Trading activity
        trading_stats = db.session.query(
            func.count(CardTrade.id).label('total_trades'),
            func.count(func.case([(CardTrade.status == 'completed', 1)])).label('completed_trades'),
            func.count(func.case([(CardTrade.status == 'pending', 1)])).label('pending_trades')
        ).first()
        
        # Format data
        product_stats = []
        for stat in card_stats:
            activation_rate = (stat.activated_cards / stat.total_cards * 100) if stat.total_cards > 0 else 0
            product_stats.append({
                'product_sku': stat.product_sku,
                'total_cards': stat.total_cards,
                'activated_cards': stat.activated_cards,
                'activation_rate': round(activation_rate, 2),
                'total_taps': stat.total_taps or 0
            })
        
        popular_products = [
            {
                'product_sku': card.product_sku,
                'usage_count': card.total_usage or 0
            } for card in popular_cards
        ]
        
        return jsonify({
            'product_statistics': product_stats,
            'popular_products': popular_products,
            'trading_statistics': {
                'total_trades': trading_stats.total_trades,
                'completed_trades': trading_stats.completed_trades,
                'pending_trades': trading_stats.pending_trades,
                'completion_rate': round((trading_stats.completed_trades / trading_stats.total_trades * 100) if trading_stats.total_trades > 0 else 0, 2)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get card usage: {str(e)}'}), 500

@admin_analytics_bp.route('/system-metrics', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_SYSTEM])
def get_system_metrics():
    """Get system performance metrics"""
    try:
        # Console metrics
        total_consoles = db.session.query(func.count(Device.id)).scalar()
        active_consoles = db.session.query(func.count(Device.id)).filter(
            and_(
                Device.status == 'active',
                Device.last_seen > datetime.utcnow() - timedelta(minutes=5)
            )
        ).scalar()
        
        # Video streaming metrics
        active_streams = db.session.query(func.count(VideoStream.id)).filter(
            VideoStream.status == 'active'
        ).scalar()
        
        # Calculate uptime
        uptime_percentage = (active_consoles / total_consoles * 100) if total_consoles > 0 else 0
        
        # System health score (simplified)
        health_score = min(100, (uptime_percentage + 
                                (100 if active_streams < total_consoles * 0.5 else 80) + 
                                90) / 3)  # Average of metrics
        
        return jsonify({
            'console_metrics': {
                'total_consoles': total_consoles,
                'active_consoles': active_consoles,
                'uptime_percentage': round(uptime_percentage, 2)
            },
            'streaming_metrics': {
                'active_streams': active_streams,
                'max_concurrent_streams': total_consoles
            },
            'system_health': {
                'overall_score': round(health_score, 1),
                'status': 'healthy' if health_score > 90 else 'warning' if health_score > 70 else 'critical'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get system metrics: {str(e)}'}), 500

@admin_analytics_bp.route('/dashboard-summary', methods=['GET'])
@admin_auth_required(permissions=[Permission.ANALYTICS_VIEW])
def get_dashboard_summary():
    """Get summary analytics for the main dashboard"""
    try:
        # Get current date ranges
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Revenue metrics
        daily_revenue = db.session.query(func.sum(CardTrade.trade_value)).filter(
            and_(
                CardTrade.created_at >= today_start,
                CardTrade.status == 'completed'
            )
        ).scalar() or 0
        
        weekly_revenue = db.session.query(func.sum(CardTrade.trade_value)).filter(
            and_(
                CardTrade.created_at >= week_start,
                CardTrade.status == 'completed'
            )
        ).scalar() or 0
        
        monthly_revenue = db.session.query(func.sum(CardTrade.trade_value)).filter(
            and_(
                CardTrade.created_at >= month_start,
                CardTrade.status == 'completed'
            )
        ).scalar() or 0
        
        # Player metrics
        new_players_today = db.session.query(func.count(Player.id)).filter(
            Player.created_at >= today_start
        ).scalar()
        
        active_players_week = db.session.query(
            func.count(func.distinct(EnhancedNFCCard.owner_player_id))
        ).filter(
            and_(
                EnhancedNFCCard.last_used_at >= week_start,
                EnhancedNFCCard.status == 'activated'
            )
        ).scalar() or 0
        
        # Card metrics
        cards_activated_today = db.session.query(func.count(EnhancedNFCCard.id)).filter(
            and_(
                EnhancedNFCCard.activated_at >= today_start,
                EnhancedNFCCard.status == 'activated'
            )
        ).scalar()
        
        return jsonify({
            'revenue': {
                'daily': float(daily_revenue),
                'weekly': float(weekly_revenue),
                'monthly': float(monthly_revenue)
            },
            'players': {
                'new_today': new_players_today,
                'active_week': active_players_week
            },
            'cards': {
                'activated_today': cards_activated_today
            },
            'timestamp': now.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard summary: {str(e)}'}), 500
