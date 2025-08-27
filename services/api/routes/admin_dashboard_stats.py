"""
Admin dashboard statistics routes - Real data from database
"""

from flask import Blueprint, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func, text
from shared.database.connection import SessionLocal
from shared.models.base import Player, Console, Match, MatchParticipant, MatchStatus, ConsoleStatus, MMQueue
from shared.models.base import NFCCard
from shared.models.shop import ShopOrder
from shared.models.subscriptions import SubscriptionInvoice
from shared.auth.auto_rbac_decorator import auto_rbac_required
from shared.auth.admin_roles import Permission
import logging

logger = logging.getLogger(__name__)

admin_dashboard_stats_bp = Blueprint('admin_dashboard_stats', __name__, url_prefix='/v1/admin/dashboard')

@admin_dashboard_stats_bp.route('/stats', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        with SessionLocal() as session:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # === CONSOLE STATISTICS ===
            # Total consoles
            total_consoles = session.query(Console).count()
            
            # Active consoles (online in last 5 minutes)
            # Note: We'll need to add a last_seen field to Console model for real tracking
            # For now, count consoles with 'active' status
            active_consoles = session.query(Console).filter(
                Console.status == ConsoleStatus.active
            ).count()
            
            # === MATCH STATISTICS ===
            # Live matches (currently active)
            live_matches = session.query(Match).filter(
                Match.status == MatchStatus.active
            ).count()
            
            # Matches today
            matches_today = session.query(Match).filter(
                Match.created_at >= today_start
            ).count()
            
            # === PLAYER STATISTICS ===
            # Total players
            total_players = session.query(Player).count()
            
            # Players who played today
            active_players_today = session.query(Player).join(MatchParticipant).join(Match).filter(
                Match.created_at >= today_start
            ).distinct().count()
            
            # Players in matchmaking queue
            queued_players = session.query(MMQueue).count()
            
            # === REVENUE STATISTICS ===
            # Today's revenue from shop orders
            from shared.models.shop import OrderStatus
            todays_shop_revenue = session.query(func.coalesce(func.sum(ShopOrder.total_amount), 0)).filter(
                ShopOrder.created_at >= today_start,
                ShopOrder.order_status == 'completed'
            ).scalar() or 0
            
            # Today's subscription revenue - TEMPORARILY DISABLED
            todays_subscription_revenue = 0  # TODO: Fix enum issue
            
            # Total revenue for today
            todays_revenue = todays_shop_revenue + todays_subscription_revenue
            
            # === NFC CARD STATISTICS ===
            # Total NFC cards (use basic NFCCard table)
            try:
                total_nfc_cards = session.query(NFCCard).count()
                # Activated cards (cards with owners)
                activated_cards = session.query(NFCCard).filter(
                    NFCCard.owner_player_id.isnot(None)
                ).count()
            except Exception as e:
                logger.warning(f"NFC card stats unavailable: {e}")
                total_nfc_cards = 0
                activated_cards = 0
            
            # === SYSTEM HEALTH ===
            # Calculate system health based on active consoles ratio
            console_health_ratio = active_consoles / max(total_consoles, 1)
            if console_health_ratio >= 0.9:
                system_health = "excellent"
            elif console_health_ratio >= 0.7:
                system_health = "good"
            elif console_health_ratio >= 0.5:
                system_health = "warning"
            else:
                system_health = "critical"
            
            # === RECENT ACTIVITY ===
            # Get recent matches for activity feed
            recent_matches = session.query(Match).filter(
                Match.created_at >= now - timedelta(hours=1)
            ).order_by(desc(Match.created_at)).limit(5).all()
            
            recent_activity = []
            for match in recent_matches:
                recent_activity.append({
                    'type': 'match_started' if match.status == MatchStatus.active else 'match_completed',
                    'match_id': match.id,
                    'time': match.created_at.isoformat(),
                    'participants': len(match.participants) if match.participants else 0
                })
            
            # === COMPILE RESPONSE ===
            stats = {
                'consoles': {
                    'total': total_consoles,
                    'active': active_consoles,
                    'offline': total_consoles - active_consoles,
                    'health_ratio': round(console_health_ratio * 100, 1)
                },
                'matches': {
                    'live': live_matches,
                    'today': matches_today,
                    'queued_players': queued_players
                },
                'players': {
                    'total': total_players,
                    'active_today': active_players_today,
                    'in_queue': queued_players
                },
                'revenue': {
                    'today': float(todays_revenue),
                    'currency': 'USD',
                    'breakdown': {
                        'shop_today': float(todays_shop_revenue),
                        'subscription_today': float(todays_subscription_revenue)
                    }
                },
                'nfc_cards': {
                    'total': total_nfc_cards,
                    'activated': activated_cards,
                    'activation_rate': round((activated_cards / max(total_nfc_cards, 1)) * 100, 1)
                },
                'system': {
                    'health': system_health,
                    'uptime_hours': 24,  # TODO: Calculate real uptime
                    'last_updated': now.isoformat()
                },
                'recent_activity': recent_activity
            }
            
            return jsonify(stats)
            
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard statistics'}), 500

@admin_dashboard_stats_bp.route('/live-data', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])
def get_live_data():
    """Get live data for real-time updates (consoles online, live matches)"""
    try:
        with SessionLocal() as session:
            # Active consoles
            active_consoles = session.query(Console).filter(
                Console.status == ConsoleStatus.active
            ).count()
            
            # Live matches
            live_matches = session.query(Match).filter(
                Match.status == MatchStatus.active
            ).count()
            
            # Players in queue
            queued_players = session.query(MMQueue).count()
            
            # Get actual live match details
            live_match_details = []
            matches = session.query(Match).filter(
                Match.status == MatchStatus.active
            ).limit(10).all()
            
            for match in matches:
                participants = []
                for participant in match.participants:
                    if participant.player:
                        participants.append({
                            'player_id': participant.player.id,
                            'display_name': participant.player.display_name or f"Player {participant.player.id}",
                            'elo_rating': participant.player.elo_rating
                        })
                
                duration_minutes = 0
                if match.started_at:
                    duration = datetime.now(timezone.utc) - match.started_at
                    duration_minutes = int(duration.total_seconds() / 60)
                
                live_match_details.append({
                    'match_id': match.id,
                    'started_at': match.started_at.isoformat() if match.started_at else None,
                    'duration_minutes': duration_minutes,
                    'participants': participants,
                    'arena_id': match.arena_id
                })
            
            return jsonify({
                'active_consoles': active_consoles,
                'live_matches': live_matches,
                'queued_players': queued_players,
                'live_match_details': live_match_details,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error getting live data: {e}")
        return jsonify({'error': 'Failed to retrieve live data'}), 500

@admin_dashboard_stats_bp.route('/console-activity', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])
def get_console_activity():
    """Get console activity data for charts"""
    try:
        with SessionLocal() as session:
            # Get console activity over the last 24 hours
            now = datetime.now(timezone.utc)
            hours_data = []
            
            for i in range(24):
                hour_start = now - timedelta(hours=i+1)
                hour_end = now - timedelta(hours=i)
                
                # Count matches started in this hour
                matches_in_hour = session.query(Match).filter(
                    and_(
                        Match.created_at >= hour_start,
                        Match.created_at < hour_end
                    )
                ).count()
                
                hours_data.append({
                    'hour': hour_start.strftime('%H:00'),
                    'matches': matches_in_hour,
                    'timestamp': hour_start.isoformat()
                })
            
            # Reverse to get chronological order
            hours_data.reverse()
            
            return jsonify({
                'hourly_activity': hours_data,
                'period': '24_hours'
            })
            
    except Exception as e:
        logger.error(f"Error getting console activity: {e}")
        return jsonify({'error': 'Failed to retrieve console activity'}), 500
