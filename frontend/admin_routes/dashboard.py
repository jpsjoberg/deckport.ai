import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Dashboard Routes for Deckport Admin Panel
Main executive dashboard and overview
"""

from flask import render_template, jsonify, request, redirect, url_for
from functools import wraps
from . import admin_bp
import logging

logger = logging.getLogger(__name__)

def require_admin_auth(f):
    """Decorator to require admin authentication for frontend routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@require_admin_auth
def dashboard():
    """Main admin dashboard with system overview"""
    
    # Initialize with safe defaults
    stats = {
        'active_consoles': 0,
        'total_consoles': 0,
        'live_matches': 0,
        'online_players': 0,
        'total_nfc_cards': 0,
        'activated_cards': 0,
        'system_health': 'unknown',
        'recent_cards': []
    }
    alerts = []
    
    try:
        from services.api_service import APIService
        api_service = APIService()
        
        # Test API connectivity first
        logger.info("Testing API connectivity...")
        
        # Get console data (most important)
        try:
            consoles_response = api_service.get('/v1/admin/devices')
            if consoles_response and isinstance(consoles_response, dict):
                consoles = consoles_response.get('devices', [])
                stats['total_consoles'] = len(consoles)
                # Safe calculation of active consoles
                def safe_get_minutes(console):
                    minutes = console.get('last_seen_minutes')
                    if isinstance(minutes, (int, float)):
                        return minutes
                    elif isinstance(minutes, str) and minutes.isdigit():
                        return int(minutes)
                    else:
                        return 999  # Default for unknown
                
                stats['active_consoles'] = len([c for c in consoles if c.get('status') == 'active' and safe_get_minutes(c) < 5])
                logger.info(f"Console data loaded: {stats['total_consoles']} total, {stats['active_consoles']} active")
            else:
                logger.warning("Console API returned invalid response")
        except Exception as e:
            logger.error(f"Console API failed: {e}")
        
        # Get NFC card statistics (optional)
        try:
            nfc_stats_response = api_service.get('/v1/nfc-cards/admin/stats')
            if nfc_stats_response and isinstance(nfc_stats_response, dict):
                stats['total_nfc_cards'] = nfc_stats_response.get('total_cards', 0)
                stats['activated_cards'] = nfc_stats_response.get('activated_cards', 0)
                logger.info(f"NFC stats loaded: {stats['total_nfc_cards']} total")
        except Exception as e:
            logger.warning(f"NFC stats API failed: {e}")
        
        # Get live match data from correct endpoint
        try:
            matches_response = api_service.get('/v1/admin/game-operations/matches/live')
            if matches_response and isinstance(matches_response, dict):
                live_matches = len(matches_response.get('matches', []))
                stats['live_matches'] = live_matches
                logger.info(f"Live matches loaded: {live_matches}")
        except Exception as e:
            logger.warning(f"Live matches API failed: {e}")
            stats['live_matches'] = 0
        
        # Get player statistics (optional)
        try:
            players_response = api_service.get('/v1/admin/players/stats')
            if players_response and isinstance(players_response, dict):
                stats['online_players'] = players_response.get('online_players', 0)
                logger.info(f"Player stats loaded: {stats['online_players']} online")
        except Exception as e:
            logger.warning(f"Player stats API failed: {e}")
        
        # Get card service data (local) with datetime conversion
        try:
            from services.card_service import get_card_service
            card_service = get_card_service()
            card_stats = card_service.get_statistics()
            if card_stats and isinstance(card_stats, dict):
                recent_cards = card_stats.get('recent_cards', [])
                
                # Convert datetime objects to strings for template safety
                safe_cards = []
                for card in (recent_cards[:5] if recent_cards else []):
                    safe_card = dict(card) if hasattr(card, 'keys') else {}
                    
                    # Convert datetime to string
                    if 'created_at' in safe_card and hasattr(safe_card['created_at'], 'strftime'):
                        safe_card['created_at'] = safe_card['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    safe_cards.append(safe_card)
                
                stats['recent_cards'] = safe_cards
                logger.info(f"Card stats loaded: {len(stats['recent_cards'])} recent cards")
        except Exception as e:
            logger.warning(f"Card service failed: {e}")
            stats['recent_cards'] = []
        
        # Set system health
        if stats['total_consoles'] > 0:
            health_ratio = stats['active_consoles'] / stats['total_consoles']
            if health_ratio > 0.8:
                stats['system_health'] = 'good'
            elif health_ratio > 0.5:
                stats['system_health'] = 'warning'
            else:
                stats['system_health'] = 'critical'
        else:
            stats['system_health'] = 'unknown'
        
        logger.info(f"Dashboard stats compiled successfully: {stats}")
        
    except Exception as e:
        logger.error(f"Dashboard data compilation failed: {e}")
        alerts.append({
            'type': 'error', 
            'message': f'Dashboard error: {str(e)}', 
            'time': 'now'
        })
    
    return render_template('admin/index.html', stats=stats, alerts=alerts)


@admin_bp.route('/api/dashboard/stats')
@require_admin_auth
def dashboard_stats():
    """Real-time dashboard statistics API"""
    from services.api_service import APIService
    api_service = APIService()
    
    try:
        # Get real-time console data
        consoles_response = api_service.get('/v1/admin/devices')
        consoles = consoles_response.get('devices', []) if consoles_response else []
        
        total_consoles = len(consoles)
        active_consoles = len([c for c in consoles if c.get('status') == 'active' and (c.get('last_seen_minutes') or 999) < 5])
        
        # Get real-time NFC stats
        nfc_stats_response = api_service.get('/v1/nfc-cards/admin/stats/real-time')
        nfc_stats = nfc_stats_response if nfc_stats_response else {}
        
        # Get match statistics
        matches_response = api_service.get('/v1/admin/matches/stats')
        match_stats = matches_response if matches_response else {}
        
        stats = {
            'active_consoles': active_consoles,
            'total_consoles': total_consoles,
            'live_matches': match_stats.get('live_matches', 0),
            'online_players': match_stats.get('online_players', 0),
            'total_nfc_cards': nfc_stats.get('total_cards', 0),
            'activated_cards': nfc_stats.get('activated_cards', 0),
            'uptime': f"{(active_consoles / total_consoles * 100):.1f}%" if total_consoles > 0 else "0%",
            'avg_match_duration': match_stats.get('avg_match_duration', '0 min')
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get real-time stats: {str(e)}',
            'active_consoles': 0,
            'total_consoles': 0,
            'live_matches': 0,
            'online_players': 0,
            'total_nfc_cards': 0,
            'activated_cards': 0,
            'uptime': '0%',
            'avg_match_duration': '0 min'
        }), 500


@admin_bp.route('/api/alerts')
@require_admin_auth
def dashboard_alerts():
    """Dashboard alerts API endpoint"""
    from services.api_service import APIService
    api_service = APIService()
    
    try:
        # Try to get alerts from the backend API
        alerts_response = api_service.get('/v1/admin/alerts')
        
        if alerts_response and alerts_response.get('alerts'):
            critical_alerts = [
                alert for alert in alerts_response['alerts'] 
                if alert.get('severity') == 'critical'
            ]
            
            return jsonify({
                'critical_alerts': critical_alerts,
                'system_status': 'warning' if critical_alerts else 'healthy',
                'total_alerts': len(alerts_response.get('alerts', []))
            })
        else:
            # No alerts from API, return healthy status
            return jsonify({
                'critical_alerts': [],
                'system_status': 'healthy',
                'total_alerts': 0
            })
            
    except Exception as e:
        # Return minimal response if API fails
        return jsonify({
            'critical_alerts': [],
            'system_status': 'unknown',
            'total_alerts': 0,
            'error': f'Alert system unavailable: {str(e)}'
        })
