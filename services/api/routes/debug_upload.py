"""
Debug Upload Endpoint - No Authentication Required
Simple endpoint to receive debug data from consoles for troubleshooting
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

debug_upload_bp = Blueprint('debug_upload', __name__, url_prefix='/v1/debug')

@debug_upload_bp.route('/upload', methods=['POST'])
def upload_debug_data():
    """
    Simple debug data upload endpoint - NO AUTHENTICATION REQUIRED
    For emergency debugging when console can't authenticate properly
    """
    try:
        # Get raw data
        if request.is_json:
            data = request.get_json()
        else:
            # Handle form data or raw text
            data = {
                'raw_data': request.get_data(as_text=True),
                'content_type': request.content_type,
                'headers': dict(request.headers)
            }
        
        # Save to file for immediate review
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_file = f"/tmp/console_debug_{timestamp}.json"
        
        with open(debug_file, 'w') as f:
            import json
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'data': data
            }, f, indent=2)
        
        # Also log to console for immediate visibility
        logger.info(f"Debug upload received from {request.remote_addr}")
        logger.info(f"Data saved to: {debug_file}")
        
        # Print to stdout so it appears in service logs
        print(f"🔍 DEBUG UPLOAD RECEIVED: {debug_file}")
        if isinstance(data, dict) and data.get('log_data'):
            print(f"📊 Log data size: {len(str(data['log_data']))} chars")
        
        return jsonify({
            'success': True,
            'message': 'Debug data received successfully',
            'debug_file': debug_file,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing debug upload: {e}")
        return jsonify({'error': f'Failed to process debug data: {str(e)}'}), 500


@debug_upload_bp.route('/simple', methods=['POST'])
def simple_upload():
    """
    Ultra-simple upload endpoint - accepts any text data
    """
    try:
        # Get raw text data
        raw_data = request.get_data(as_text=True)
        
        # Save immediately
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_file = f"/tmp/simple_debug_{timestamp}.txt"
        
        with open(debug_file, 'w') as f:
            f.write(f"Debug Upload: {datetime.now().isoformat()}\n")
            f.write(f"From: {request.remote_addr}\n")
            f.write("=" * 50 + "\n")
            f.write(raw_data)
        
        print(f"📋 SIMPLE DEBUG UPLOAD: {debug_file}")
        print(f"📊 Data size: {len(raw_data)} chars")
        
        return jsonify({
            'success': True,
            'file': debug_file,
            'size': len(raw_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
