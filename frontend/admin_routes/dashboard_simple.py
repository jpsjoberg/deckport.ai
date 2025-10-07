"""
Simple Dashboard Routes - Minimal version without complex API calls
"""

from flask import render_template, jsonify, request, redirect, url_for
from functools import wraps
from . import admin_bp

def require_admin_auth_simple(f):
    """Simple admin auth decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard-simple')
@require_admin_auth_simple
def dashboard_simple():
    """Simple admin dashboard without complex API calls"""
    
    # Basic stats without API calls
    stats = {
        'active_consoles': 1,
        'total_consoles': 1, 
        'live_matches': 0,
        'online_players': 0,
        'total_nfc_cards': 0,
        'activated_cards': 0,
        'system_health': 'good'
    }
    
    return render_template('admin/dashboard_simple.html', stats=stats, alerts=[])

@admin_bp.route('/test-auth')
def test_auth():
    """Test endpoint to check if routing works"""
    return jsonify({
        "status": "ok", 
        "message": "Admin routes are working",
        "timestamp": "2025-08-30"
    })
