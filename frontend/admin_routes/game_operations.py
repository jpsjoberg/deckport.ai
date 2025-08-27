"""
Game Operations Routes for Deckport Admin Panel
Handles live matches, tournaments, and game balance
"""

from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime, timezone
from . import admin_bp
from services.api_service import APIService

# Initialize API service
api_service = APIService()

@admin_bp.route('/game-operations')
def game_operations():
    """Game operations dashboard"""
    try:
        # Get dashboard data from API
        dashboard_response = api_service.get('/v1/admin/game-operations/dashboard')
        live_matches_response = api_service.get('/v1/admin/game-operations/matches/live')
        queue_response = api_service.get('/v1/admin/game-operations/matchmaking/queue')
        tournaments_response = api_service.get('/v1/admin/game-operations/tournaments')
        
        # Ensure dashboard_data has the expected structure
        dashboard_data = dashboard_response or {}
        
        # If dashboard_data doesn't have the expected nested structure, create it
        if 'live_matches' not in dashboard_data:
            dashboard_data['live_matches'] = {
                'active': 0,
                'queued_players': 0,
                'avg_wait_time': 0,
                'peak_concurrent': 0
            }
        
        if 'tournaments' not in dashboard_data:
            dashboard_data['tournaments'] = {
                'active': 0,
                'participants_today': 0,
                'total_prize_pool': 0,
                'scheduled_today': 0
            }
            
        if 'player_activity' not in dashboard_data:
            dashboard_data['player_activity'] = {
                'online_now': 0,
                'matches_today': 0,
                'peak_today': 0,
                'avg_session_time': 0
            }
            
        if 'game_balance' not in dashboard_data:
            dashboard_data['game_balance'] = {
                'imbalanced_cards': 0,
                'meta_diversity': 0,
                'recent_changes': 0,
                'pending_reviews': 0
            }
        
        live_matches = live_matches_response.get('matches', []) if live_matches_response else []
        queue_data = queue_response or {}
        tournaments = tournaments_response.get('tournaments', []) if tournaments_response else []
        
        # Filter for recent matches and active tournaments
        recent_matches = live_matches[:10]  # Show top 10 recent matches
        active_tournaments = [t for t in tournaments if t.get('status') == 'active'][:5]
        
        return render_template('admin/game_operations/index.html',
                             dashboard_data=dashboard_data,
                             recent_matches=recent_matches,
                             queue_data=queue_data,
                             active_tournaments=active_tournaments)
                             
    except Exception as e:
        flash(f'Error loading game operations data: {str(e)}', 'error')
        # Return with empty data as fallback with proper structure
        fallback_dashboard_data = {
            'live_matches': {
                'active': 0,
                'queued_players': 0,
                'avg_wait_time': 0,
                'peak_concurrent': 0
            },
            'tournaments': {
                'active': 0,
                'participants_today': 0,
                'total_prize_pool': 0,
                'scheduled_today': 0
            },
            'player_activity': {
                'online_now': 0,
                'matches_today': 0,
                'peak_today': 0,
                'avg_session_time': 0
            },
            'game_balance': {
                'imbalanced_cards': 0,
                'meta_diversity': 0,
                'recent_changes': 0,
                'pending_reviews': 0
            }
        }
        
        return render_template('admin/game_operations/index.html',
                             dashboard_data=fallback_dashboard_data,
                             recent_matches=[],
                             queue_data={},
                             active_tournaments=[])

@admin_bp.route('/game-operations/live-matches')
def live_matches():
    """Live match monitoring"""
    try:
        # Get live matches data
        matches_response = api_service.get('/v1/admin/game-operations/matches/live')
        matches = matches_response.get('matches', []) if matches_response else []
        
        return render_template('admin/game_operations/live_matches.html',
                             matches=matches,
                             total_matches=len(matches))
                             
    except Exception as e:
        flash(f'Error loading live matches: {str(e)}', 'error')
        return render_template('admin/game_operations/live_matches.html',
                             matches=[],
                             total_matches=0)

@admin_bp.route('/game-operations/match/<match_id>')
def match_detail(match_id):
    """Individual match detail and control"""
    try:
        # Get match details
        match_response = api_service.get(f'/v1/admin/game-operations/matches/{match_id}')
        
        if not match_response:
            flash('Match not found', 'error')
            return redirect(url_for('admin.live_matches'))
        
        return render_template('admin/game_operations/match_detail.html',
                             match=match_response)
                             
    except Exception as e:
        flash(f'Error loading match details: {str(e)}', 'error')
        return redirect(url_for('admin.live_matches'))

@admin_bp.route('/game-operations/card-balance')
def card_balance():
    """Card balance management interface"""
    try:
        # Get card balance data
        balance_response = api_service.get('/v1/admin/game-operations/balance/cards')
        balance_data = balance_response or {}
        
        cards = balance_data.get('cards', [])
        summary = balance_data.get('summary', {})
        
        # Filter problem cards (high priority issues)
        problem_cards = [c for c in cards if c.get('priority') in ['high', 'medium']][:20]
        
        return render_template('admin/game_operations/card_balance.html',
                             cards=cards,
                             problem_cards=problem_cards,
                             summary=summary)
                             
    except Exception as e:
        flash(f'Error loading card balance data: {str(e)}', 'error')
        return render_template('admin/game_operations/card_balance.html',
                             cards=[],
                             problem_cards=[],
                             summary={})

@admin_bp.route('/game-operations/tournaments')
def tournaments():
    """Tournament management interface"""
    try:
        # Get tournaments data
        tournaments_response = api_service.get('/v1/admin/game-operations/tournaments')
        tournaments = tournaments_response.get('tournaments', []) if tournaments_response else []
        
        # Separate active and scheduled tournaments
        active_tournaments = [t for t in tournaments if t.get('status') == 'active']
        scheduled_tournaments = [t for t in tournaments if t.get('status') == 'scheduled']
        
        return render_template('admin/game_operations/tournaments.html',
                             active_tournaments=active_tournaments,
                             scheduled_tournaments=scheduled_tournaments,
                             total_tournaments=len(tournaments))
                             
    except Exception as e:
        flash(f'Error loading tournaments: {str(e)}', 'error')
        return render_template('admin/game_operations/tournaments.html',
                             active_tournaments=[],
                             scheduled_tournaments=[],
                             total_tournaments=0)

@admin_bp.route('/game-operations/analytics')
def game_analytics():
    """Game analytics dashboard"""
    try:
        # Get analytics data
        analytics_response = api_service.get('/v1/admin/game-operations/analytics/player-activity')
        analytics_data = analytics_response or {}
        
        return render_template('admin/game_operations/analytics.html',
                             analytics=analytics_data)
                             
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('admin/game_operations/analytics.html',
                             analytics={})

# API Routes for AJAX calls
@admin_bp.route('/api/game-operations/match/<match_id>/terminate', methods=['POST'])
def terminate_match(match_id):
    """Terminate a match (admin intervention)"""
    try:
        data = request.get_json() or {}
        response = api_service.post(f'/v1/admin/game-operations/matches/{match_id}/terminate', data)
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message', f'Match {match_id} terminated')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to terminate match'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error terminating match: {str(e)}'
        }), 500

@admin_bp.route('/api/game-operations/card/<product_sku>/balance', methods=['POST'])
def update_card_balance(product_sku):
    """Update card balance stats"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        response = api_service.post(f'/v1/admin/game-operations/balance/cards/{product_sku}', data)
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message'),
                'changes': response.get('changes', [])
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update card balance'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating card balance: {str(e)}'
        }), 500

@admin_bp.route('/api/game-operations/maintenance', methods=['POST'])
def trigger_maintenance():
    """Trigger system maintenance mode"""
    try:
        data = request.get_json() or {}
        response = api_service.post('/v1/admin/game-operations/system/maintenance', data)
        
        if response and response.get('success'):
            return jsonify({
                'success': True,
                'message': response.get('message'),
                'estimated_end': response.get('estimated_end')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to trigger maintenance'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error triggering maintenance: {str(e)}'
        }), 500

@admin_bp.route('/api/game-operations/dashboard/refresh', methods=['GET'])
def refresh_dashboard():
    """Get refreshed dashboard data"""
    try:
        dashboard_response = api_service.get('/v1/admin/game-operations/dashboard')
        
        if dashboard_response:
            return jsonify(dashboard_response)
        else:
            return jsonify({'error': 'Failed to refresh dashboard data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error refreshing dashboard: {str(e)}'}), 500

@admin_bp.route('/api/game-operations/queue/status', methods=['GET'])
def get_queue_status():
    """Get current matchmaking queue status"""
    try:
        queue_response = api_service.get('/v1/admin/game-operations/matchmaking/queue')
        
        if queue_response:
            return jsonify(queue_response)
        else:
            return jsonify({'error': 'Failed to get queue status'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error getting queue status: {str(e)}'}), 500