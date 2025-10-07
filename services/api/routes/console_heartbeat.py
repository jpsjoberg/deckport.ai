"""
Console Heartbeat API Routes
Handles real-time health monitoring and status updates from consoles
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from shared.database.connection import SessionLocal
from shared.models.base import Console, AuditLog
from shared.auth.decorators import device_required
import logging

logger = logging.getLogger(__name__)

console_heartbeat_bp = Blueprint('console_heartbeat', __name__, url_prefix='/v1/console')

@console_heartbeat_bp.route('/heartbeat', methods=['POST'])
@device_required
def console_heartbeat():
    """Receive heartbeat and health data from console"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        device_uid = data.get('device_uid')
        if not device_uid:
            return jsonify({'error': 'Device UID required'}), 400
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Update console health data (using setattr for compatibility)
            current_time = datetime.now(timezone.utc)
            
            # Basic heartbeat
            setattr(console, 'last_heartbeat', current_time)
            
            # Health status
            health_status = data.get('health_status', 'unknown')
            setattr(console, 'health_status', health_status)
            
            # Performance metrics
            if 'uptime_seconds' in data:
                setattr(console, 'uptime_seconds', int(data['uptime_seconds']))
            if 'cpu_usage_percent' in data:
                setattr(console, 'cpu_usage_percent', float(data['cpu_usage_percent']))
            if 'memory_usage_percent' in data:
                setattr(console, 'memory_usage_percent', float(data['memory_usage_percent']))
            if 'disk_usage_percent' in data:
                setattr(console, 'disk_usage_percent', float(data['disk_usage_percent']))
            if 'temperature_celsius' in data:
                setattr(console, 'temperature_celsius', float(data['temperature_celsius']))
            if 'network_latency_ms' in data:
                setattr(console, 'network_latency_ms', float(data['network_latency_ms']))
            
            # Battery information (new)
            if 'battery' in data:
                battery_data = data['battery']
                setattr(console, 'battery_capacity_percent', battery_data.get('capacity_percent', 100))
                setattr(console, 'battery_status', battery_data.get('status', 'AC_Power'))
                setattr(console, 'battery_present', battery_data.get('present', 0))
                setattr(console, 'battery_voltage_mv', battery_data.get('voltage_mv', 0))
                setattr(console, 'battery_current_ma', battery_data.get('current_ma', 0))
                setattr(console, 'power_consumption_watts', battery_data.get('power_consumption_watts', 0))
                setattr(console, 'battery_time_remaining_minutes', battery_data.get('time_remaining_minutes', 0))
                setattr(console, 'ac_connected', battery_data.get('ac_connected', 1))
            
            # Camera information (new)
            if 'camera' in data:
                camera_data = data['camera']
                setattr(console, 'camera_device_count', camera_data.get('device_count', 0))
                setattr(console, 'camera_status', camera_data.get('status', 'unavailable'))
                setattr(console, 'camera_working', camera_data.get('working', False))
                setattr(console, 'camera_devices', camera_data.get('devices', ''))
                setattr(console, 'surveillance_capable', camera_data.get('surveillance_capable', False))
            
            # Version information (if provided)
            if 'software_version' in data:
                setattr(console, 'software_version', data['software_version'])
            if 'firmware_version' in data:
                setattr(console, 'firmware_version', data['firmware_version'])
            if 'hardware_version' in data:
                setattr(console, 'hardware_version', data['hardware_version'])
            
            session.commit()
            
            # Create audit log entry for heartbeat
            audit_log = AuditLog(
                actor_type="console",
                actor_id=console.id,
                action="console.heartbeat",
                details={
                    'device_id': str(console.id),
                    'device_uid': device_uid,
                    'health_status': health_status,
                    'uptime_seconds': data.get('uptime_seconds'),
                    'cpu_usage_percent': data.get('cpu_usage_percent'),
                    'memory_usage_percent': data.get('memory_usage_percent'),
                    'disk_usage_percent': data.get('disk_usage_percent'),
                    'temperature_celsius': data.get('temperature_celsius'),
                    'network_latency_ms': data.get('network_latency_ms'),
                    'software_version': data.get('software_version'),
                    'firmware_version': data.get('firmware_version'),
                    'additional_data': data.get('additional_data', {})
                },
                created_at=current_time
            )
            session.add(audit_log)
            session.commit()
            
            # Determine if any updates are available (simplified logic)
            update_available = False
            latest_versions = {
                'software': '2.1.0',  # These would come from a version management system
                'firmware': '1.5.2'
            }
            
            current_software = getattr(console, 'software_version', '1.0.0')
            current_firmware = getattr(console, 'firmware_version', '1.0.0')
            
            if (current_software != latest_versions['software'] or 
                current_firmware != latest_versions['firmware']):
                update_available = True
                setattr(console, 'update_available', True)
                session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Heartbeat received',
                'server_time': current_time.isoformat(),
                'update_available': update_available,
                'latest_versions': latest_versions if update_available else None,
                'health_status': health_status,
                'next_heartbeat_seconds': 30  # Recommend heartbeat frequency
            })
            
    except Exception as e:
        logger.error(f"Error processing console heartbeat: {e}")
        return jsonify({'error': 'Failed to process heartbeat'}), 500


@console_heartbeat_bp.route('/status', methods=['POST'])
@device_required
def update_console_status():
    """Update console status and location (from console itself)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        device_uid = data.get('device_uid')
        if not device_uid:
            return jsonify({'error': 'Device UID required'}), 400
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Update location if provided (GPS from console)
            if 'location' in data:
                location_data = data['location']
                if location_data.get('latitude') and location_data.get('longitude'):
                    setattr(console, 'location_latitude', float(location_data['latitude']))
                    setattr(console, 'location_longitude', float(location_data['longitude']))
                    setattr(console, 'location_source', 'gps')
                    setattr(console, 'location_updated_at', datetime.now(timezone.utc))
            
            # Update network information
            if 'network' in data:
                network_data = data['network']
                if 'latency_ms' in network_data:
                    setattr(console, 'network_latency_ms', float(network_data['latency_ms']))
            
            session.commit()
            
            # Log status update
            audit_log = AuditLog(
                actor_type="console",
                actor_id=console.id,
                action="console.status_update",
                details={
                    'device_id': str(console.id),
                    'device_uid': device_uid,
                    'status_data': data
                },
                created_at=datetime.now(timezone.utc)
            )
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Console status updated',
                'server_time': datetime.now(timezone.utc).isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error updating console status: {e}")
        return jsonify({'error': 'Failed to update console status'}), 500
