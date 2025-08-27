"""
Admin security monitoring API routes
Provides endpoints for security monitoring, audit logs, and access control management
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, func, and_, or_
from shared.database.connection import SessionLocal
from shared.models.base import AuditLog, Admin
from shared.auth.auto_rbac_decorator import auto_rbac_required, super_admin_only
from shared.auth.admin_roles import Permission
from shared.security import (
    AdminAuditLogger, get_rate_limit_status, reset_rate_limit,
    session_manager, ip_access_control
)
import logging

logger = logging.getLogger(__name__)

admin_security_bp = Blueprint('admin_security', __name__, url_prefix='/v1/admin/security')

# === AUDIT LOGS ===

@admin_security_bp.route('/audit-logs', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_LOGS])
def get_audit_logs():
    """Get audit logs with filtering and pagination"""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        actor_type = request.args.get('actor_type')  # admin, player, console
        action = request.args.get('action')
        admin_id = request.args.get('admin_id', type=int)
        hours = int(request.args.get('hours', 24))
        sensitive_only = request.args.get('sensitive_only', 'false').lower() == 'true'
        
        # Calculate time range
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with SessionLocal() as session:
            # Build query
            query = session.query(AuditLog).filter(
                AuditLog.created_at >= cutoff_time
            )
            
            # Apply filters
            if actor_type:
                query = query.filter(AuditLog.actor_type == actor_type)
            
            if action:
                query = query.filter(AuditLog.action.ilike(f'%{action}%'))
            
            if admin_id:
                query = query.filter(AuditLog.actor_id == admin_id)
            
            if sensitive_only:
                query = query.filter(
                    AuditLog.details.op('->>')('sensitive') == 'true'
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            logs = query.order_by(desc(AuditLog.created_at)).offset(
                (page - 1) * per_page
            ).limit(per_page).all()
            
            # Format response
            audit_logs = []
            for log in logs:
                audit_logs.append({
                    'id': log.id,
                    'actor_type': log.actor_type,
                    'actor_id': log.actor_id,
                    'action': log.action,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'created_at': log.created_at.isoformat(),
                    'sensitive': log.details.get('sensitive', False) if log.details else False
                })
            
            return jsonify({
                'audit_logs': audit_logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                },
                'filters': {
                    'actor_type': actor_type,
                    'action': action,
                    'admin_id': admin_id,
                    'hours': hours,
                    'sensitive_only': sensitive_only
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({'error': 'Failed to retrieve audit logs'}), 500

@admin_security_bp.route('/security-events', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_LOGS])
def get_security_events():
    """Get recent security events"""
    try:
        hours = int(request.args.get('hours', 24))
        events = AdminAuditLogger.get_security_events(hours)
        
        return jsonify({
            'security_events': events,
            'timeframe_hours': hours,
            'count': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        return jsonify({'error': 'Failed to retrieve security events'}), 500

# === ADMIN ACTIVITY MONITORING ===

@admin_security_bp.route('/admin-activity', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.ADMIN_VIEW])
def get_admin_activity():
    """Get admin activity summary"""
    try:
        hours = int(request.args.get('hours', 24))
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with SessionLocal() as session:
            # Get activity by admin
            activity_query = session.query(
                AuditLog.actor_id,
                func.count(AuditLog.id).label('action_count'),
                func.max(AuditLog.created_at).label('last_activity'),
                func.count(
                    func.nullif(AuditLog.details.op('->>')('sensitive'), None)
                ).label('sensitive_actions')
            ).filter(
                AuditLog.actor_type == 'admin',
                AuditLog.created_at >= cutoff_time,
                AuditLog.actor_id.isnot(None)
            ).group_by(AuditLog.actor_id).all()
            
            # Get admin details
            admin_ids = [activity.actor_id for activity in activity_query]
            admins = session.query(Admin).filter(Admin.id.in_(admin_ids)).all()
            admin_map = {admin.id: admin for admin in admins}
            
            # Format activity data
            admin_activity = []
            for activity in activity_query:
                admin = admin_map.get(activity.actor_id)
                if admin:
                    admin_activity.append({
                        'admin_id': activity.actor_id,
                        'admin_email': admin.email,
                        'admin_username': admin.username,
                        'is_super_admin': admin.is_super_admin,
                        'action_count': activity.action_count,
                        'sensitive_actions': activity.sensitive_actions,
                        'last_activity': activity.last_activity.isoformat(),
                        'is_active': admin.is_active
                    })
            
            # Sort by activity level
            admin_activity.sort(key=lambda x: x['action_count'], reverse=True)
            
            return jsonify({
                'admin_activity': admin_activity,
                'timeframe_hours': hours,
                'total_admins': len(admin_activity)
            })
            
    except Exception as e:
        logger.error(f"Error getting admin activity: {e}")
        return jsonify({'error': 'Failed to retrieve admin activity'}), 500

@admin_security_bp.route('/admin-sessions', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.ADMIN_VIEW])
def get_admin_sessions():
    """Get active admin sessions"""
    try:
        admin_id = request.args.get('admin_id', type=int)
        
        if admin_id:
            # Get sessions for specific admin
            sessions = session_manager.get_admin_sessions(admin_id)
        else:
            # Get all active sessions (super admin only)
            if not g.is_super_admin:
                return jsonify({'error': 'Super admin access required'}), 403
            
            # This would require extending session_manager to get all sessions
            # For now, return empty list with note
            sessions = []
        
        session_data = []
        for session in sessions:
            session_data.append({
                'session_id': session.session_id,
                'admin_id': session.admin_id,
                'admin_email': session.admin_email,
                'admin_username': session.admin_username,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent[:100] + '...' if len(session.user_agent) > 100 else session.user_agent,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'expires_at': session.expires_at.isoformat(),
                'is_active': session.is_active
            })
        
        return jsonify({
            'sessions': session_data,
            'count': len(session_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting admin sessions: {e}")
        return jsonify({'error': 'Failed to retrieve admin sessions'}), 500

# === RATE LIMITING MANAGEMENT ===

@admin_security_bp.route('/rate-limits/<identifier>', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_CONFIG])
def get_rate_limit_info(identifier):
    """Get rate limit status for an identifier"""
    try:
        status = get_rate_limit_status(identifier)
        return jsonify({
            'identifier': identifier,
            'rate_limits': status
        })
        
    except Exception as e:
        logger.error(f"Error getting rate limit info: {e}")
        return jsonify({'error': 'Failed to retrieve rate limit info'}), 500

@admin_security_bp.route('/rate-limits/<identifier>/reset', methods=['POST'])
@super_admin_only
def reset_rate_limit_endpoint(identifier):
    """Reset rate limits for an identifier (super admin only)"""
    try:
        if not g.is_super_admin:
            return jsonify({'error': 'Super admin access required'}), 403
        
        data = request.get_json() or {}
        limit_type = data.get('limit_type')  # Optional: reset specific limit type
        
        success = reset_rate_limit(identifier, limit_type)
        
        if success:
            # Log the action
            AdminAuditLogger.log_admin_action(
                'rate_limit_reset',
                details={
                    'identifier': identifier,
                    'limit_type': limit_type,
                    'reset_by_admin': g.admin_id
                }
            )
            
            return jsonify({
                'success': True,
                'message': f'Rate limits reset for {identifier}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reset rate limits'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resetting rate limits: {e}")
        return jsonify({'error': 'Failed to reset rate limits'}), 500

# === IP ACCESS CONTROL ===

@admin_security_bp.route('/ip-access-control', methods=['GET'])
@super_admin_only
def get_ip_access_control():
    """Get current IP access control configuration"""
    try:
        if not g.is_super_admin:
            return jsonify({'error': 'Super admin access required'}), 403
        
        config = ip_access_control.get_access_lists()
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting IP access control: {e}")
        return jsonify({'error': 'Failed to retrieve IP access control'}), 500

@admin_security_bp.route('/ip-access-control/allowlist', methods=['POST'])
@super_admin_only
def add_to_ip_allowlist():
    """Add IP/network to allowlist (super admin only)"""
    try:
        if not g.is_super_admin:
            return jsonify({'error': 'Super admin access required'}), 403
        
        data = request.get_json()
        if not data or 'ip_or_network' not in data:
            return jsonify({'error': 'ip_or_network is required'}), 400
        
        ip_or_network = data['ip_or_network']
        success = ip_access_control.add_to_allowlist(ip_or_network)
        
        if success:
            AdminAuditLogger.log_admin_action(
                'ip_allowlist_add',
                details={
                    'ip_or_network': ip_or_network,
                    'added_by_admin': g.admin_id
                }
            )
            
            return jsonify({
                'success': True,
                'message': f'Added {ip_or_network} to allowlist'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add to allowlist (invalid format or already exists)'
            }), 400
            
    except Exception as e:
        logger.error(f"Error adding to IP allowlist: {e}")
        return jsonify({'error': 'Failed to add to allowlist'}), 500

@admin_security_bp.route('/ip-access-control/blocklist', methods=['POST'])
@super_admin_only
def add_to_ip_blocklist():
    """Add IP/network to blocklist (super admin only)"""
    try:
        if not g.is_super_admin:
            return jsonify({'error': 'Super admin access required'}), 403
        
        data = request.get_json()
        if not data or 'ip_or_network' not in data:
            return jsonify({'error': 'ip_or_network is required'}), 400
        
        ip_or_network = data['ip_or_network']
        success = ip_access_control.add_to_blocklist(ip_or_network)
        
        if success:
            AdminAuditLogger.log_admin_action(
                'ip_blocklist_add',
                details={
                    'ip_or_network': ip_or_network,
                    'added_by_admin': g.admin_id
                }
            )
            
            return jsonify({
                'success': True,
                'message': f'Added {ip_or_network} to blocklist'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add to blocklist (invalid format or already exists)'
            }), 400
            
    except Exception as e:
        logger.error(f"Error adding to IP blocklist: {e}")
        return jsonify({'error': 'Failed to add to blocklist'}), 500

# === SECURITY DASHBOARD ===

@admin_security_bp.route('/dashboard', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.SYSTEM_HEALTH])
def get_security_dashboard():
    """Get security dashboard overview"""
    try:
        hours = int(request.args.get('hours', 24))
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with SessionLocal() as session:
            # Get security metrics
            total_admin_actions = session.query(AuditLog).filter(
                AuditLog.actor_type == 'admin',
                AuditLog.created_at >= cutoff_time
            ).count()
            
            failed_logins = session.query(AuditLog).filter(
                AuditLog.actor_type == 'admin',
                AuditLog.action == 'admin_login_failed',
                AuditLog.created_at >= cutoff_time
            ).count()
            
            sensitive_actions = session.query(AuditLog).filter(
                AuditLog.actor_type == 'admin',
                AuditLog.details.op('->>')('sensitive') == 'true',
                AuditLog.created_at >= cutoff_time
            ).count()
            
            unique_admin_ips = session.query(
                func.count(func.distinct(AuditLog.ip_address))
            ).filter(
                AuditLog.actor_type == 'admin',
                AuditLog.created_at >= cutoff_time
            ).scalar()
            
            active_admins = session.query(
                func.count(func.distinct(AuditLog.actor_id))
            ).filter(
                AuditLog.actor_type == 'admin',
                AuditLog.created_at >= cutoff_time,
                AuditLog.actor_id.isnot(None)
            ).scalar()
        
        # Get recent security events
        recent_events = AdminAuditLogger.get_security_events(hours=6)  # Last 6 hours
        
        return jsonify({
            'timeframe_hours': hours,
            'metrics': {
                'total_admin_actions': total_admin_actions,
                'failed_logins': failed_logins,
                'sensitive_actions': sensitive_actions,
                'unique_admin_ips': unique_admin_ips,
                'active_admins': active_admins
            },
            'recent_security_events': recent_events[:10],  # Last 10 events
            'ip_access_control': ip_access_control.get_access_lists()
        })
        
    except Exception as e:
        logger.error(f"Error getting security dashboard: {e}")
        return jsonify({'error': 'Failed to retrieve security dashboard'}), 500
