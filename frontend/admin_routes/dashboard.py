"""
Dashboard Routes for Deckport Admin Panel
Main executive dashboard and overview
"""

from flask import render_template, jsonify, request, redirect, url_for
from functools import wraps
from . import admin_bp

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
    from services.api_service import APIService
    api_service = APIService()
    
    try:
        # Get real console data
        consoles_response = api_service.get('/v1/admin/devices')
        consoles = consoles_response.get('devices', []) if consoles_response else []
        
        # Calculate real statistics
        total_consoles = len(consoles)
        active_consoles = len([c for c in consoles if c.get('status') == 'active' and (c.get('last_seen_minutes') or 999) < 5])
        
        # Get NFC card statistics
        nfc_stats_response = api_service.get('/v1/nfc-cards/admin/stats')
        nfc_stats = nfc_stats_response if nfc_stats_response else {}
        
        # Get live match data (placeholder for now)
        matches_response = api_service.get('/v1/admin/matches/live')
        live_matches = len(matches_response.get('matches', [])) if matches_response else 0
        
        # Get player statistics
        players_response = api_service.get('/v1/admin/players/stats')
        player_stats = players_response if players_response else {}
        
        stats = {
            'active_consoles': active_consoles,
            'total_consoles': total_consoles,
            'live_matches': live_matches,
            'online_players': player_stats.get('online_players', 0),
            'total_nfc_cards': nfc_stats.get('total_cards', 0),
            'activated_cards': nfc_stats.get('activated_cards', 0),
            'system_health': 'good' if active_consoles > total_consoles * 0.8 else 'warning'
        }
        
        # Get real alerts from system
        alerts_response = api_service.get('/v1/admin/alerts')
        alerts = alerts_response.get('alerts', []) if alerts_response else []
        
        # Add system-generated alerts
        if active_consoles < total_consoles * 0.9:
            alerts.insert(0, {
                'type': 'warning',
                'message': f'{total_consoles - active_consoles} consoles offline',
                'time': 'now'
            })
        
    except Exception as e:
        # Fallback to basic stats if API fails
        stats = {
            'active_consoles': 0,
            'total_consoles': 0,
            'live_matches': 0,
            'online_players': 0,
            'total_nfc_cards': 0,
            'activated_cards': 0,
            'system_health': 'error'
        }
        alerts = [
            {'type': 'error', 'message': f'API connection failed: {str(e)}', 'time': 'now'}
        ]
    
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
