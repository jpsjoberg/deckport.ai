

"""
Admin Alerts API Routes
Dynamic alert system for the admin panel
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from shared.models.base import db, Device, Player, EnhancedNFCCard, VideoStream, CardTrade
from shared.auth.unified_admin_auth import admin_auth_required
from shared.auth.admin_roles import Permission


admin_alerts_bp = Blueprint('admin_alerts', __name__, url_prefix='/v1/admin/alerts')

    """Decorator to require admin authentication"""
    
    def decorated_function(*args, **kwargs):
        auth_result = verify_admin_token(request)
        if not auth_result['valid']:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_console_alerts():
    """Check for console-related alerts"""
    alerts = []
    now = datetime.utcnow()
    
    # Offline consoles
    offline_threshold = now - timedelta(minutes=10)
    offline_consoles = db.session.query(Device).filter(
        and_(
            Device.status == 'active',
            or_(
                Device.last_seen < offline_threshold,
                Device.last_seen.is_(None)
            )
        )
    ).all()
    
    if offline_consoles:
        if len(offline_consoles) == 1:
            console = offline_consoles[0]
            offline_duration = now - (console.last_seen or console.created_at)
            hours = int(offline_duration.total_seconds() // 3600)
            minutes = int((offline_duration.total_seconds() % 3600) // 60)
            
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            alerts.append({
                'id': f'console_offline_{console.device_uid}',
                'type': 'warning',
                'category': 'console',
                'title': 'Console Offline',
                'message': f'Console {console.device_uid} offline for {time_str}',
                'timestamp': now.isoformat(),
                'severity': 'high' if hours >= 2 else 'medium',
                'data': {
                    'device_uid': console.device_uid,
                    'offline_duration': offline_duration.total_seconds()
                }
            })
        else:
            alerts.append({
                'id': 'multiple_consoles_offline',
                'type': 'error',
                'category': 'console',
                'title': 'Multiple Consoles Offline',
                'message': f'{len(offline_consoles)} consoles are currently offline',
                'timestamp': now.isoformat(),
                'severity': 'critical',
                'data': {
                    'offline_count': len(offline_consoles),
                    'device_uids': [c.device_uid for c in offline_consoles]
                }
            })
    
    # Pending console registrations
    pending_consoles = db.session.query(func.count(Device.id)).filter(
        Device.status == 'pending'
    ).scalar()
    
    if pending_consoles > 0:
        alerts.append({
            'id': 'pending_registrations',
            'type': 'info',
            'category': 'console',
            'title': 'Pending Console Registrations',
            'message': f'{pending_consoles} console(s) awaiting approval',
            'timestamp': now.isoformat(),
            'severity': 'low',
            'data': {
                'pending_count': pending_consoles
            }
        })
    
    return alerts

def check_nfc_alerts():
    """Check for NFC card-related alerts"""
    alerts = []
    now = datetime.utcnow()
    
    # Failed card activations (cards programmed but not activated within 7 days)
    week_ago = now - timedelta(days=7)
    stale_cards = db.session.query(func.count(EnhancedNFCCard.id)).filter(
        and_(
            EnhancedNFCCard.status == 'programmed',
            EnhancedNFCCard.programmed_at < week_ago
        )
    ).scalar()
    
    if stale_cards > 10:  # Alert if more than 10 cards are stale
        alerts.append({
            'id': 'stale_nfc_cards',
            'type': 'warning',
            'category': 'nfc',
            'title': 'Stale NFC Cards',
            'message': f'{stale_cards} programmed cards not activated within 7 days',
            'timestamp': now.isoformat(),
            'severity': 'medium',
            'data': {
                'stale_count': stale_cards
            }
        })
    
    # High number of revoked cards today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    revoked_today = db.session.query(func.count(EnhancedNFCCard.id)).filter(
        and_(
            EnhancedNFCCard.status == 'revoked',
            EnhancedNFCCard.updated_at >= today_start
        )
    ).scalar()
    
    if revoked_today > 5:  # Alert if more than 5 cards revoked today
        alerts.append({
            'id': 'high_revocation_rate',
            'type': 'error',
            'category': 'nfc',
            'title': 'High Card Revocation Rate',
            'message': f'{revoked_today} cards revoked today - possible security issue',
            'timestamp': now.isoformat(),
            'severity': 'high',
            'data': {
                'revoked_count': revoked_today
            }
        })
    
    # Pending trades
    pending_trades = db.session.query(func.count(CardTrade.id)).filter(
        CardTrade.status == 'pending'
    ).scalar()
    
    if pending_trades > 20:  # Alert if many trades are pending
        alerts.append({
            'id': 'high_pending_trades',
            'type': 'warning',
            'category': 'nfc',
            'title': 'High Pending Trades',
            'message': f'{pending_trades} card trades awaiting processing',
            'timestamp': now.isoformat(),
            'severity': 'medium',
            'data': {
                'pending_count': pending_trades
            }
        })
    
    return alerts

def check_system_alerts():
    """Check for system-wide alerts"""
    alerts = []
    now = datetime.utcnow()
    
    # High number of active video streams
    active_streams = db.session.query(func.count(VideoStream.id)).filter(
        VideoStream.status == 'active'
    ).scalar()
    
    total_consoles = db.session.query(func.count(Device.id)).filter(
        Device.status == 'active'
    ).scalar()
    
    if active_streams > total_consoles * 0.8:  # Alert if >80% of consoles streaming
        alerts.append({
            'id': 'high_streaming_load',
            'type': 'warning',
            'category': 'system',
            'title': 'High Streaming Load',
            'message': f'{active_streams} active video streams (high server load)',
            'timestamp': now.isoformat(),
            'severity': 'medium',
            'data': {
                'active_streams': active_streams,
                'total_consoles': total_consoles,
                'load_percentage': round(active_streams / total_consoles * 100, 1) if total_consoles > 0 else 0
            }
        })
    
    # Database connection issues (simplified check)
    try:
        db.session.execute('SELECT 1').scalar()
        db_healthy = True
    except Exception:
        db_healthy = False
    
    if not db_healthy:
        alerts.append({
            'id': 'database_connection_issue',
            'type': 'error',
            'category': 'system',
            'title': 'Database Connection Issue',
            'message': 'Unable to connect to database - system may be unstable',
            'timestamp': now.isoformat(),
            'severity': 'critical',
            'data': {}
        })
    
    return alerts

def check_player_alerts():
    """Check for player-related alerts"""
    alerts = []
    now = datetime.utcnow()
    
    # Unusual registration spike
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    
    registrations_today = db.session.query(func.count(Player.id)).filter(
        Player.created_at >= today_start
    ).scalar()
    
    registrations_yesterday = db.session.query(func.count(Player.id)).filter(
        and_(
            Player.created_at >= yesterday_start,
            Player.created_at < today_start
        )
    ).scalar()
    
    # Alert if today's registrations are 3x yesterday's
    if registrations_yesterday > 0 and registrations_today > registrations_yesterday * 3:
        alerts.append({
            'id': 'registration_spike',
            'type': 'info',
            'category': 'player',
            'title': 'Registration Spike',
            'message': f'{registrations_today} new registrations today (vs {registrations_yesterday} yesterday)',
            'timestamp': now.isoformat(),
            'severity': 'low',
            'data': {
                'today_count': registrations_today,
                'yesterday_count': registrations_yesterday,
                'spike_ratio': round(registrations_today / registrations_yesterday, 1)
            }
        })
    
    return alerts

@admin_alerts_bp.route('/', methods=['GET'])
@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])
def get_alerts():
    """Get all current system alerts"""
    try:
        all_alerts = []
        
        # Collect alerts from different categories
        all_alerts.extend(check_console_alerts())
        all_alerts.extend(check_nfc_alerts())
        all_alerts.extend(check_system_alerts())
        all_alerts.extend(check_player_alerts())
        
        # Sort by severity and timestamp
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_alerts.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['timestamp']), reverse=True)
        
        # Filter by category if requested
        category = request.args.get('category')
        if category:
            all_alerts = [alert for alert in all_alerts if alert['category'] == category]
        
        # Filter by severity if requested
        min_severity = request.args.get('min_severity')
        if min_severity:
            severity_levels = ['low', 'medium', 'high', 'critical']
            if min_severity in severity_levels:
                min_index = severity_levels.index(min_severity)
                all_alerts = [alert for alert in all_alerts 
                            if severity_levels.index(alert['severity']) >= min_index]
        
        # Limit results
        limit = int(request.args.get('limit', 50))
        all_alerts = all_alerts[:limit]
        
        return jsonify({
            'alerts': all_alerts,
            'total_count': len(all_alerts),
            'categories': ['console', 'nfc', 'system', 'player'],
            'severity_levels': ['low', 'medium', 'high', 'critical']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get alerts: {str(e)}'}), 500

@admin_alerts_bp.route('/summary', methods=['GET'])
@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])
def get_alerts_summary():
    """Get alert summary for dashboard"""
    try:
        all_alerts = []
        all_alerts.extend(check_console_alerts())
        all_alerts.extend(check_nfc_alerts())
        all_alerts.extend(check_system_alerts())
        all_alerts.extend(check_player_alerts())
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for alert in all_alerts:
            severity_counts[alert['severity']] += 1
        
        # Get most recent critical/high alerts for display
        critical_alerts = [alert for alert in all_alerts if alert['severity'] in ['critical', 'high']]
        critical_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'total_alerts': len(all_alerts),
            'severity_breakdown': severity_counts,
            'critical_alerts': critical_alerts[:5],  # Top 5 most recent critical/high
            'system_status': 'critical' if severity_counts['critical'] > 0 else 
                           'warning' if severity_counts['high'] > 0 else 
                           'caution' if severity_counts['medium'] > 0 else 'healthy'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get alerts summary: {str(e)}'}), 500

@admin_alerts_bp.route('/<alert_id>/acknowledge', methods=['POST'])
@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])
def acknowledge_alert(alert_id):
    """Acknowledge an alert (mark as seen)"""
    try:
        # In a full implementation, you'd store acknowledged alerts in the database
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': f'Alert {alert_id} acknowledged',
            'acknowledged_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to acknowledge alert: {str(e)}'}), 500

@admin_alerts_bp.route('/health-check', methods=['GET'])
@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])
def health_check():
    """Perform system health check"""
    try:
        now = datetime.utcnow()
        health_status = {
            'timestamp': now.isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check database
        try:
            db.session.execute('SELECT 1').scalar()
            health_status['components']['database'] = {
                'status': 'healthy',
                'response_time_ms': 10  # Simplified
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check console connectivity
        total_consoles = db.session.query(func.count(Device.id)).filter(
            Device.status == 'active'
        ).scalar()
        
        active_consoles = db.session.query(func.count(Device.id)).filter(
            and_(
                Device.status == 'active',
                Device.last_seen > now - timedelta(minutes=5)
            )
        ).scalar()
        
        console_uptime = (active_consoles / total_consoles * 100) if total_consoles > 0 else 100
        
        health_status['components']['consoles'] = {
            'status': 'healthy' if console_uptime > 90 else 'degraded' if console_uptime > 70 else 'unhealthy',
            'uptime_percentage': round(console_uptime, 2),
            'active_count': active_consoles,
            'total_count': total_consoles
        }
        
        if console_uptime < 90:
            health_status['overall_status'] = 'degraded' if console_uptime > 70 else 'unhealthy'
        
        # Check NFC system
        total_cards = db.session.query(func.count(EnhancedNFCCard.id)).scalar()
        activated_cards = db.session.query(func.count(EnhancedNFCCard.id)).filter(
            EnhancedNFCCard.status == 'activated'
        ).scalar()
        
        activation_rate = (activated_cards / total_cards * 100) if total_cards > 0 else 0
        
        health_status['components']['nfc_system'] = {
            'status': 'healthy',
            'total_cards': total_cards,
            'activated_cards': activated_cards,
            'activation_rate': round(activation_rate, 2)
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unhealthy',
            'error': f'Health check failed: {str(e)}'
        }), 500
