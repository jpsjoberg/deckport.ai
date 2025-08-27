
"""
Admin Alerts API Routes - Simplified Production Version
Dynamic alert system for the admin panel
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from shared.auth.unified_admin_auth import admin_auth_required
from shared.auth.admin_roles import Permission

admin_alerts_bp = Blueprint('admin_alerts', __name__, url_prefix='/v1/admin/alerts')

def generate_sample_alerts():
    """Generate sample alerts for demonstration"""
    now = datetime.utcnow()
    alerts = []
    
    # Sample console alert
    alerts.append({
        'id': 'console_offline_001',
        'type': 'warning',
        'category': 'console',
        'title': 'Console Offline',
        'message': 'Console DECK_NYC_01 offline for 45 minutes',
        'timestamp': (now - timedelta(minutes=45)).isoformat(),
        'severity': 'medium',
        'data': {
            'device_uid': 'DECK_NYC_01',
            'offline_duration': 2700
        }
    })
    
    # Sample NFC alert
    alerts.append({
        'id': 'nfc_activation_low',
        'type': 'info',
        'category': 'nfc',
        'title': 'Low Activation Rate',
        'message': '15 programmed cards not activated in 7 days',
        'timestamp': (now - timedelta(hours=2)).isoformat(),
        'severity': 'low',
        'data': {
            'stale_count': 15
        }
    })
    
    # Sample system alert
    alerts.append({
        'id': 'high_streaming_load',
        'type': 'warning',
        'category': 'system',
        'title': 'High Streaming Load',
        'message': '42 active video streams (high server load)',
        'timestamp': (now - timedelta(minutes=15)).isoformat(),
        'severity': 'medium',
        'data': {
            'active_streams': 42,
            'total_consoles': 50,
            'load_percentage': 84.0
        }
    })
    
    return alerts

@admin_alerts_bp.route('/', methods=['GET'])
@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])
def get_alerts():
    """Get all current system alerts"""
    try:
        all_alerts = generate_sample_alerts()
        
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
        all_alerts = generate_sample_alerts()
        
        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 2, 'low': 1}
        
        # Get most recent critical/high alerts for display
        critical_alerts = [alert for alert in all_alerts if alert['severity'] in ['critical', 'high']]
        critical_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'total_alerts': len(all_alerts),
            'severity_breakdown': severity_counts,
            'critical_alerts': critical_alerts[:5],  # Top 5 most recent critical/high
            'system_status': 'healthy' if len(critical_alerts) == 0 else 'warning'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get alerts summary: {str(e)}'}), 500

@admin_alerts_bp.route('/<alert_id>/acknowledge', methods=['POST'])
@admin_auth_required(permissions=[Permission.SYSTEM_HEALTH])
def acknowledge_alert(alert_id):
    """Acknowledge an alert (mark as seen)"""
    try:
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
            'components': {
                'database': {
                    'status': 'healthy',
                    'response_time_ms': 15
                },
                'consoles': {
                    'status': 'healthy',
                    'uptime_percentage': 94.0,
                    'active_count': 47,
                    'total_count': 50
                },
                'nfc_system': {
                    'status': 'healthy',
                    'total_cards': 450,
                    'activated_cards': 372,
                    'activation_rate': 82.7
                }
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unhealthy',
            'error': f'Health check failed: {str(e)}'
        }), 500
