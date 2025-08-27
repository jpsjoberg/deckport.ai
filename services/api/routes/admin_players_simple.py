"""

Admin Player Management API Routes - Simplified Production Version
Comprehensive player administration, support, and moderation
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from shared.auth.auto_rbac_decorator import auto_rbac_required
import logging
from shared.auth.admin_roles import Permission

admin_players_bp = Blueprint('admin_players', __name__, url_prefix='/v1/admin/players')

    """Decorator to require admin authentication"""
    
    def decorated_function(*args, **kwargs):
        auth_result = verify_admin_token(request)
        if not auth_result['valid']:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Sample data (in production, this would be database-backed)
sample_players = [
    {
        'id': 1,
        'username': 'cardmaster_pro',
        'email': 'cardmaster@example.com',
        'created_at': (datetime.utcnow() - timedelta(days=45)).isoformat(),
        'updated_at': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        'card_count': 12,
        'trade_count': 8,
        'last_activity': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        'status': 'active',
        'admin_notes': 'VIP player, very active in tournaments'
    },
    {
        'id': 2,
        'username': 'newbie_player',
        'email': 'newbie@example.com',
        'created_at': (datetime.utcnow() - timedelta(days=3)).isoformat(),
        'updated_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
        'card_count': 3,
        'trade_count': 0,
        'last_activity': (datetime.utcnow() - timedelta(days=1)).isoformat(),
        'status': 'active',
        'admin_notes': 'New player, needs guidance'
    },
    {
        'id': 3,
        'username': 'inactive_user',
        'email': 'inactive@example.com',
        'created_at': (datetime.utcnow() - timedelta(days=120)).isoformat(),
        'updated_at': (datetime.utcnow() - timedelta(days=45)).isoformat(),
        'card_count': 5,
        'trade_count': 2,
        'last_activity': (datetime.utcnow() - timedelta(days=45)).isoformat(),
        'status': 'inactive',
        'admin_notes': 'Long-time inactive, potential re-engagement target'
    }
]

sample_tickets = [
    {
        'id': 1,
        'player_id': 1,
        'player_username': 'cardmaster_pro',
        'subject': 'Card not activating properly',
        'description': 'My new RADIANT-001 card won\'t activate when I tap it',
        'priority': 'medium',
        'status': 'open',
        'category': 'technical',
        'created_at': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
        'created_by': 'player',
        'assigned_to': 'support_team',
        'responses': []
    },
    {
        'id': 2,
        'player_id': 2,
        'player_username': 'newbie_player',
        'subject': 'How to trade cards?',
        'description': 'I\'m new and don\'t understand how the trading system works',
        'priority': 'low',
        'status': 'resolved',
        'category': 'general',
        'created_at': (datetime.utcnow() - timedelta(days=2)).isoformat(),
        'created_by': 'player',
        'assigned_to': 'support_team',
        'responses': [
            {
                'message': 'Here\'s a guide to our trading system...',
                'created_at': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'created_by': 'support_agent'
            }
        ]
    }
]

sample_reports = [
    {
        'id': 1,
        'reported_player_id': 3,
        'reported_username': 'inactive_user',
        'reporter_player_id': 1,
        'reporter_username': 'cardmaster_pro',
        'reason': 'inappropriate_behavior',
        'description': 'Player was using offensive language in chat',
        'severity': 'medium',
        'status': 'pending',
        'created_at': (datetime.utcnow() - timedelta(hours=12)).isoformat(),
        'evidence': ['screenshot1.png', 'chat_log.txt']
    }
]

@admin_players_bp.route('/stats', methods=['GET'])
@auto_rbac_required()
def get_player_stats():
    """Get comprehensive player statistics"""
    try:
        # Sample statistics
        return jsonify({
            'total_players': 1247,
            'active_players': 456,
            'online_players': 89,
            'new_registrations': {
                'today': 12,
                'this_week': 67,
                'this_month': 234
            },
            'engagement_metrics': {
                'activation_rate': 78.5,
                'retention_rate': 65.2,
                'trading_participation': 42.1
            },
            'players_with_cards': 892,
            'players_who_traded': 376
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get player stats: {str(e)}'}), 500

@admin_players_bp.route('/', methods=['GET'])
@auto_rbac_required()
def get_players():
    """Get paginated list of players with filtering"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        
        # Filter players based on search and status
        filtered_players = sample_players
        
        if search:
            filtered_players = [p for p in filtered_players 
                              if search.lower() in p['username'].lower() or 
                                 search.lower() in p['email'].lower()]
        
        if status_filter:
            filtered_players = [p for p in filtered_players if p['status'] == status_filter]
        
        # Simple pagination
        total_count = len(filtered_players)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_players = filtered_players[start_idx:end_idx]
        
        return jsonify({
            'players': paginated_players,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page,
                'has_next': page * per_page < total_count,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get players: {str(e)}'}), 500

@admin_players_bp.route('/<int:player_id>', methods=['GET'])
@auto_rbac_required()
def get_player_detail(player_id):
    """Get detailed information about a specific player"""
    try:
        # Find player
        player = next((p for p in sample_players if p['id'] == player_id), None)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Sample detailed data
        player_detail = {
            'player': player,
            'statistics': {
                'total_cards': player['card_count'],
                'total_taps': player['card_count'] * 45,  # Sample calculation
                'total_trades': player['trade_count'],
                'last_activity': player['last_activity']
            },
            'cards': [
                {
                    'id': i,
                    'product_sku': f'CARD-{i:03d}',
                    'serial_number': f'SN{player_id:03d}{i:03d}',
                    'status': 'activated',
                    'activated_at': (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
                    'last_used_at': (datetime.utcnow() - timedelta(hours=i*2)).isoformat(),
                    'tap_counter': i * 12,
                    'current_level': min(i + 1, 10)
                } for i in range(1, player['card_count'] + 1)
            ],
            'recent_trades': [
                {
                    'id': i,
                    'status': 'completed',
                    'trade_value': 25.50 + (i * 5),
                    'created_at': (datetime.utcnow() - timedelta(days=i*7)).isoformat(),
                    'role': 'seller' if i % 2 == 0 else 'buyer'
                } for i in range(1, min(player['trade_count'] + 1, 6))
            ]
        }
        
        return jsonify(player_detail)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get player detail: {str(e)}'}), 500

@admin_players_bp.route('/<int:player_id>/notes', methods=['PUT'])
@auto_rbac_required()
def update_player_notes(player_id):
    """Update admin notes for a player"""
    try:
        data = request.get_json()
        notes = data.get('notes', '')
        
        # Find and update player
        player = next((p for p in sample_players if p['id'] == player_id), None)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        player['admin_notes'] = notes
        
        logging.info(f"Updated admin notes for player {player_id}")
        
        return jsonify({
            'success': True,
            'message': 'Player notes updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update player notes: {str(e)}'}), 500

@admin_players_bp.route('/support/tickets', methods=['GET'])
@auto_rbac_required()
def get_support_tickets():
    """Get support tickets"""
    try:
        # Filter parameters
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        
        # Filter tickets
        filtered_tickets = sample_tickets
        if status:
            filtered_tickets = [t for t in filtered_tickets if t['status'] == status]
        if priority:
            filtered_tickets = [t for t in filtered_tickets if t['priority'] == priority]
        
        return jsonify({
            'tickets': filtered_tickets,
            'pagination': {
                'page': 1,
                'per_page': 20,
                'total': len(filtered_tickets),
                'pages': 1
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get support tickets: {str(e)}'}), 500

@admin_players_bp.route('/support/tickets', methods=['POST'])
@auto_rbac_required()
def create_support_ticket():
    """Create a support ticket (admin-initiated)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['player_id', 'subject', 'description', 'priority']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Find player
        player = next((p for p in sample_players if p['id'] == data['player_id']), None)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Create ticket
        ticket = {
            'id': len(sample_tickets) + 1,
            'player_id': data['player_id'],
            'player_username': player['username'],
            'subject': data['subject'],
            'description': data['description'],
            'priority': data['priority'],
            'status': 'open',
            'category': data.get('category', 'general'),
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',
            'assigned_to': data.get('assigned_to', ''),
            'responses': []
        }
        
        sample_tickets.append(ticket)
        
        logging.info(f"Created support ticket for player {data['player_id']}: {data['subject']}")
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'message': 'Support ticket created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create support ticket: {str(e)}'}), 500

@admin_players_bp.route('/moderation/reports', methods=['GET'])
@auto_rbac_required()
def get_moderation_reports():
    """Get moderation reports"""
    try:
        status = request.args.get('status', '')
        filtered_reports = sample_reports
        if status:
            filtered_reports = [r for r in filtered_reports if r['status'] == status]
        
        return jsonify({
            'reports': filtered_reports,
            'total_count': len(filtered_reports)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get moderation reports: {str(e)}'}), 500

@admin_players_bp.route('/moderation/reports/<int:report_id>/resolve', methods=['POST'])
@auto_rbac_required()
def resolve_moderation_report(report_id):
    """Resolve a moderation report"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        notes = data.get('notes', '')
        
        # Find report
        report = next((r for r in sample_reports if r['id'] == report_id), None)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Update report
        report['status'] = 'resolved'
        report['resolved_at'] = datetime.utcnow().isoformat()
        report['resolved_by'] = 'admin'
        report['action_taken'] = action
        report['resolution_notes'] = notes
        
        logging.info(f"Resolved moderation report {report_id} with action: {action}")
        
        return jsonify({
            'success': True,
            'report': report,
            'message': 'Moderation report resolved successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to resolve moderation report: {str(e)}'}), 500
