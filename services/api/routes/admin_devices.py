"""
Admin device management routes
Handles console fleet management, approval, and remote operations
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc
from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleStatus, AuditLog
from shared.auth.auto_rbac_decorator import auto_rbac_required, console_management_required
from shared.auth.admin_roles import Permission
from shared.auth.decorators import admin_required
import logging
from shared.auth.admin_context import log_admin_action, get_current_admin_id

logger = logging.getLogger(__name__)

admin_devices_bp = Blueprint('admin_devices', __name__, url_prefix='/v1/admin/devices')

@admin_devices_bp.route('', methods=['GET'])
@console_management_required(Permission.CONSOLE_VIEW)
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
                    AuditLog.details.op('->>')('device_id') == str(console.id)
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
@console_management_required(Permission.CONSOLE_VIEW)
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
                AuditLog.details.op('->>')('device_id') == str(console.id),
                AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).order_by(desc(AuditLog.created_at)).limit(50).all()
            
            logs = []
            for log in recent_logs:
                logs.append({
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'details': log.details
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
@console_management_required(Permission.CONSOLE_APPROVE)
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
                log_admin_action(session, "console_approved", f"Console {device_uid} approved by admin", {'message': f"Console {device_uid} approved by admin", 'device_uid': device_uid, 'device_id': console.id}
                )
                session.commit()
                
                return jsonify({
                    'status': 'approved',
                    'message': f'Console {device_uid} has been approved'
                })
            else:
                console.status = ConsoleStatus.revoked
                
                # Log the rejection
                log_admin_action(session, "console_rejected", f"Console {device_uid} rejected by admin", {'message': f"Console {device_uid} rejected by admin", 'device_uid': device_uid, 'device_id': console.id}
                )
                session.commit()
                
                return jsonify({
                    'status': 'rejected',
                    'message': f'Console {device_uid} has been rejected'
                })
                
    except Exception as e:
        logger.error(f"Error approving device: {e}")
        return jsonify({'error': 'Failed to approve device'}), 500

@admin_devices_bp.route('/<device_uid>/reject', methods=['POST'])
@console_management_required(Permission.CONSOLE_APPROVE)
def reject_device(device_uid):
    """Reject a pending console registration"""
    return approve_device(device_uid)  # Same logic with approved=False

@admin_devices_bp.route('/<device_uid>/reboot', methods=['POST'])
@console_management_required(Permission.CONSOLE_REMOTE)
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
            log_admin_action(session, "console_reboot_command", f"Console {device_uid} reboot command by admin", {'message': f"Reboot command sent to console {device_uid}", 'device_uid': device_uid, 'device_id': console.id}
            )
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Reboot command sent to {device_uid}'
            })
            
    except Exception as e:
        logger.error(f"Error rebooting device: {e}")
        return jsonify({'error': 'Failed to send reboot command'}), 500

@admin_devices_bp.route('/<device_uid>/shutdown', methods=['POST'])
@console_management_required(Permission.CONSOLE_REMOTE)
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
            log_admin_action(session, "console_shutdown_command", f"Console {device_uid} shutdown command by admin", {'message': f"Shutdown command sent to console {device_uid}", 'device_uid': device_uid, 'device_id': console.id}
            )
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Shutdown command sent to {device_uid}'
            })
            
    except Exception as e:
        logger.error(f"Error shutting down device: {e}")
        return jsonify({'error': 'Failed to send shutdown command'}), 500

@admin_devices_bp.route('/<device_uid>/ping', methods=['POST'])
@console_management_required(Permission.CONSOLE_MANAGE)
def ping_device(device_uid):
    """Send ping to offline console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # TODO: Implement actual ping via WebSocket or message queue
            # For now, just log the ping attempt
            log_admin_action(session, "console_ping_command", f"Console {device_uid} ping command by admin", {'message': f"Ping sent to console {device_uid}", 'device_uid': device_uid, 'device_id': console.id}
            )
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
@console_management_required(Permission.CONSOLE_VIEW)
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
                AuditLog.details.op('->>')('device_id') == str(console.id)
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
@console_management_required(Permission.CONSOLE_MANAGE)
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
                AuditLog.details.op('->>')('device_id') == str(console.id),
                AuditLog.created_at >= datetime.now(timezone.utc) - timedelta(hours=hours)
            ).order_by(desc(AuditLog.created_at)).limit(limit)
            
            logs = []
            for log in logs_query:
                logs.append({
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'details': log.details
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
@console_management_required(Permission.CONSOLE_MANAGE)
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

# Console Game Management Endpoints
@admin_devices_bp.route('/<device_uid>/assign-arena', methods=['POST'])
@console_management_required(Permission.CONSOLE_MANAGE)
def assign_arena_to_console(device_uid):
    """Assign an arena to a console"""
    try:
        data = request.get_json()
        arena_id = data.get('arena_id')
        
        if arena_id is None:
            return jsonify({'error': 'Arena ID required'}), 400
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # If arena_id is None, we're removing the assignment
            if arena_id is None:
                console.current_arena_id = None
                session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Arena assignment removed from console {device_uid}'
                })
            
            # Verify arena exists
            from shared.models.arena import Arena
            arena = session.query(Arena).filter(Arena.id == arena_id).first()
            if not arena:
                return jsonify({'error': 'Arena not found'}), 404
            
            # Assign arena to console
            console.current_arena_id = arena_id
            session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Arena {arena.name} assigned to console {device_uid}'
            })
            
    except Exception as e:
        logger.error(f"Error assigning arena to console: {e}")
        return jsonify({'error': 'Failed to assign arena to console'}), 500

@admin_devices_bp.route('/<device_uid>/matches', methods=['GET'])
@console_management_required(Permission.CONSOLE_VIEW)
def get_console_matches(device_uid):
    """Get match history for a specific console"""
    try:
        limit = int(request.args.get('limit', 20))
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get matches for this console
            from shared.models.base import Match, MatchParticipant
            matches = session.query(Match).join(MatchParticipant).filter(
                MatchParticipant.console_id == console.id
            ).order_by(desc(Match.created_at)).limit(limit).all()
            
            match_list = []
            for match in matches:
                # Get arena name if available
                arena_name = None
                if match.arena_id:
                    from shared.models.arena import Arena
                    arena = session.query(Arena).filter(Arena.id == match.arena_id).first()
                    arena_name = arena.name if arena else None
                
                match_data = {
                    'id': match.id,
                    'status': match.status.value,
                    'created_at': match.created_at.isoformat(),
                    'ended_at': match.ended_at.isoformat() if match.ended_at else None,
                    'winner_team': match.winner_team,
                    'arena_name': arena_name,
                    'arena_id': match.arena_id,
                    'duration_minutes': int((match.ended_at - match.created_at).total_seconds() / 60) if match.ended_at else None,
                    'player_count': len(match.participants) if hasattr(match, 'participants') else 2
                }
                match_list.append(match_data)
            
            return jsonify({
                'matches': match_list,
                'console_uid': device_uid,
                'total': len(match_list)
            })
            
    except Exception as e:
        logger.error(f"Error getting console matches: {e}")
        return jsonify({'error': 'Failed to retrieve console matches'}), 500

@admin_devices_bp.route('/<device_uid>/current-match', methods=['GET'])
@console_management_required(Permission.CONSOLE_VIEW)
def get_console_current_match(device_uid):
    """Get current active match for a console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get current active match
            from shared.models.base import Match, MatchParticipant, MatchStatus
            current_match = session.query(Match).join(MatchParticipant).filter(
                MatchParticipant.console_id == console.id,
                Match.status == MatchStatus.active
            ).first()
            
            if not current_match:
                return jsonify({'error': 'No active match found'}), 404
            
            # Get arena name if available
            arena_name = None
            if current_match.arena_id:
                from shared.models.arena import Arena
                arena = session.query(Arena).filter(Arena.id == current_match.arena_id).first()
                arena_name = arena.name if arena else None
            
            match_data = {
                'match_id': current_match.id,
                'status': current_match.status.value,
                'created_at': current_match.created_at.isoformat(),
                'arena_name': arena_name,
                'arena_id': current_match.arena_id,
                'duration': str(datetime.now(timezone.utc) - current_match.created_at),
                'participants': len(current_match.participants) if hasattr(current_match, 'participants') else 2
            }
            
            return jsonify(match_data)
            
    except Exception as e:
        logger.error(f"Error getting current match: {e}")
        return jsonify({'error': 'Failed to retrieve current match'}), 500

@admin_devices_bp.route('/<device_uid>/start-match', methods=['POST'])
@console_management_required(Permission.CONSOLE_MANAGE)
def start_console_match(device_uid):
    """Start a new match on a console"""
    try:
        data = request.get_json()
        arena_id = data.get('arena_id')
        game_mode = data.get('game_mode', 'standard')
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Check if console already has an active match
            from shared.models.base import Match, MatchParticipant, MatchStatus
            existing_match = session.query(Match).join(MatchParticipant).filter(
                MatchParticipant.console_id == console.id,
                Match.status == MatchStatus.active
            ).first()
            
            if existing_match:
                return jsonify({'error': 'Console already has an active match'}), 400
            
            # Verify arena exists if provided
            if arena_id:
                from shared.models.arena import Arena
                arena = session.query(Arena).filter(Arena.id == arena_id).first()
                if not arena:
                    return jsonify({'error': 'Arena not found'}), 404
            
            # Create new match
            new_match = Match(
                arena_id=arena_id,
                status=MatchStatus.active,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_match)
            session.flush()  # Get the match ID
            
            # Add console as participant
            participant = MatchParticipant(
                match_id=new_match.id,
                console_id=console.id,
                team=0,
                joined_at=datetime.now(timezone.utc)
            )
            session.add(participant)
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Match started successfully',
                'match_id': new_match.id
            })
            
    except Exception as e:
        logger.error(f"Error starting console match: {e}")
        return jsonify({'error': 'Failed to start match'}), 500

@admin_devices_bp.route('/<device_uid>/end-match', methods=['POST'])
@console_management_required(Permission.CONSOLE_MANAGE)
def end_console_match(device_uid):
    """End current match on a console"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'admin_terminated')
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get current active match
            from shared.models.base import Match, MatchParticipant, MatchStatus
            current_match = session.query(Match).join(MatchParticipant).filter(
                MatchParticipant.console_id == console.id,
                Match.status == MatchStatus.active
            ).first()
            
            if not current_match:
                return jsonify({'error': 'No active match found'}), 404
            
            # End the match
            current_match.status = MatchStatus.completed
            current_match.ended_at = datetime.now(timezone.utc)
            current_match.end_reason = reason
            session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Match ended successfully'
            })
            
    except Exception as e:
        logger.error(f"Error ending console match: {e}")
        return jsonify({'error': 'Failed to end match'}), 500

@admin_devices_bp.route('/<device_uid>/game-settings', methods=['GET', 'POST'])
@console_management_required(Permission.CONSOLE_MANAGE)
def console_game_settings(device_uid):
    """Get or update game settings for a console"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            if request.method == 'GET':
                # Return current game settings (stored in console metadata or default values)
                # For now, return default settings - in a full implementation, these would be stored
                settings = {
                    'turn_time_seconds': 60,
                    'play_window_seconds': 10,
                    'quickdraw_bonus_seconds': 3,
                    'max_turns': 20,
                    'starting_health': 20,
                    'auto_arena_rotation': False,
                    'difficulty_level': 'normal'
                }
                
                return jsonify(settings)
            
            else:  # POST
                data = request.get_json()
                
                # Validate settings
                settings = {
                    'turn_time_seconds': max(30, min(300, int(data.get('turn_time_seconds', 60)))),
                    'play_window_seconds': max(5, min(30, int(data.get('play_window_seconds', 10)))),
                    'quickdraw_bonus_seconds': max(1, min(10, int(data.get('quickdraw_bonus_seconds', 3)))),
                    'max_turns': max(10, min(50, int(data.get('max_turns', 20)))),
                    'starting_health': max(10, min(50, int(data.get('starting_health', 20)))),
                    'auto_arena_rotation': bool(data.get('auto_arena_rotation', False)),
                    'difficulty_level': data.get('difficulty_level', 'normal')
                }
                
                # In a full implementation, you would store these settings in the console record
                # For now, we'll just return success
                
                return jsonify({
                    'success': True,
                    'message': 'Game settings updated successfully',
                    'settings': settings
                })
            
    except Exception as e:
        logger.error(f"Error managing console game settings: {e}")
        return jsonify({'error': 'Failed to manage game settings'}), 500


@admin_devices_bp.route('/pending', methods=['GET'])
@admin_required
def get_pending_devices():
    """Get devices pending approval"""
    try:
        with SessionLocal() as session:
            # Get devices with pending status
            pending_devices = session.query(Console).filter(
                Console.status == 'pending'
            ).order_by(desc(Console.registered_at)).all()
            
            devices = []
            for console in pending_devices:
                device_data = {
                    'id': console.id,
                    'device_uid': console.device_uid,
                    'status': console.status.value,
                    'registered_at': console.registered_at.isoformat(),
                    'owner_player_id': console.owner_player_id,
                    'public_key_fingerprint': console.public_key_pem[-12:] if console.public_key_pem else None,
                    'location': getattr(console, 'location', 'Unknown')
                }
                devices.append(device_data)
            
            return jsonify({
                'devices': devices,
                'total': len(devices)
            })
            
    except Exception as e:
        logger.error(f"Error getting pending devices: {e}")
        return jsonify({'error': str(e)}), 500


@admin_devices_bp.route('/stats', methods=['GET'])
@admin_required
def get_device_statistics():
    """Get device statistics"""
    try:
        with SessionLocal() as session:
            # Count devices by status
            total_devices = session.query(Console).count()
            active_devices = session.query(Console).filter(Console.status == 'active').count()
            pending_devices = session.query(Console).filter(Console.status == 'pending').count()
            revoked_devices = session.query(Console).filter(Console.status == 'revoked').count()
            
            # Get online devices - simplified (assume all active devices are potentially online)
            online_devices = active_devices  # Simplified approach since ConsoleActivityLog doesn't exist
            
            # Recent registrations (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_registrations = session.query(Console).filter(
                Console.registered_at >= yesterday
            ).count()
            
            return jsonify({
                'total_devices': total_devices,
                'active_devices': active_devices,
                'pending_devices': pending_devices,
                'revoked_devices': revoked_devices,
                'online_devices': online_devices,
                'recent_registrations': recent_registrations,
                'online_percentage': round((online_devices / active_devices * 100) if active_devices > 0 else 0, 1)
            })
            
    except Exception as e:
        logger.error(f"Error getting device statistics: {e}")
        return jsonify({'error': str(e)}), 500
