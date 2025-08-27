"""
Video streaming routes - Basic video streaming endpoints
"""

from flask import Blueprint, request, jsonify
import secrets
import uuid

video_streaming_bp = Blueprint('video_streaming', __name__, url_prefix='/v1/video')

@video_streaming_bp.route('/battle/start', methods=['POST'])
def start_battle_stream():
    """Start a video stream for battle participants"""
    data = request.get_json() or {}
    
    # Generate mock stream data
    stream_id = f"battle_{secrets.token_urlsafe(16)}"
    
    return jsonify({
        "stream_id": stream_id,
        "stream_url": f"rtmp://localhost:1935/live/{stream_id}",
        "rtmp_key": secrets.token_urlsafe(32),
        "status": "starting",
        "recording": True,
        "quality_settings": {
            "resolution": "1280x720",
            "fps": 30,
            "bitrate": "2500k"
        }
    })

@video_streaming_bp.route('/admin/surveillance/start', methods=['POST'])
def start_admin_surveillance():
    """Start admin surveillance of a console"""
    data = request.get_json() or {}
    
    console_id = data.get('console_id', 1)
    stream_id = f"admin_surveillance_{console_id}_{secrets.token_urlsafe(16)}"
    
    return jsonify({
        "stream_id": stream_id,
        "surveillance_url": f"/admin/surveillance/view/{stream_id}",
        "status": "starting",
        "recording": True,
        "console_id": console_id,
        "started_by": "admin"
    })

@video_streaming_bp.route('/admin/active-streams', methods=['GET'])
def get_active_streams():
    """Get all active video streams"""
    # Return mock data for now
    return jsonify({
        "active_streams": [],
        "total_count": 0
    })