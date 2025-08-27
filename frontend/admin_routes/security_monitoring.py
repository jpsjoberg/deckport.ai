"""
Admin security monitoring frontend routes
Provides web interface for security monitoring, audit logs, and access control
"""

from flask import render_template, request, jsonify, redirect, url_for, flash
from . import admin_bp
from services.api_service import APIService
import logging

logger = logging.getLogger(__name__)

def require_admin_auth(f):
    """Decorator to require admin authentication for routes"""
    from functools import wraps
    from frontend.app import _get_admin_jwt
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not _get_admin_jwt():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    
    return decorated_function

@admin_bp.route('/security')
@require_admin_auth
def security_monitoring():
    """Security monitoring dashboard"""
    api_service = APIService()
    
    try:
        # Get security dashboard data
        dashboard_response = api_service.get('/v1/admin/security/dashboard')
        dashboard_data = dashboard_response if dashboard_response else {}
        
        # Get recent audit logs
        audit_logs_response = api_service.get('/v1/admin/security/audit-logs', {
            'per_page': 20,
            'hours': 24
        })
        audit_logs = audit_logs_response.get('audit_logs', []) if audit_logs_response else []
        
        # Get admin activity
        activity_response = api_service.get('/v1/admin/security/admin-activity', {
            'hours': 24
        })
        admin_activity = activity_response.get('admin_activity', []) if activity_response else []
        
        return render_template('admin/security/monitoring.html',
                             dashboard=dashboard_data,
                             audit_logs=audit_logs,
                             admin_activity=admin_activity)
        
    except Exception as e:
        logger.error(f"Error loading security monitoring: {e}")
        flash('Error loading security monitoring data', 'error')
        return render_template('admin/security/monitoring.html',
                             dashboard={},
                             audit_logs=[],
                             admin_activity=[])

@admin_bp.route('/security/audit-logs')
@require_admin_auth
def audit_logs():
    """Detailed audit logs view"""
    api_service = APIService()
    
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        hours = int(request.args.get('hours', 24))
        actor_type = request.args.get('actor_type', '')
        action = request.args.get('action', '')
        sensitive_only = request.args.get('sensitive_only', 'false') == 'true'
        
        # Build query parameters
        params = {
            'page': page,
            'per_page': per_page,
            'hours': hours
        }
        
        if actor_type:
            params['actor_type'] = actor_type
        if action:
            params['action'] = action
        if sensitive_only:
            params['sensitive_only'] = 'true'
        
        # Get audit logs
        response = api_service.get('/v1/admin/security/audit-logs', params)
        
        if response:
            audit_logs = response.get('audit_logs', [])
            pagination = response.get('pagination', {})
            filters = response.get('filters', {})
        else:
            audit_logs = []
            pagination = {}
            filters = {}
        
        return render_template('admin/security/audit_logs.html',
                             audit_logs=audit_logs,
                             pagination=pagination,
                             filters=filters,
                             current_params=params)
        
    except Exception as e:
        logger.error(f"Error loading audit logs: {e}")
        flash('Error loading audit logs', 'error')
        return render_template('admin/security/audit_logs.html',
                             audit_logs=[],
                             pagination={},
                             filters={},
                             current_params={})

@admin_bp.route('/security/ip-access-control')
@require_admin_auth
def ip_access_control():
    """IP access control management"""
    api_service = APIService()
    
    try:
        # Get current IP access control configuration
        response = api_service.get('/v1/admin/security/ip-access-control')
        config = response if response else {
            'allowlist_enabled': False,
            'allowlist': [],
            'blocklist': []
        }
        
        return render_template('admin/security/ip_access_control.html',
                             config=config)
        
    except Exception as e:
        logger.error(f"Error loading IP access control: {e}")
        flash('Error loading IP access control configuration', 'error')
        return render_template('admin/security/ip_access_control.html',
                             config={
                                 'allowlist_enabled': False,
                                 'allowlist': [],
                                 'blocklist': []
                             })

@admin_bp.route('/security/admin-sessions')
@require_admin_auth
def admin_sessions():
    """Admin session management"""
    api_service = APIService()
    
    try:
        # Get admin sessions
        response = api_service.get('/v1/admin/security/admin-sessions')
        sessions_data = response if response else {'sessions': [], 'count': 0}
        
        return render_template('admin/security/admin_sessions.html',
                             sessions=sessions_data.get('sessions', []),
                             count=sessions_data.get('count', 0))
        
    except Exception as e:
        logger.error(f"Error loading admin sessions: {e}")
        flash('Error loading admin sessions', 'error')
        return render_template('admin/security/admin_sessions.html',
                             sessions=[],
                             count=0)

# API endpoints for AJAX requests

@admin_bp.route('/api/security/add-ip-allowlist', methods=['POST'])
@require_admin_auth
def add_ip_allowlist():
    """Add IP to allowlist via AJAX"""
    api_service = APIService()
    
    try:
        data = request.get_json()
        if not data or 'ip_or_network' not in data:
            return jsonify({'success': False, 'message': 'IP or network is required'}), 400
        
        response = api_service.post('/v1/admin/security/ip-access-control/allowlist', data)
        
        if response and response.get('success'):
            return jsonify({'success': True, 'message': response.get('message')})
        else:
            return jsonify({'success': False, 'message': 'Failed to add to allowlist'}), 400
        
    except Exception as e:
        logger.error(f"Error adding to IP allowlist: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@admin_bp.route('/api/security/add-ip-blocklist', methods=['POST'])
@require_admin_auth
def add_ip_blocklist():
    """Add IP to blocklist via AJAX"""
    api_service = APIService()
    
    try:
        data = request.get_json()
        if not data or 'ip_or_network' not in data:
            return jsonify({'success': False, 'message': 'IP or network is required'}), 400
        
        response = api_service.post('/v1/admin/security/ip-access-control/blocklist', data)
        
        if response and response.get('success'):
            return jsonify({'success': True, 'message': response.get('message')})
        else:
            return jsonify({'success': False, 'message': 'Failed to add to blocklist'}), 400
        
    except Exception as e:
        logger.error(f"Error adding to IP blocklist: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@admin_bp.route('/api/security/reset-rate-limit', methods=['POST'])
@require_admin_auth
def reset_rate_limit():
    """Reset rate limit for identifier via AJAX"""
    api_service = APIService()
    
    try:
        data = request.get_json()
        if not data or 'identifier' not in data:
            return jsonify({'success': False, 'message': 'Identifier is required'}), 400
        
        identifier = data['identifier']
        response = api_service.post(f'/v1/admin/security/rate-limits/{identifier}/reset', data)
        
        if response and response.get('success'):
            return jsonify({'success': True, 'message': response.get('message')})
        else:
            return jsonify({'success': False, 'message': 'Failed to reset rate limit'}), 400
        
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500
