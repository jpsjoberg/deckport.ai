"""
Admin device management routes
Handles console fleet management, approval, and remote operations
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc
from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleStatus, AuditLog
from shared.auth.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

admin_devices_bp = Blueprint('admin_devices', __name__, url_prefix='/v1/admin/devices')

@admin_devices_bp.route('', methods=['GET'])
@admin_required
def get_devices():
    """Get list of console devices with optional filtering"""
    try:
        status_filter = request.args.get('status')
        location_filter = request.args.get('location')
        
        with SessionLocal() as session:
            query = session.query(Console)
            
            # Apply status filter
            if status_filter:
                if status_filter == 'pending':
                    query = query.filter(Console.status == ConsoleStatus.pending)
                elif status_filter == 'active':
                    query = query.filter(Console.status == ConsoleStatus.active)
                elif status_filter == 'revoked':
                    query = query.filter(Console.status == ConsoleStatus.revoked)
            
            consoles = query.order_by(desc(Console.registered_at)).all()
            
            # Enrich with additional data
            devices = []
            for console in consoles:
                # Get last seen information from audit logs
                last_log = session.query(AuditLog).filter(
                    AuditLog.actor_type == "console",
                    AuditLog.meta.op('->>')('device_id') == str(console.id)
                ).order_by(desc(AuditLog.created_at)).first()
                
                last_seen = None
                last_seen_minutes = None
                if last_log:
                    last_seen = last_log.created_at.isoformat()
                    last_seen_minutes = int((datetime.now(timezone.utc) - last_log.created_at).total_seconds() / 60)
                
                # Determine online status
                is_online = last_seen_minutes is not None and last_seen_minutes < 5
                
                device_data = {
                    'id': console.id,
                    'device_uid': console.device_uid,
                    'status': console.status.value,
                    'registered_at': console.registered_at.isoformat(),
                    'last_seen': last_seen,
                    'last_seen_minutes': last_seen_minutes,
                    'is_online': is_online,
                    'owner_player_id': console.owner_player_id,
                    'public_key_fingerprint': console.public_key_pem[-12:] if console.public_key_pem else None,
                    # Mock additional data for now
                    'location': 'Unknown',  # TODO: Add location tracking
                    'current_player': None,  # TODO: Get from active sessions
                    'uptime_7d': 95.0 + (console.id % 10),  # Mock uptime
                    'version': '1.0.0',  # TODO: Track console versions
                }
                
                devices.append(device_data)
            
            return jsonify({
                'devices': devices,
                'total': len(devices)
            })
            
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'error': 'Failed to retrieve devices'}), 500

@admin_devices_bp.route('/<device_uid>', methods=['GET'])
@admin_required
def get_device_detail(device_uid):
    """Get detailed information about a specific console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get recent logs for this device
            recent_logs = session.query(AuditLog).filter(
                AuditLog.actor_type == "console",
                AuditLog.meta.op('->>')('device_id') == str(console.id),
                AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).order_by(desc(AuditLog.created_at)).limit(50).all()
            
            logs = []
            for log in recent_logs:
                logs.append({
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'details': log.details,
                    'meta': log.meta
                })
            
            # Calculate uptime and statistics
            total_logs = len(recent_logs)
            error_logs = len([log for log in recent_logs if 'error' in log.action.lower()])
            
            device_detail = {
                'id': console.id,
                'device_uid': console.device_uid,
                'status': console.status.value,
                'registered_at': console.registered_at.isoformat(),
                'owner_player_id': console.owner_player_id,
                'public_key_fingerprint': console.public_key_pem[-12:] if console.public_key_pem else None,
                'recent_logs': logs,
                'statistics': {
                    'total_logs_24h': total_logs,
                    'error_logs_24h': error_logs,
                    'success_rate': ((total_logs - error_logs) / total_logs * 100) if total_logs > 0 else 100,
                    'uptime_24h': 95.0 + (console.id % 10),  # Mock uptime
                },
                # Mock additional data
                'location': 'Unknown',
                'hardware_info': {
                    'cpu_usage': 45.2,
                    'memory_usage': 62.1,
                    'disk_usage': 78.9,
                    'temperature': 42.5
                },
                'network_info': {
                    'ip_address': '192.168.1.100',
                    'connection_type': 'ethernet',
                    'signal_strength': 100
                }
            }
            
            return jsonify(device_detail)
            
    except Exception as e:
        logger.error(f"Error getting device detail: {e}")
        return jsonify({'error': 'Failed to retrieve device details'}), 500

@admin_devices_bp.route('/<device_uid>/approve', methods=['POST'])
@admin_required
def approve_device(device_uid):
    """Approve a pending console registration"""
    try:
        data = request.get_json() or {}
        approved = data.get('approved', True)
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            if console.status != ConsoleStatus.pending:
                return jsonify({'error': 'Console is not pending approval'}), 400
            
            if approved:
                console.status = ConsoleStatus.active
                
                # Log the approval
                audit_log = AuditLog(
                    actor_type="admin",
                    actor_id=1,  # TODO: Get actual admin ID from JWT
                    action="console_approved",
                    details=f"Console {device_uid} approved by admin",
                    meta={'device_uid': device_uid, 'device_id': console.id}
                )
                session.add(audit_log)
                
                session.commit()
                
                return jsonify({
                    'status': 'approved',
                    'message': f'Console {device_uid} has been approved'
                })
            else:
                console.status = ConsoleStatus.revoked
                
                # Log the rejection
                audit_log = AuditLog(
                    actor_type="admin",
                    actor_id=1,  # TODO: Get actual admin ID from JWT
                    action="console_rejected",
                    details=f"Console {device_uid} rejected by admin",
                    meta={'device_uid': device_uid, 'device_id': console.id}
                )
                session.add(audit_log)
                
                session.commit()
                
                return jsonify({
                    'status': 'rejected',
                    'message': f'Console {device_uid} has been rejected'
                })
                
    except Exception as e:
        logger.error(f"Error approving device: {e}")
        return jsonify({'error': 'Failed to approve device'}), 500

@admin_devices_bp.route('/<device_uid>/reject', methods=['POST'])
@admin_required
def reject_device(device_uid):
    """Reject a pending console registration"""
    return approve_device(device_uid)  # Same logic with approved=False

@admin_devices_bp.route('/<device_uid>/reboot', methods=['POST'])
@admin_required
def reboot_device(device_uid):
    """Send reboot command to console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            if console.status != ConsoleStatus.active:
                return jsonify({'error': 'Console is not active'}), 400
            
            # TODO: Implement actual remote reboot via WebSocket or message queue
            # For now, just log the command
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="console_reboot_command",
                details=f"Reboot command sent to console {device_uid}",
                meta={'device_uid': device_uid, 'device_id': console.id}
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Reboot command sent to {device_uid}'
            })
            
    except Exception as e:
        logger.error(f"Error rebooting device: {e}")
        return jsonify({'error': 'Failed to send reboot command'}), 500

@admin_devices_bp.route('/<device_uid>/shutdown', methods=['POST'])
@admin_required
def shutdown_device(device_uid):
    """Send shutdown command to console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            if console.status != ConsoleStatus.active:
                return jsonify({'error': 'Console is not active'}), 400
            
            # TODO: Implement actual remote shutdown via WebSocket or message queue
            # For now, just log the command
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="console_shutdown_command",
                details=f"Shutdown command sent to console {device_uid}",
                meta={'device_uid': device_uid, 'device_id': console.id}
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Shutdown command sent to {device_uid}'
            })
            
    except Exception as e:
        logger.error(f"Error shutting down device: {e}")
        return jsonify({'error': 'Failed to send shutdown command'}), 500

@admin_devices_bp.route('/<device_uid>/ping', methods=['POST'])
@admin_required
def ping_device(device_uid):
    """Send ping to offline console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # TODO: Implement actual ping via WebSocket or message queue
            # For now, just log the ping attempt
            audit_log = AuditLog(
                actor_type="admin",
                actor_id=1,  # TODO: Get actual admin ID from JWT
                action="console_ping_command",
                details=f"Ping sent to console {device_uid}",
                meta={'device_uid': device_uid, 'device_id': console.id}
            )
            session.add(audit_log)
            session.commit()
            
            # Mock ping response (in real implementation, this would wait for actual response)
            import random
            success = random.choice([True, False, True, True])  # 75% success rate
            
            return jsonify({
                'success': success,
                'message': f'Ping {"successful" if success else "failed"} for {device_uid}',
                'response_time': round(random.uniform(10, 100), 2) if success else None
            })
            
    except Exception as e:
        logger.error(f"Error pinging device: {e}")
        return jsonify({'error': 'Failed to ping device'}), 500

@admin_devices_bp.route('/<device_uid>/status', methods=['GET'])
@admin_required
def get_device_status(device_uid):
    """Get real-time status of a specific console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get most recent activity
            last_log = session.query(AuditLog).filter(
                AuditLog.actor_type == "console",
                AuditLog.meta.op('->>')('device_id') == str(console.id)
            ).order_by(desc(AuditLog.created_at)).first()
            
            last_seen = None
            last_seen_minutes = None
            if last_log:
                last_seen = last_log.created_at.isoformat()
                last_seen_minutes = int((datetime.now(timezone.utc) - last_log.created_at).total_seconds() / 60)
            
            is_online = last_seen_minutes is not None and last_seen_minutes < 5
            
            status = {
                'device_uid': device_uid,
                'status': console.status.value,
                'is_online': is_online,
                'last_seen': last_seen,
                'last_seen_minutes': last_seen_minutes,
                'registered_at': console.registered_at.isoformat(),
                # Mock real-time data
                'current_player': None,
                'active_session': None,
                'system_health': {
                    'cpu_usage': round(random.uniform(20, 80), 1),
                    'memory_usage': round(random.uniform(40, 90), 1),
                    'disk_usage': round(random.uniform(60, 95), 1),
                    'temperature': round(random.uniform(35, 50), 1)
                }
            }
            
            return jsonify(status)
            
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        return jsonify({'error': 'Failed to get device status'}), 500

@admin_devices_bp.route('/<device_uid>/logs', methods=['GET'])
@admin_required
def get_device_logs(device_uid):
    """Get logs for a specific console"""
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        hours = int(request.args.get('hours', 24))
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get logs for this device
            logs_query = session.query(AuditLog).filter(
                AuditLog.actor_type == "console",
                AuditLog.meta.op('->>')('device_id') == str(console.id),
                AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=hours)
            ).order_by(desc(AuditLog.created_at)).limit(limit)
            
            logs = []
            for log in logs_query:
                logs.append({
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'details': log.details,
                    'meta': log.meta
                })
            
            return jsonify({
                'logs': logs,
                'total': len(logs),
                'device_uid': device_uid,
                'hours': hours
            })
            
    except Exception as e:
        logger.error(f"Error getting device logs: {e}")
        return jsonify({'error': 'Failed to retrieve device logs'}), 500

@admin_devices_bp.route('/<device_uid>/diagnostics', methods=['GET'])
@admin_required
def get_device_diagnostics(device_uid):
    """Get diagnostic information for a specific console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Mock diagnostic data (in real implementation, this would come from the console)
            import random
            
            diagnostics = {
                'device_uid': device_uid,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_info': {
                    'os': 'Ubuntu 22.04 LTS',
                    'kernel': '5.15.0-71-generic',
                    'architecture': 'x86_64',
                    'uptime_seconds': random.randint(3600, 604800),  # 1 hour to 1 week
                },
                'hardware': {
                    'cpu_model': 'Intel Core i5-10400',
                    'cpu_cores': 6,
                    'cpu_usage_percent': round(random.uniform(20, 80), 1),
                    'memory_total_gb': 16,
                    'memory_used_gb': round(random.uniform(6, 12), 1),
                    'disk_total_gb': 500,
                    'disk_used_gb': round(random.uniform(200, 400), 1),
                    'temperature_celsius': round(random.uniform(35, 50), 1),
                },
                'network': {
                    'interface': 'eth0',
                    'ip_address': f'192.168.1.{random.randint(100, 200)}',
                    'connection_type': 'ethernet',
                    'speed_mbps': 1000,
                    'bytes_sent': random.randint(1000000, 10000000),
                    'bytes_received': random.randint(5000000, 50000000),
                },
                'services': {
                    'godot_engine': 'running',
                    'nfc_reader': 'running',
                    'api_client': 'running',
                    'video_player': 'running',
                },
                'health_checks': {
                    'api_connectivity': random.choice(['healthy', 'healthy', 'warning']),
                    'database_connectivity': 'healthy',
                    'nfc_reader_status': random.choice(['healthy', 'healthy', 'error']),
                    'display_output': 'healthy',
                    'audio_output': 'healthy',
                }
            }
            
            return jsonify({'diagnostics': diagnostics})
            
    except Exception as e:
        logger.error(f"Error getting device diagnostics: {e}")
        return jsonify({'error': 'Failed to retrieve device diagnostics'}), 500
