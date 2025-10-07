import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Console Log Management Routes
Admin interface for viewing and managing console logs
"""

from flask import render_template, jsonify, request
from . import admin_bp
from services.api_service import APIService
import logging

logger = logging.getLogger(__name__)

@admin_bp.route('/consoles/<int:console_id>/logs')
def console_logs(console_id):
    """Console log viewer interface"""
    try:
        api_service = APIService()
        
        # Get console information
        console_response = api_service.get(f'/v1/admin/devices/{console_id}')
        console = console_response if console_response else {}
        
        # Get recent logs
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        log_level = request.args.get('level', '')
        
        # Build log request URL
        log_url = f'/v1/console-logs/admin/console/{console_id}/logs?page={page}&per_page={per_page}'
        if log_level:
            log_url += f'&level={log_level}'
        
        logs_response = api_service.get(log_url)
        logs_data = logs_response if logs_response else {'logs': [], 'pagination': {}}
        
        # Get crash reports
        crash_response = api_service.get(f'/v1/console-logs/admin/console/{console_id}/crash-reports')
        crash_reports = crash_response.get('crash_reports', []) if crash_response else []
        
        return render_template('admin/console_management/logs.html',
                             console=console,
                             logs=logs_data.get('logs', []),
                             pagination=logs_data.get('pagination', {}),
                             crash_reports=crash_reports,
                             current_level=log_level)
                             
    except Exception as e:
        logger.error(f"Error loading console logs: {e}")
        return render_template('admin/console_management/logs.html',
                             console={'id': console_id, 'device_uid': 'Unknown'},
                             logs=[],
                             pagination={},
                             crash_reports=[],
                             current_level='',
                             error=f"Failed to load logs: {str(e)}")


@admin_bp.route('/consoles/<int:console_id>/logs/download')
def download_console_logs(console_id):
    """Download console logs as text file"""
    try:
        api_service = APIService()
        
        # Get all logs for console
        logs_response = api_service.get(f'/v1/console-logs/admin/console/{console_id}/logs?per_page=1000')
        logs_data = logs_response if logs_response else {'logs': []}
        
        # Format logs as text
        log_text = f"Deckport Console Logs - Console ID: {console_id}\n"
        log_text += f"Generated: {datetime.now().isoformat()}\n"
        log_text += "=" * 80 + "\n\n"
        
        for log in logs_data.get('logs', []):
            log_text += f"[{log.get('timestamp', 'Unknown')}] [{log.get('level', 'INFO')}] [{log.get('source', 'unknown')}]\n"
            log_text += f"  {log.get('message', 'No message')}\n"
            if log.get('data'):
                log_text += f"  Data: {log['data']}\n"
            log_text += "\n"
        
        # Return as downloadable file
        from flask import make_response
        response = make_response(log_text)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=console-{console_id}-logs.txt'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading console logs: {e}")
        return jsonify({'error': 'Failed to download logs'}), 500


@admin_bp.route('/logs/all-consoles')
def all_console_logs():
    """View logs from all consoles"""
    try:
        api_service = APIService()
        
        # Get all consoles
        consoles_response = api_service.get('/v1/admin/devices')
        consoles = consoles_response.get('devices', []) if consoles_response else []
        
        # Get recent logs from all consoles
        all_logs = []
        for console in consoles:
            try:
                logs_response = api_service.get(f'/v1/console-logs/admin/console/{console["id"]}/logs?per_page=10')
                console_logs = logs_response.get('logs', []) if logs_response else []
                
                for log in console_logs:
                    log['console_info'] = {
                        'id': console['id'],
                        'device_uid': console['device_uid'],
                        'location': console.get('location', {}).get('name', 'Unknown')
                    }
                    all_logs.append(log)
            except:
                continue
        
        # Sort by timestamp (most recent first)
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return render_template('admin/console_management/all_logs.html',
                             consoles=consoles,
                             logs=all_logs[:100],  # Show top 100 recent logs
                             total_consoles=len(consoles))
                             
    except Exception as e:
        logger.error(f"Error loading all console logs: {e}")
        return render_template('admin/console_management/all_logs.html',
                             consoles=[],
                             logs=[],
                             total_consoles=0,
                             error=f"Failed to load logs: {str(e)}")
