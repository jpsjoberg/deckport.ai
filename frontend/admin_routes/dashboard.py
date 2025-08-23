"""
Dashboard Routes for Deckport Admin Panel
Main executive dashboard and overview
"""

from flask import render_template, jsonify
from . import admin_bp


@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    """Main admin dashboard with system overview"""
    # Mock data for now - replace with real API calls
    stats = {
        'active_consoles': 47,
        'total_consoles': 50,
        'live_matches': 23,
        'online_players': 1247,
        'daily_revenue': 2341,
        'system_health': 'good'
    }
    
    alerts = [
        {'type': 'warning', 'message': 'Console #42 offline for 2 hours', 'time': '2 hours ago'},
        {'type': 'info', 'message': 'New card balance update deployed', 'time': '4 hours ago'}
    ]
    
    return render_template('admin/index.html', stats=stats, alerts=alerts)


@admin_bp.route('/api/dashboard/stats')
def dashboard_stats():
    """Real-time dashboard statistics API"""
    # This would connect to actual metrics in production
    stats = {
        'active_consoles': 47,
        'total_consoles': 50,
        'live_matches': 23,
        'online_players': 1247,
        'daily_revenue': 2341,
        'uptime': '99.8%',
        'avg_match_duration': '8.4 min'
    }
    return jsonify(stats)
