"""
Console logging routes - receives real-time logs from consoles
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from shared.database.connection import SessionLocal
from shared.models.base import AuditLog
import json

console_logs_bp = Blueprint('console_logs', __name__, url_prefix='/v1/console')

@console_logs_bp.route('/logs', methods=['POST'])
def receive_console_logs():
    """Receive real-time logs from console"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    device_id = data.get('device_id', 'unknown')
    logs = data.get('logs', [])
    
    if not logs:
        return jsonify({"error": "No logs provided"}), 400
    
    try:
        with SessionLocal() as session:
            # Store each log entry
            for log_entry in logs:
                # Store log using AuditLog model
                audit_log = AuditLog(
                    actor_type="console",
                    actor_id=None,  # Console ID would go here when available
                    action=f"{log_entry.get('component', 'unknown')}.{log_entry.get('message', 'unknown')}",
                    details={
                        'device_id': device_id,
                        'level': log_entry.get('level', 'INFO'),
                        'component': log_entry.get('component', 'unknown'),
                        'message': log_entry.get('message', ''),
                        'data': log_entry.get('data', {}),
                        'session_id': log_entry.get('session_id', ''),
                        'console_timestamp': log_entry.get('timestamp', '')
                    },
                    created_at=datetime.now(timezone.utc)
                )
                session.add(audit_log)
            
            session.commit()
            
            return jsonify({
                "status": "success",
                "logs_received": len(logs),
                "device_id": device_id
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to store logs"}), 500

@console_logs_bp.route('/logs/<device_id>', methods=['GET'])
def get_console_logs(device_id):
    """Get logs for a specific console (for monitoring)"""
    try:
        with SessionLocal() as session:
            # Get recent logs for this device (search in details field)
            logs = session.query(AuditLog).filter(
                AuditLog.actor_type == "console"
            ).order_by(AuditLog.created_at.desc()).limit(100).all()
            
            # Filter by device_id in details
            device_logs = []
            for log in logs:
                if log.details and log.details.get('device_id') == device_id:
                    device_logs.append(log)
            
            log_data = []
            for log in device_logs:
                log_data.append({
                    "id": log.id,
                    "timestamp": log.created_at.isoformat(),
                    "action": log.action,
                    "details": log.details
                })
            
            return jsonify({
                "device_id": device_id,
                "logs": log_data,
                "total": len(log_data)
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to retrieve logs"}), 500

@console_logs_bp.route('/devices', methods=['GET'])
def get_active_devices():
    """Get list of active console devices"""
    try:
        with SessionLocal() as session:
            # Get devices that have logged activity in the last 24 hours
            recent_logs = session.query(AuditLog).filter(
                AuditLog.actor_type == "console",
                AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).all()
            
            devices = set()
            for log in recent_logs:
                if log.details and log.details.get('device_id'):
                    devices.add(log.details['device_id'])
            
            devices = list(devices)
            
            return jsonify({
                "active_devices": devices,
                "total": len(devices)
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to retrieve devices"}), 500
