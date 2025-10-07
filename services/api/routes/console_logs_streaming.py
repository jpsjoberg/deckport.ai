"""
Console Log Streaming API Routes
Receives and processes real-time logs from deployed consoles for debugging and monitoring
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from sqlalchemy import desc
from shared.database.connection import SessionLocal
from shared.models.base import Console, AuditLog
from shared.auth.decorators import device_required
import logging
import json
import gzip
import base64

logger = logging.getLogger(__name__)

console_logs_streaming_bp = Blueprint('console_logs_streaming', __name__, url_prefix='/v1/console-logs')

@console_logs_streaming_bp.route('/stream', methods=['POST'])
@device_required
def stream_console_logs():
    """
    Receive streaming logs from console
    Handles both individual log entries and bulk log uploads
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        console_id = data.get('console_id')
        device_uid = data.get('device_uid')
        
        if not console_id and not device_uid:
            return jsonify({'error': 'Console ID or Device UID required'}), 400
        
        # Find console in database
        with SessionLocal() as session:
            if console_id:
                console = session.query(Console).filter(Console.id == console_id).first()
            else:
                console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Process log entries
            log_entries = data.get('logs', [])
            if not isinstance(log_entries, list):
                return jsonify({'error': 'Logs must be an array'}), 400
            
            processed_count = 0
            
            for log_entry in log_entries:
                try:
                    # Extract log data
                    log_level = log_entry.get('level', 'INFO')
                    log_message = log_entry.get('message', '')
                    log_source = log_entry.get('source', 'console')
                    log_timestamp = log_entry.get('timestamp')
                    log_data = log_entry.get('data', {})
                    
                    # Parse timestamp
                    entry_time = datetime.now(timezone.utc)
                    if log_timestamp:
                        try:
                            entry_time = datetime.fromisoformat(log_timestamp.replace('Z', '+00:00'))
                        except:
                            pass  # Use current time if parsing fails
                    
                    # Create audit log entry
                    audit_log = AuditLog(
                        actor_type="console",
                        actor_id=console.id,
                        action=f"console.log.{log_level.lower()}",
                        details={
                            'device_uid': console.device_uid,
                            'log_level': log_level,
                            'log_source': log_source,
                            'log_message': log_message,
                            'log_timestamp': log_timestamp,
                            'console_data': log_data,
                            'received_at': datetime.now(timezone.utc).isoformat()
                        },
                        created_at=entry_time
                    )
                    
                    session.add(audit_log)
                    processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to process log entry: {e}")
                    continue
            
            # Commit all log entries
            session.commit()
            
            return jsonify({
                'success': True,
                'processed_logs': processed_count,
                'total_received': len(log_entries),
                'console_id': console.id,
                'device_uid': console.device_uid,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error processing console logs: {e}")
        return jsonify({'error': 'Failed to process console logs'}), 500


@console_logs_streaming_bp.route('/upload-file', methods=['POST'])
@device_required 
def upload_log_file():
    """
    Upload entire log file from console
    Handles compressed log files and large log uploads
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        console_id = data.get('console_id')
        device_uid = data.get('device_uid')
        log_file_path = data.get('file_path', '/var/log/unknown.log')
        log_content = data.get('content', '')
        is_compressed = data.get('compressed', False)
        
        if not console_id and not device_uid:
            return jsonify({'error': 'Console ID or Device UID required'}), 400
        
        if not log_content:
            return jsonify({'error': 'Log content required'}), 400
        
        # Find console in database
        with SessionLocal() as session:
            if console_id:
                console = session.query(Console).filter(Console.id == console_id).first()
            else:
                console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Decompress if needed
            if is_compressed:
                try:
                    compressed_data = base64.b64decode(log_content)
                    log_content = gzip.decompress(compressed_data).decode('utf-8')
                except Exception as e:
                    return jsonify({'error': f'Failed to decompress log file: {e}'}), 400
            
            # Store log file as audit entry
            audit_log = AuditLog(
                actor_type="console",
                actor_id=console.id,
                action="console.log_file_upload",
                details={
                    'device_uid': console.device_uid,
                    'file_path': log_file_path,
                    'content_length': len(log_content),
                    'compressed': is_compressed,
                    'log_content': log_content,
                    'uploaded_at': datetime.now(timezone.utc).isoformat()
                },
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(audit_log)
            session.commit()
            
            return jsonify({
                'success': True,
                'file_path': log_file_path,
                'content_length': len(log_content),
                'console_id': console.id,
                'device_uid': console.device_uid,
                'message': f'Log file {log_file_path} uploaded successfully'
            })
            
    except Exception as e:
        logger.error(f"Error uploading log file: {e}")
        return jsonify({'error': 'Failed to upload log file'}), 500


@console_logs_streaming_bp.route('/crash-report', methods=['POST'])
def submit_crash_report():
    """
    Submit crash report with system state and logs
    Special endpoint for when console crashes or encounters critical errors
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        console_id = data.get('console_id')
        device_uid = data.get('device_uid')
        crash_type = data.get('crash_type', 'unknown')
        error_message = data.get('error_message', '')
        system_state = data.get('system_state', {})
        log_files = data.get('log_files', {})
        
        if not console_id and not device_uid:
            return jsonify({'error': 'Console ID or Device UID required'}), 400
        
        # Find console in database
        with SessionLocal() as session:
            if console_id:
                console = session.query(Console).filter(Console.id == console_id).first()
            else:
                console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Create critical crash report audit entry
            audit_log = AuditLog(
                actor_type="console",
                actor_id=console.id,
                action="console.crash_report",
                details={
                    'device_uid': console.device_uid,
                    'crash_type': crash_type,
                    'error_message': error_message,
                    'system_state': system_state,
                    'log_files': log_files,
                    'crash_time': datetime.now(timezone.utc).isoformat(),
                    'severity': 'critical'
                },
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(audit_log)
            
            # Update console health status to critical
            setattr(console, 'health_status', 'critical')
            setattr(console, 'last_error', error_message)
            setattr(console, 'last_error_time', datetime.now(timezone.utc))
            
            session.commit()
            
            logger.critical(f"Console crash report received: {console.device_uid} - {crash_type}: {error_message}")
            
            return jsonify({
                'success': True,
                'crash_report_id': audit_log.id,
                'console_id': console.id,
                'device_uid': console.device_uid,
                'message': 'Crash report submitted successfully',
                'support_contact': 'Check admin panel for detailed logs'
            })
            
    except Exception as e:
        logger.error(f"Error processing crash report: {e}")
        return jsonify({'error': 'Failed to process crash report'}), 500


# Admin endpoints for viewing console logs

@console_logs_streaming_bp.route('/admin/console/<int:console_id>/logs', methods=['GET'])
def get_console_logs(console_id):
    """Get logs for a specific console (admin endpoint)"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 100)), 1000)  # Max 1000 logs per request
        log_level = request.args.get('level')  # Filter by log level
        
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.id == console_id).first()
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Build query for console logs
            query = session.query(AuditLog).filter(
                AuditLog.actor_type == "console",
                AuditLog.actor_id == console_id
            )
            
            # Filter by log level if specified
            if log_level:
                query = query.filter(AuditLog.action.like(f'%{log_level.lower()}%'))
            
            # Order by most recent first
            query = query.order_by(desc(AuditLog.created_at))
            
            # Paginate
            offset = (page - 1) * per_page
            logs = query.offset(offset).limit(per_page).all()
            total_logs = query.count()
            
            # Format logs for response
            log_entries = []
            for log in logs:
                entry = {
                    'id': log.id,
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'level': log.details.get('log_level', 'INFO'),
                    'source': log.details.get('log_source', 'unknown'),
                    'message': log.details.get('log_message', ''),
                    'data': log.details.get('console_data', {}),
                    'received_at': log.details.get('received_at')
                }
                log_entries.append(entry)
            
            return jsonify({
                'logs': log_entries,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_logs,
                    'pages': (total_logs + per_page - 1) // per_page
                },
                'console': {
                    'id': console.id,
                    'device_uid': console.device_uid,
                    'status': console.status.value if hasattr(console.status, 'value') else str(console.status)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting console logs: {e}")
        return jsonify({'error': 'Failed to retrieve console logs'}), 500


@console_logs_streaming_bp.route('/admin/console/<int:console_id>/crash-reports', methods=['GET'])
def get_console_crash_reports(console_id):
    """Get crash reports for a specific console (admin endpoint)"""
    try:
        with SessionLocal() as session:
            console = session.query(Console).filter(Console.id == console_id).first()
            if not console:
                return jsonify({'error': 'Console not found'}), 404
            
            # Get crash reports
            crash_reports = session.query(AuditLog).filter(
                AuditLog.actor_type == "console",
                AuditLog.actor_id == console_id,
                AuditLog.action == "console.crash_report"
            ).order_by(desc(AuditLog.created_at)).limit(50).all()
            
            # Format crash reports
            reports = []
            for report in crash_reports:
                entry = {
                    'id': report.id,
                    'crash_time': report.created_at.isoformat(),
                    'crash_type': report.details.get('crash_type', 'unknown'),
                    'error_message': report.details.get('error_message', ''),
                    'system_state': report.details.get('system_state', {}),
                    'log_files': report.details.get('log_files', {}),
                    'severity': report.details.get('severity', 'unknown')
                }
                reports.append(entry)
            
            return jsonify({
                'crash_reports': reports,
                'total': len(reports),
                'console': {
                    'id': console.id,
                    'device_uid': console.device_uid,
                    'current_health': getattr(console, 'health_status', 'unknown'),
                    'last_error': getattr(console, 'last_error', None),
                    'last_error_time': getattr(console, 'last_error_time', None)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting crash reports: {e}")
        return jsonify({'error': 'Failed to retrieve crash reports'}), 500
