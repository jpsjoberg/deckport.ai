import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Arena Management Routes for Deckport Admin Panel
Handles arena creation, assignment, and game environment management
"""

from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime, timezone
from functools import wraps
from . import admin_bp
from services.api_service import APIService

# Initialize API service
api_service = APIService()

def require_admin_auth(f):
    """Decorator to require admin authentication for frontend routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/arenas')
@require_admin_auth
def arena_management():
    """Arena management dashboard"""
    try:
        # Get all arenas from API
        arenas_response = api_service.get('/v1/admin/arenas')
        arenas = arenas_response.get('arenas', []) if arenas_response else []
        
        # Get arena usage statistics
        stats_response = api_service.get('/v1/admin/arenas/stats')
        arena_stats = stats_response if stats_response else {}
        
        # Calculate arena statistics
        total_arenas = len(arenas)
        active_arenas = len([a for a in arenas if a.get('status') == 'active'])
        console_assignments = sum(a.get('console_count', 0) for a in arenas)
        
        stats = {
            'total_arenas': total_arenas,
            'active_arenas': active_arenas,
            'console_assignments': console_assignments,
            'match_count_24h': arena_stats.get('matches_24h', 0)
        }
        
        return render_template('admin/arena_management/index.html',
                             arenas=arenas,
                             stats=stats)
                             
    except Exception as e:
        flash(f'Error loading arena data: {str(e)}', 'error')
        return render_template('admin/arena_management/index.html',
                             arenas=[],
                             stats={'total_arenas': 0, 'active_arenas': 0, 'console_assignments': 0, 'match_count_24h': 0})

@admin_bp.route('/arenas/<int:arena_id>')
def arena_detail(arena_id):
    """Individual arena detail and management"""
    try:
        # Get specific arena data
        arena_response = api_service.get(f'/v1/admin/arenas/{arena_id}')
        
        if not arena_response:
            flash('Arena not found', 'error')
            return redirect(url_for('admin.arena_management'))
            
        arena = arena_response
        
        # Get consoles assigned to this arena
        consoles_response = api_service.get(f'/v1/admin/arenas/{arena_id}/consoles')
        arena['assigned_consoles'] = consoles_response.get('consoles', []) if consoles_response else []
        
        # Get recent matches in this arena
        matches_response = api_service.get(f'/v1/admin/arenas/{arena_id}/matches?limit=10')
        arena['recent_matches'] = matches_response.get('matches', []) if matches_response else []
        
        return render_template('admin/arena_management/detail.html', arena=arena)
        
    except Exception as e:
        flash(f'Error loading arena details: {str(e)}', 'error')
        return redirect(url_for('admin.arena_management'))

@admin_bp.route('/arenas/<int:arena_id>/consoles')
def arena_consoles(arena_id):
    """Manage console assignments for specific arena"""
    try:
        # Get arena info
        arena_response = api_service.get(f'/v1/admin/arenas/{arena_id}')
        if not arena_response:
            flash('Arena not found', 'error')
            return redirect(url_for('admin.arena_management'))
            
        arena = arena_response
        
        # Get all consoles
        all_consoles_response = api_service.get('/v1/admin/devices')
        all_consoles = all_consoles_response.get('devices', []) if all_consoles_response else []
        
        # Get consoles assigned to this arena
        assigned_response = api_service.get(f'/v1/admin/arenas/{arena_id}/consoles')
        assigned_consoles = assigned_response.get('consoles', []) if assigned_response else []
        assigned_ids = [c['id'] for c in assigned_consoles]
        
        # Separate assigned and available consoles
        available_consoles = [c for c in all_consoles if c['id'] not in assigned_ids]
        
        return render_template('admin/arena_management/console_assignment.html',
                             arena=arena,
                             assigned_consoles=assigned_consoles,
                             available_consoles=available_consoles)
                             
    except Exception as e:
        flash(f'Error loading console assignments: {str(e)}', 'error')
        return redirect(url_for('admin.arena_detail', arena_id=arena_id))

# API Routes for AJAX calls
@admin_bp.route('/api/arenas/<int:arena_id>/assign-console', methods=['POST'])
def assign_console_to_arena(arena_id):
    """Assign a console to an arena"""
    try:
        data = request.get_json()
        device_uid = data.get('device_uid')
        
        if not device_uid:
            return jsonify({'success': False, 'message': 'Device UID required'}), 400
        
        response = api_service.post(f'/v1/admin/arenas/{arena_id}/assign-console', {
            'device_uid': device_uid
        })
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} assigned to arena'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to assign console to arena'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error assigning console: {str(e)}'
        }), 500

@admin_bp.route('/api/arenas/<int:arena_id>/unassign-console', methods=['POST'])
def unassign_console_from_arena(arena_id):
    """Remove console assignment from arena"""
    try:
        data = request.get_json()
        device_uid = data.get('device_uid')
        
        if not device_uid:
            return jsonify({'success': False, 'message': 'Device UID required'}), 400
        
        response = api_service.post(f'/v1/admin/arenas/{arena_id}/unassign-console', {
            'device_uid': device_uid
        })
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} unassigned from arena'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to unassign console from arena'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error unassigning console: {str(e)}'
        }), 500

@admin_bp.route('/api/arenas/<int:arena_id>/activate', methods=['POST'])
def activate_arena(arena_id):
    """Activate an arena for use"""
    try:
        response = api_service.post(f'/v1/admin/arenas/{arena_id}/activate')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': 'Arena activated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to activate arena'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error activating arena: {str(e)}'
        }), 500

@admin_bp.route('/api/arenas/<int:arena_id>/deactivate', methods=['POST'])
def deactivate_arena(arena_id):
    """Deactivate an arena"""
    try:
        response = api_service.post(f'/v1/admin/arenas/{arena_id}/deactivate')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': 'Arena deactivated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to deactivate arena'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deactivating arena: {str(e)}'
        }), 500

@admin_bp.route('/arenas/create')
@require_admin_auth
def arena_creation_interface():
    """Arena creation interface with AI generation options"""
    return render_template('admin/arena_management/create.html')

@admin_bp.route('/arenas/create-batch', methods=['POST'])
@require_admin_auth
def create_arenas_batch():
    """Create multiple arenas using AI generation"""
    try:
        data = request.get_json()
        count = int(data.get('count', 1))
        theme_preference = data.get('theme_preference', '')
        
        if count < 1 or count > 100:
            return jsonify({
                'success': False,
                'message': 'Arena count must be between 1 and 100'
            }), 400
        
        # Import and use the arena creation engine
        import sys
        sys.path.append('/home/jp/deckport.ai')
        from services.arena_creation_engine import ArenaCreationAPI
        
        # Create arenas asynchronously
        import asyncio
        arena_api = ArenaCreationAPI()
        result = asyncio.run(arena_api.create_arenas_endpoint(count, theme_preference))
        
        if result.get('success'):
            flash(f"Successfully created {result['total_created']} arenas!", 'success')
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error creating arenas: {e}")
        return jsonify({
            'success': False,
            'message': f'Error creating arenas: {str(e)}'
        }), 500

@admin_bp.route('/arenas/creation-status/<job_id>')
@require_admin_auth
def arena_creation_status(job_id):
    """Get status of arena creation job"""
    # This would track long-running arena creation jobs
    # For now, return completed since we're doing synchronous creation
    return jsonify({
        'success': True,
        'status': 'completed',
        'progress': 100,
        'message': 'Arena creation completed'
    })
