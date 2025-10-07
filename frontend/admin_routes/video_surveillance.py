import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Admin video surveillance routes - Monitor console video streams and manage surveillance
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from services.api_service import APIService
import logging

logger = logging.getLogger(__name__)

video_surveillance_bp = Blueprint('video_surveillance', __name__)

@video_surveillance_bp.route('/admin/surveillance')
def surveillance_dashboard():
    """Admin surveillance dashboard"""
    if 'admin_token' not in session:
        return redirect(url_for('auth.admin_login'))
    
    try:
        api_service = APIService()
        
        # Get active video streams
        active_streams_response = api_service.get('/v1/video/admin/active-streams', 
                                                headers={'Authorization': f'Bearer {session["admin_token"]}'})
        
        active_streams = []
        if active_streams_response and active_streams_response.get('active_streams'):
            active_streams = active_streams_response['active_streams']
        
        # Get all consoles for surveillance options
        consoles_response = api_service.get('/v1/admin/devices',
                                          headers={'Authorization': f'Bearer {session["admin_token"]}'})
        
        consoles = []
        if consoles_response and consoles_response.get('devices'):
            consoles = consoles_response['devices']
        
        return render_template('admin/video_surveillance/dashboard.html',
                             active_streams=active_streams,
                             consoles=consoles)
    
    except Exception as e:
        logger.error(f"Error loading surveillance dashboard: {e}")
        return render_template('admin/video_surveillance/dashboard.html',
                             active_streams=[],
                             consoles=[],
                             error="Failed to load surveillance data")

@video_surveillance_bp.route('/admin/surveillance/start', methods=['POST'])
def start_surveillance():
    """Start surveillance of a console"""
    if 'admin_token' not in session:
        return jsonify({"error": "Admin authentication required"}), 401
    
    try:
        data = request.get_json()
        console_id = data.get('console_id')
        reason = data.get('reason', 'Security monitoring')
        
        if not console_id:
            return jsonify({"error": "Console ID required"}), 400
        
        api_service = APIService()
        
        # Start surveillance stream
        surveillance_data = {
            "console_id": console_id,
            "reason": reason,
            "enable_audio": data.get('enable_audio', True)
        }
        
        response = api_service.post('/v1/video/admin/surveillance/start',
                                  data=surveillance_data,
                                  headers={'Authorization': f'Bearer {session["admin_token"]}'})
        
        if response:
            logger.info(f"Surveillance started for console {console_id} by admin {session.get('admin_username')}")
            return jsonify({
                "success": True,
                "stream_id": response.get('stream_id'),
                "surveillance_url": response.get('surveillance_url'),
                "message": f"Surveillance started for console {console_id}"
            })
        else:
            return jsonify({"error": "Failed to start surveillance"}), 500
    
    except Exception as e:
        logger.error(f"Error starting surveillance: {e}")
        return jsonify({"error": "Failed to start surveillance"}), 500

@video_surveillance_bp.route('/admin/surveillance/view/<stream_id>')
def view_surveillance(stream_id):
    """View surveillance stream"""
    if 'admin_token' not in session:
        return redirect(url_for('auth.admin_login'))
    
    try:
        api_service = APIService()
        
        # Get surveillance stream info
        response = api_service.get(f'/v1/video/admin/surveillance/{stream_id}/view',
                                 headers={'Authorization': f'Bearer {session["admin_token"]}'})
        
        if response:
            stream_info = response
            
            # Get stream logs
            logs_response = api_service.get(f'/v1/video/{stream_id}/logs',
                                          headers={'Authorization': f'Bearer {session["admin_token"]}'})
            
            stream_logs = []
            if logs_response and logs_response.get('logs'):
                stream_logs = logs_response['logs']
            
            return render_template('admin/video_surveillance/view.html',
                                 stream_info=stream_info,
                                 stream_logs=stream_logs,
                                 stream_id=stream_id)
        else:
            return render_template('admin/video_surveillance/view.html',
                                 error="Surveillance stream not found or access denied")
    
    except Exception as e:
        logger.error(f"Error viewing surveillance stream {stream_id}: {e}")
        return render_template('admin/video_surveillance/view.html',
                             error="Failed to load surveillance stream")

@video_surveillance_bp.route('/admin/surveillance/end/<stream_id>', methods=['POST'])
def end_surveillance(stream_id):
    """End surveillance stream"""
    if 'admin_token' not in session:
        return jsonify({"error": "Admin authentication required"}), 401
    
    try:
        api_service = APIService()
        
        # End the stream
        response = api_service.post(f'/v1/video/{stream_id}/end',
                                  headers={'Authorization': f'Bearer {session["admin_token"]}'})
        
        if response:
            logger.info(f"Surveillance stream {stream_id} ended by admin {session.get('admin_username')}")
            return jsonify({
                "success": True,
                "message": "Surveillance ended",
                "duration_seconds": response.get('duration_seconds')
            })
        else:
            return jsonify({"error": "Failed to end surveillance"}), 500
    
    except Exception as e:
        logger.error(f"Error ending surveillance stream {stream_id}: {e}")
        return jsonify({"error": "Failed to end surveillance"}), 500

@video_surveillance_bp.route('/admin/surveillance/logs/<stream_id>')
def get_surveillance_logs(stream_id):
    """Get surveillance stream logs"""
    if 'admin_token' not in session:
        return jsonify({"error": "Admin authentication required"}), 401
    
    try:
        api_service = APIService()
        
        response = api_service.get(f'/v1/video/{stream_id}/logs',
                                 headers={'Authorization': f'Bearer {session["admin_token"]}'})
        
        if response:
            return jsonify(response)
        else:
            return jsonify({"error": "Failed to get logs"}), 500
    
    except Exception as e:
        logger.error(f"Error getting surveillance logs for {stream_id}: {e}")
        return jsonify({"error": "Failed to get logs"}), 500

@video_surveillance_bp.route('/admin/surveillance/history')
def surveillance_history():
    """View surveillance history"""
    if 'admin_token' not in session:
        return redirect(url_for('auth.admin_login'))
    
    try:
        # This would need a new API endpoint to get historical surveillance data
        # For now, show placeholder
        return render_template('admin/video_surveillance/history.html',
                             surveillance_history=[],
                             message="Surveillance history feature coming soon")
    
    except Exception as e:
        logger.error(f"Error loading surveillance history: {e}")
        return render_template('admin/video_surveillance/history.html',
                             surveillance_history=[],
                             error="Failed to load surveillance history")
