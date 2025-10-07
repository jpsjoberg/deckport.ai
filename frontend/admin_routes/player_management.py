import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Player Management Routes for Deckport Admin Panel
Handles player accounts, authentication, and community moderation
"""

from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime, timezone
from . import admin_bp
from services.api_service import APIService

# Initialize API service
api_service = APIService()

@admin_bp.route('/players')
def player_management():
    """Player management dashboard"""
    try:
        # Get player statistics
        stats_response = api_service.get('/v1/admin/players/statistics')
        stats = stats_response or {}
        
        # Get recent players (first page)
        players_response = api_service.get('/v1/admin/players?page=1&page_size=20')
        players_data = players_response or {}
        
        recent_players = players_data.get('players', [])
        
        return render_template('admin/player_management/index.html',
                             stats=stats,
                             recent_players=recent_players)
                             
    except Exception as e:
        flash(f'Error loading player data: {str(e)}', 'error')
        return render_template('admin/player_management/index.html',
                             stats={},
                             recent_players=[])

@admin_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    """Individual player detail and management"""
    try:
        # Get player details
        player_response = api_service.get(f'/v1/admin/players/{player_id}')
        
        if not player_response:
            flash('Player not found', 'error')
            return redirect(url_for('admin.player_management'))
        
        return render_template('admin/player_management/player_detail.html',
                             player=player_response)
                             
    except Exception as e:
        flash(f'Error loading player details: {str(e)}', 'error')
        return redirect(url_for('admin.player_management'))

@admin_bp.route('/players/search')
def player_search():
    """Player search interface"""
    try:
        # Get search parameters
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        status_filter = request.args.get('status', '')
        
        # Build API query parameters
        params = {
            'page': page,
            'page_size': page_size,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        if query:
            params['search'] = query
        if status_filter:
            params['status'] = status_filter
        
        # Get players from API
        players_response = api_service.get('/v1/admin/players', params=params)
        players_data = players_response or {}
        
        return render_template('admin/player_management/search.html',
                             players_data=players_data,
                             search_query=query,
                             current_page=page,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             status_filter=status_filter)
                             
    except Exception as e:
        flash(f'Error searching players: {str(e)}', 'error')
        return render_template('admin/player_management/search.html',
                             players_data={'players': [], 'total': 0},
                             search_query='',
                             current_page=1,
                             sort_by='created_at',
                             sort_order='desc',
                             status_filter='')

@admin_bp.route('/player-support')
def player_support():
    """Support ticket management"""
    # TODO: Implement support ticket system
    return render_template('admin/player_management/support.html',
                         tickets=[])

@admin_bp.route('/player-moderation')
def player_moderation():
    """Player moderation interface"""
    # TODO: Implement moderation dashboard
    return render_template('admin/player_management/moderation.html',
                         recent_actions=[])

# API Routes for AJAX calls
@admin_bp.route('/api/players/<int:player_id>/ban', methods=['POST'])
def ban_player(player_id):
    """Ban a player account"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        response = api_service.post(f'/v1/admin/players/{player_id}/ban', data)
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to ban player'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error banning player: {str(e)}'
        }), 500

@admin_bp.route('/api/players/<int:player_id>/unban', methods=['POST'])
def unban_player(player_id):
    """Unban a player account"""
    try:
        response = api_service.post(f'/v1/admin/players/{player_id}/unban')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to unban player'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error unbanning player: {str(e)}'
        }), 500

@admin_bp.route('/api/players/<int:player_id>/warn', methods=['POST'])
def warn_player(player_id):
    """Issue a warning to a player"""
    try:
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'success': False, 'message': 'Warning message required'}), 400
        
        response = api_service.post(f'/v1/admin/players/{player_id}/warn', data)
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to issue warning'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error issuing warning: {str(e)}'
        }), 500

@admin_bp.route('/api/players/<int:player_id>/reset-password', methods=['POST'])
def reset_player_password(player_id):
    """Reset a player's password"""
    try:
        response = api_service.post(f'/v1/admin/players/{player_id}/reset-password')
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reset password'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resetting password: {str(e)}'
        }), 500

@admin_bp.route('/api/players/search', methods=['GET'])
def api_search_players():
    """Search players via API (for autocomplete, etc.)"""
    try:
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query:
            return jsonify({'players': []})
        
        response = api_service.get(f'/v1/admin/players/search?q={query}&limit={limit}')
        
        if response:
            return jsonify(response)
        else:
            return jsonify({'players': []})
            
    except Exception as e:
        return jsonify({'error': f'Error searching players: {str(e)}'}), 500

@admin_bp.route('/api/players/statistics/refresh', methods=['GET'])
def refresh_player_statistics():
    """Get refreshed player statistics"""
    try:
        stats_response = api_service.get('/v1/admin/players/statistics')
        
        if stats_response:
            return jsonify(stats_response)
        else:
            return jsonify({'error': 'Failed to refresh statistics'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error refreshing statistics: {str(e)}'}), 500