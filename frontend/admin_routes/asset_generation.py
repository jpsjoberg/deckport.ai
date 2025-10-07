import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Asset Generation Admin Routes
Manages batch card artwork generation, queues, and progress monitoring
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from services.api_service import APIService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

asset_gen_bp = Blueprint('asset_generation', __name__, url_prefix='/admin/assets')

def require_admin_auth(f):
    """Admin authentication decorator"""
    from functools import wraps
    from flask import request, redirect, url_for
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@asset_gen_bp.route('/generation')
@require_admin_auth
def asset_generation_dashboard():
    """Asset generation dashboard with queue and progress monitoring"""
    try:
        api_service = APIService()
        
        # Get card statistics
        cards_response = api_service.get('/v1/admin/cards/stats')
        card_stats = cards_response if cards_response else {}
        
        # Get generation queue status
        queue_response = api_service.get('/v1/admin/assets/queue')
        queue_data = queue_response if queue_response else {}
        
        # Get ComfyUI status
        comfyui_response = api_service.get('/v1/admin/assets/comfyui/status')
        comfyui_status = comfyui_response if comfyui_response else {}
        
        # Get recent generation history
        history_response = api_service.get('/v1/admin/assets/history?limit=20')
        generation_history = history_response.get('history', []) if history_response else []
        
        return render_template('admin/asset_generation/dashboard.html',
                             card_stats=card_stats,
                             queue_data=queue_data,
                             comfyui_status=comfyui_status,
                             generation_history=generation_history)
                             
    except Exception as e:
        logger.error(f"Error loading asset generation dashboard: {e}")
        flash(f'Error loading asset generation data: {str(e)}', 'error')
        return render_template('admin/asset_generation/dashboard.html',
                             card_stats={},
                             queue_data={},
                             comfyui_status={},
                             generation_history=[])

@asset_gen_bp.route('/generate-all', methods=['POST'])
@require_admin_auth
def start_batch_generation():
    """Start batch generation of all card assets"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        generation_type = data.get('generation_type', 'artwork')  # artwork, frames, videos, all
        batch_size = int(data.get('batch_size', 10))
        priority = data.get('priority', 'normal')
        
        api_service = APIService()
        
        # Start batch generation via API
        response = api_service.post('/v1/admin/assets/batch-generate', {
            'generation_type': generation_type,
            'batch_size': batch_size,
            'priority': priority,
            'started_by': 'admin_panel'
        })
        
        if response and response.get('success'):
            flash(f'Batch generation started! Queue ID: {response.get("queue_id")}', 'success')
            return jsonify({
                'success': True,
                'queue_id': response.get('queue_id'),
                'estimated_time': response.get('estimated_time'),
                'total_cards': response.get('total_cards')
            })
        else:
            error_msg = response.get('error', 'Unknown error') if response else 'API call failed'
            flash(f'Failed to start batch generation: {error_msg}', 'error')
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Error starting batch generation: {e}")
        flash(f'Error starting batch generation: {str(e)}', 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_gen_bp.route('/queue')
@require_admin_auth
def view_generation_queue():
    """View current asset generation queue"""
    try:
        api_service = APIService()
        
        # Get detailed queue information
        queue_response = api_service.get('/v1/admin/assets/queue/detailed')
        queue_data = queue_response if queue_response else {}
        
        return render_template('admin/asset_generation/queue.html',
                             queue_data=queue_data)
                             
    except Exception as e:
        logger.error(f"Error loading generation queue: {e}")
        flash(f'Error loading queue data: {str(e)}', 'error')
        return render_template('admin/asset_generation/queue.html',
                             queue_data={})

@asset_gen_bp.route('/progress/<queue_id>')
@require_admin_auth
def view_generation_progress(queue_id):
    """View progress of specific generation job"""
    try:
        api_service = APIService()
        
        # Get progress data
        progress_response = api_service.get(f'/v1/admin/assets/progress/{queue_id}')
        progress_data = progress_response if progress_response else {}
        
        return render_template('admin/asset_generation/progress.html',
                             queue_id=queue_id,
                             progress_data=progress_data)
                             
    except Exception as e:
        logger.error(f"Error loading generation progress: {e}")
        return jsonify({'error': str(e)}), 500

@asset_gen_bp.route('/api/progress/<queue_id>')
@require_admin_auth
def get_generation_progress_api(queue_id):
    """Get real-time progress data for AJAX updates"""
    try:
        api_service = APIService()
        
        # Get current progress
        progress_response = api_service.get(f'/v1/admin/assets/progress/{queue_id}')
        
        if progress_response:
            return jsonify(progress_response)
        else:
            return jsonify({'error': 'Progress data not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting progress data: {e}")
        return jsonify({'error': str(e)}), 500

@asset_gen_bp.route('/cancel/<queue_id>', methods=['POST'])
@require_admin_auth
def cancel_generation(queue_id):
    """Cancel asset generation job"""
    try:
        api_service = APIService()
        
        # Cancel generation via API
        response = api_service.post(f'/v1/admin/assets/cancel/{queue_id}')
        
        if response and response.get('success'):
            flash('Generation job cancelled successfully', 'success')
            return jsonify({'success': True})
        else:
            error_msg = response.get('error', 'Failed to cancel job') if response else 'API call failed'
            flash(f'Failed to cancel generation: {error_msg}', 'error')
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Error cancelling generation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_gen_bp.route('/retry-failed', methods=['POST'])
@require_admin_auth
def retry_failed_generations():
    """Retry all failed asset generations"""
    try:
        api_service = APIService()
        
        # Retry failed generations via API
        response = api_service.post('/v1/admin/assets/retry-failed')
        
        if response and response.get('success'):
            flash(f'Retrying {response.get("retry_count", 0)} failed generations', 'success')
            return jsonify({
                'success': True,
                'retry_count': response.get('retry_count'),
                'new_queue_id': response.get('queue_id')
            })
        else:
            error_msg = response.get('error', 'Failed to retry') if response else 'API call failed'
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Error retrying failed generations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_gen_bp.route('/comfyui/status')
@require_admin_auth
def comfyui_status():
    """Get ComfyUI server status"""
    try:
        api_service = APIService()
        
        # Get ComfyUI status via API
        response = api_service.get('/v1/admin/assets/comfyui/status')
        
        if response:
            return jsonify(response)
        else:
            return jsonify({'status': 'unknown', 'error': 'Could not get ComfyUI status'}), 500
            
    except Exception as e:
        logger.error(f"Error getting ComfyUI status: {e}")
        return jsonify({'error': str(e)}), 500
