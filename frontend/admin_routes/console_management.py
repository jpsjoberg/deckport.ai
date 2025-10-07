import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Console Management Routes for Deckport Admin Panel
Handles console fleet management, diagnostics, and deployment
"""

import requests
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

@admin_bp.route('/consoles')
@require_admin_auth
def console_management():
    """Console fleet management dashboard"""
    try:
        # Get console fleet data from API
        consoles_response = api_service.get('/v1/admin/devices')
        pending_response = api_service.get('/v1/admin/devices?status=pending')
        
        consoles = consoles_response.get('devices', []) if consoles_response else []
        pending_consoles = pending_response.get('devices', []) if pending_response else []
        
        # Calculate fleet statistics with safe type checking
        total_consoles = len(consoles)
        
        def safe_get_minutes(console):
            """Safely get last_seen_minutes as integer"""
            minutes = console.get('last_seen_minutes')
            if isinstance(minutes, (int, float)):
                return minutes
            elif isinstance(minutes, str) and minutes.isdigit():
                return int(minutes)
            else:
                return 999  # Default for unknown
        
        online_count = len([c for c in consoles if c.get('status') == 'active' and safe_get_minutes(c) < 5])
        offline_count = len([c for c in consoles if c.get('status') == 'active' and safe_get_minutes(c) >= 5])
        maintenance_count = len([c for c in consoles if c.get('status') == 'maintenance'])
        pending_count = len(pending_consoles)
        
        fleet_stats = {
            'total': total_consoles,
            'online': online_count,
            'offline': offline_count,
            'maintenance': maintenance_count,
            'pending': pending_count
        }
        
        # Debug: Print to stdout (will appear in logs)
        print(f"TEMPLATE DEBUG: consoles={len(consoles)}, pending={len(pending_consoles)}, stats={fleet_stats}")
        
        return render_template('admin/console_management/index_deckport.html', 
                             consoles=consoles, 
                             pending_consoles=pending_consoles[:3],  # Show first 3 in sidebar
                             total_consoles=fleet_stats['total'],
                             active_consoles=fleet_stats['online'],
                             pending_count=fleet_stats['pending'],
                             fleet_stats=fleet_stats)
                             
    except Exception as e:
        flash(f'Error loading console data: {str(e)}', 'error')
        # Return with mock data as fallback
        fleet_stats = {'total': 0, 'online': 0, 'offline': 0, 'maintenance': 0, 'pending': 0}
        return render_template('admin/console_management/index_deckport.html', 
                             consoles=[], 
                             pending_consoles=[],
                             total_consoles=0,
                             active_consoles=0,
                             fleet_stats=fleet_stats)

@admin_bp.route('/simple-test-no-auth')
def simple_test_no_auth():
    """Simple test route without auth"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error("SIMPLE TEST NO AUTH: Route called")
    return "<h1>Simple Test No Auth Works</h1>"

@admin_bp.route('/simple-test')
@require_admin_auth
def simple_test():
    """Simple test route"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error("SIMPLE TEST: Route called")
    return "<h1>Simple Test Works</h1>"

@admin_bp.route('/debug-api-test')
@require_admin_auth
def console_debug():
    """Debug route to test API service"""
    from services.api_service import APIService
    api_service = APIService()
    try:
        response = api_service.get('/v1/admin/devices')
        return f"<h1>Debug Response</h1><p>Type: {type(response)}</p><p>Keys: {list(response.keys()) if response else 'None'}</p><p>Devices: {len(response.get('devices', [])) if response else 0}</p><pre>{str(response)[:1000]}...</pre>"
    except Exception as e:
        return f"<h1>Debug Error</h1><p>{str(e)}</p>"

@admin_bp.route('/consoles/<device_uid>')
@require_admin_auth
def console_detail(device_uid):
    """Individual console detail and management"""
    try:
        # Get specific console data
        console_response = api_service.get(f'/v1/admin/devices/{device_uid}')
        
        if not console_response:
            flash('Console not found', 'error')
            return redirect(url_for('admin.console_management'))
            
        console = console_response
        
        # Get console logs and diagnostics
        logs_response = api_service.get(f'/v1/admin/devices/{device_uid}/logs')
        diagnostics_response = api_service.get(f'/v1/admin/devices/{device_uid}/diagnostics')
        
        console['logs'] = logs_response.get('logs', []) if logs_response else []
        console['diagnostics'] = diagnostics_response.get('diagnostics', {}) if diagnostics_response else {}
        
        return render_template('admin/console_management/console_detail.html', console=console)
        
    except Exception as e:
        flash(f'Error loading console details: {str(e)}', 'error')
        return redirect(url_for('admin.console_management'))

@admin_bp.route('/consoles/registration')
def console_registration():
    """Console registration approval interface"""
    try:
        # Get all pending registrations
        pending_response = api_service.get('/v1/admin/devices?status=pending')
        pending_consoles = pending_response.get('devices', []) if pending_response else []
        
        return render_template('admin/console_management/registration.html', 
                             pending_consoles=pending_consoles)
                             
    except Exception as e:
        flash(f'Error loading pending registrations: {str(e)}', 'error')
        return render_template('admin/console_management/registration.html', 
                             pending_consoles=[])

# API Routes for AJAX calls
@admin_bp.route('/api/console/<device_uid>/approve', methods=['POST'])
def approve_console(device_uid):
    """Approve a pending console registration"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/approve', 
                                  {'approved': True})
        
        if response and response.get('status') == 'approved':
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} approved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to approve console'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error approving console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/reject', methods=['POST'])
def reject_console(device_uid):
    """Reject a pending console registration"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/reject', 
                                  {'approved': False})
        
        if response:
            return jsonify({
                'success': True,
                'message': f'Console {device_uid} rejected'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reject console'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error rejecting console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/reboot', methods=['POST'])
def reboot_console(device_uid):
    """Send reboot command to console"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/reboot')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Reboot command sent to {device_uid}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send reboot command'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error rebooting console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/shutdown', methods=['POST'])
def shutdown_console(device_uid):
    """Send shutdown command to console"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/shutdown')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Shutdown command sent to {device_uid}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send shutdown command'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error shutting down console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/ping', methods=['POST'])
def ping_console(device_uid):
    """Send ping to offline console"""
    try:
        response = api_service.post(f'/v1/admin/devices/{device_uid}/ping')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': f'Ping sent to {device_uid}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Console did not respond to ping'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error pinging console: {str(e)}'
        }), 500

@admin_bp.route('/api/console/<device_uid>/status', methods=['GET'])
def get_console_status(device_uid):
    """Get real-time console status"""
    try:
        response = api_service.get(f'/v1/admin/devices/{device_uid}/status')
        
        if response:
            return jsonify(response)
        else:
            return jsonify({
                'error': 'Console not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': f'Error getting console status: {str(e)}'
        }), 500

@admin_bp.route('/api/consoles/fleet-status', methods=['GET'])
def get_fleet_status():
    """Get real-time fleet status for dashboard updates"""
    try:
        consoles_response = api_service.get('/v1/admin/devices')
        consoles = consoles_response.get('devices', []) if consoles_response else []
        
        # Calculate real-time statistics
        total_consoles = len(consoles)
        online_count = len([c for c in consoles if c.get('status') == 'active' and c.get('last_seen_minutes', 999) < 5])
        offline_count = len([c for c in consoles if c.get('status') == 'active' and c.get('last_seen_minutes', 0) >= 5])
        maintenance_count = len([c for c in consoles if c.get('status') == 'maintenance'])
        
        return jsonify({
            'total': total_consoles,
            'online': online_count,
            'offline': offline_count,
            'maintenance': maintenance_count,
            'consoles': consoles
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting fleet status: {str(e)}'
        }), 500

# Arena and Game Integration Routes
@admin_bp.route('/consoles/<device_uid>/arena', methods=['GET', 'POST'])
def console_arena_management(device_uid):
    """Manage arena assignment for specific console"""
    try:
        if request.method == 'POST':
            # Handle arena assignment
            data = request.get_json() if request.is_json else request.form
            arena_id = data.get('arena_id')
            
            if not arena_id:
                return jsonify({'success': False, 'message': 'Arena ID required'}), 400
            
            response = api_service.post(f'/v1/admin/devices/{device_uid}/assign-arena', {
                'arena_id': arena_id
            })
            
            if response and response.get('success'):
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Arena assigned successfully'})
                else:
                    flash('Arena assigned successfully', 'success')
                    return redirect(url_for('admin.console_detail', device_uid=device_uid))
            else:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Failed to assign arena'}), 400
                else:
                    flash('Failed to assign arena', 'error')
        
        # GET request - show arena assignment interface
        console_response = api_service.get(f'/v1/admin/devices/{device_uid}')
        if not console_response:
            flash('Console not found', 'error')
            return redirect(url_for('admin.console_management'))
        
        console = console_response
        
        # Get available arenas
        arenas_response = api_service.get('/v1/admin/arenas')
        arenas = arenas_response.get('arenas', []) if arenas_response else []
        
        # Get current arena assignment
        current_arena = None
        if console.get('current_arena_id'):
            arena_response = api_service.get(f'/v1/admin/arenas/{console["current_arena_id"]}')
            current_arena = arena_response if arena_response else None
        
        return render_template('admin/console_management/arena_assignment.html',
                             console=console,
                             arenas=arenas,
                             current_arena=current_arena)
                             
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
        else:
            flash(f'Error managing arena assignment: {str(e)}', 'error')
            return redirect(url_for('admin.console_detail', device_uid=device_uid))

@admin_bp.route('/consoles/<device_uid>/matches')
def console_matches(device_uid):
    """View console's match history and active games"""
    try:
        # Get console info
        console_response = api_service.get(f'/v1/admin/devices/{device_uid}')
        if not console_response:
            flash('Console not found', 'error')
            return redirect(url_for('admin.console_management'))
        
        console = console_response
        
        # Get match history
        matches_response = api_service.get(f'/v1/admin/devices/{device_uid}/matches')
        matches = matches_response.get('matches', []) if matches_response else []
        
        # Get current active match
        current_match_response = api_service.get(f'/v1/admin/devices/{device_uid}/current-match')
        current_match = current_match_response if current_match_response else None
        
        # Calculate match statistics
        total_matches = len(matches)
        wins = len([m for m in matches if m.get('winner_team') == 0])  # Assuming team 0 is console's team
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        match_stats = {
            'total_matches': total_matches,
            'wins': wins,
            'losses': total_matches - wins,
            'win_rate': round(win_rate, 1),
            'avg_match_duration': sum(m.get('duration_minutes', 0) for m in matches) / total_matches if total_matches > 0 else 0
        }
        
        return render_template('admin/console_management/matches.html',
                             console=console,
                             matches=matches,
                             current_match=current_match,
                             match_stats=match_stats)
                             
    except Exception as e:
        flash(f'Error loading console matches: {str(e)}', 'error')
        return redirect(url_for('admin.console_detail', device_uid=device_uid))

@admin_bp.route('/consoles/<device_uid>/current-match')
def console_current_match(device_uid):
    """Monitor active match on console"""
    try:
        # Get current match data
        match_response = api_service.get(f'/v1/admin/devices/{device_uid}/current-match')
        
        if not match_response:
            return jsonify({'error': 'No active match found'}), 404
        
        match_data = match_response
        
        # Get real-time match state
        if match_data.get('match_id'):
            state_response = api_service.get(f'/v1/admin/matches/{match_data["match_id"]}/state')
            match_data['game_state'] = state_response if state_response else {}
        
        return jsonify(match_data)
        
    except Exception as e:
        return jsonify({'error': f'Error getting current match: {str(e)}'}), 500

@admin_bp.route('/consoles/<device_uid>/start-match', methods=['POST'])
def start_console_match(device_uid):
    """Start a new match on console"""
    try:
        data = request.get_json()
        arena_id = data.get('arena_id')
        game_mode = data.get('game_mode', 'standard')
        
        response = api_service.post(f'/v1/admin/devices/{device_uid}/start-match', {
            'arena_id': arena_id,
            'game_mode': game_mode
        })
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': 'Match started successfully',
                'match_id': response.get('match_id')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start match'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting match: {str(e)}'
        }), 500

@admin_bp.route('/consoles/<device_uid>/end-match', methods=['POST'])
def end_console_match(device_uid):
    """End current match on console"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'admin_terminated')
        
        response = api_service.post(f'/v1/admin/devices/{device_uid}/end-match', {
            'reason': reason
        })
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': 'Match ended successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to end match'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error ending match: {str(e)}'
        }), 500

@admin_bp.route('/consoles/<device_uid>/game-settings', methods=['GET', 'POST'])
def console_game_settings(device_uid):
    """Configure game-specific console settings"""
    try:
        if request.method == 'POST':
            # Handle settings update
            data = request.get_json() if request.is_json else request.form
            
            settings = {
                'turn_time_seconds': int(data.get('turn_time_seconds', 60)),
                'play_window_seconds': int(data.get('play_window_seconds', 10)),
                'quickdraw_bonus_seconds': int(data.get('quickdraw_bonus_seconds', 3)),
                'max_turns': int(data.get('max_turns', 20)),
                'starting_health': int(data.get('starting_health', 20)),
                'auto_arena_rotation': data.get('auto_arena_rotation', 'false') == 'true',
                'difficulty_level': data.get('difficulty_level', 'normal')
            }
            
            response = api_service.post(f'/v1/admin/devices/{device_uid}/game-settings', settings)
            
            if response and response.get('success'):
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Settings updated successfully'})
                else:
                    flash('Game settings updated successfully', 'success')
                    return redirect(url_for('admin.console_detail', device_uid=device_uid))
            else:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Failed to update settings'}), 400
                else:
                    flash('Failed to update game settings', 'error')
        
        # GET request - show settings interface
        console_response = api_service.get(f'/v1/admin/devices/{device_uid}')
        if not console_response:
            flash('Console not found', 'error')
            return redirect(url_for('admin.console_management'))
        
        console = console_response
        
        # Get current game settings
        settings_response = api_service.get(f'/v1/admin/devices/{device_uid}/game-settings')
        current_settings = settings_response if settings_response else {
            'turn_time_seconds': 60,
            'play_window_seconds': 10,
            'quickdraw_bonus_seconds': 3,
            'max_turns': 20,
            'starting_health': 20,
            'auto_arena_rotation': False,
            'difficulty_level': 'normal'
        }
        
        return render_template('admin/console_management/game_settings.html',
                             console=console,
                             settings=current_settings)
                             
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
        else:
            flash(f'Error managing game settings: {str(e)}', 'error')
            return redirect(url_for('admin.console_detail', device_uid=device_uid))