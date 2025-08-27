"""

Admin Player Management API Routes
Comprehensive player administration, support, and moderation
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from shared.models.base import db, Player, EnhancedNFCCard, CardTrade
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

# In-memory storage for demo purposes (would use database in production)
support_tickets = []
moderation_reports = []
player_notes = {}

@admin_players_bp.route('/stats', methods=['GET'])
@auto_rbac_required()
def get_player_stats():
    """Get comprehensive player statistics"""
    try:
        now = datetime.utcnow()
        
        # Basic player counts
        total_players = db.session.query(func.count(Player.id)).scalar()
        
        # Active players (have activated cards in last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        active_players = db.session.query(
            func.count(func.distinct(EnhancedNFCCard.owner_player_id))
        ).filter(
            and_(
                EnhancedNFCCard.status == 'activated',
                EnhancedNFCCard.last_used_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        # Online players (used cards in last 24 hours)
        yesterday = now - timedelta(hours=24)
        online_players = db.session.query(
            func.count(func.distinct(EnhancedNFCCard.owner_player_id))
        ).filter(
            and_(
                EnhancedNFCCard.status == 'activated',
                EnhancedNFCCard.last_used_at >= yesterday
            )
        ).scalar() or 0
        
        # New registrations
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        new_today = db.session.query(func.count(Player.id)).filter(
            Player.created_at >= today_start
        ).scalar()
        
        new_this_week = db.session.query(func.count(Player.id)).filter(
            Player.created_at >= week_start
        ).scalar()
        
        new_this_month = db.session.query(func.count(Player.id)).filter(
            Player.created_at >= month_start
        ).scalar()
        
        # Player engagement metrics
        players_with_cards = db.session.query(
            func.count(func.distinct(EnhancedNFCCard.owner_player_id))
        ).filter(
            EnhancedNFCCard.status == 'activated'
        ).scalar() or 0
        
        players_who_traded = db.session.query(
            func.count(func.distinct(CardTrade.seller_player_id))
        ).filter(
            CardTrade.status == 'completed'
        ).scalar() or 0
        
        # Calculate rates
        activation_rate = (players_with_cards / total_players * 100) if total_players > 0 else 0
        retention_rate = (active_players / total_players * 100) if total_players > 0 else 0
        trading_participation = (players_who_traded / players_with_cards * 100) if players_with_cards > 0 else 0
        
        return jsonify({
            'total_players': total_players,
            'active_players': active_players,
            'online_players': online_players,
            'new_registrations': {
                'today': new_today,
                'this_week': new_this_week,
                'this_month': new_this_month
            },
            'engagement_metrics': {
                'activation_rate': round(activation_rate, 2),
                'retention_rate': round(retention_rate, 2),
                'trading_participation': round(trading_participation, 2)
            },
            'players_with_cards': players_with_cards,
            'players_who_traded': players_who_traded
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
        per_page = min(int(request.args.get('per_page', 50)), 100)  # Max 100 per page
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')  # 'active', 'inactive', 'suspended'
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build base query
        query = db.session.query(Player)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Player.username.ilike(f'%{search}%'),
                    Player.email.ilike(f'%{search}%'),
                    Player.id == int(search) if search.isdigit() else False
                )
            )
        
        # Apply status filter
        if status_filter == 'active':
            # Players with recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_player_ids = db.session.query(EnhancedNFCCard.owner_player_id).filter(
                and_(
                    EnhancedNFCCard.status == 'activated',
                    EnhancedNFCCard.last_used_at >= thirty_days_ago
                )
            ).distinct().subquery()
            query = query.filter(Player.id.in_(active_player_ids))
        elif status_filter == 'inactive':
            # Players without recent activity
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_player_ids = db.session.query(EnhancedNFCCard.owner_player_id).filter(
                and_(
                    EnhancedNFCCard.status == 'activated',
                    EnhancedNFCCard.last_used_at >= thirty_days_ago
                )
            ).distinct().subquery()
            query = query.filter(~Player.id.in_(active_player_ids))
        
        # Apply sorting
        if sort_by == 'username':
            query = query.order_by(desc(Player.username) if sort_order == 'desc' else Player.username)
        elif sort_by == 'email':
            query = query.order_by(desc(Player.email) if sort_order == 'desc' else Player.email)
        elif sort_by == 'created_at':
            query = query.order_by(desc(Player.created_at) if sort_order == 'desc' else Player.created_at)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        players = query.offset(offset).limit(per_page).all()
        
        # Enhance player data with additional info
        enhanced_players = []
        for player in players:
            # Get card count
            card_count = db.session.query(func.count(EnhancedNFCCard.id)).filter(
                and_(
                    EnhancedNFCCard.owner_player_id == player.id,
                    EnhancedNFCCard.status == 'activated'
                )
            ).scalar() or 0
            
            # Get last activity
            last_activity = db.session.query(func.max(EnhancedNFCCard.last_used_at)).filter(
                and_(
                    EnhancedNFCCard.owner_player_id == player.id,
                    EnhancedNFCCard.status == 'activated'
                )
            ).scalar()
            
            # Get trade count
            trade_count = db.session.query(func.count(CardTrade.id)).filter(
                or_(
                    CardTrade.seller_player_id == player.id,
                    CardTrade.buyer_player_id == player.id
                )
            ).scalar() or 0
            
            enhanced_players.append({
                'id': player.id,
                'username': player.username,
                'email': player.email,
                'created_at': player.created_at.isoformat() if player.created_at else None,
                'updated_at': player.updated_at.isoformat() if player.updated_at else None,
                'card_count': card_count,
                'trade_count': trade_count,
                'last_activity': last_activity.isoformat() if last_activity else None,
                'status': 'active' if last_activity and last_activity > datetime.utcnow() - timedelta(days=30) else 'inactive',
                'admin_notes': player_notes.get(player.id, '')
            })
        
        return jsonify({
            'players': enhanced_players,
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
        # Get player
        player = db.session.query(Player).filter(Player.id == player_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Get player's cards
        cards = db.session.query(EnhancedNFCCard).filter(
            EnhancedNFCCard.owner_player_id == player_id
        ).all()
        
        # Get player's trades
        trades = db.session.query(CardTrade).filter(
            or_(
                CardTrade.seller_player_id == player_id,
                CardTrade.buyer_player_id == player_id
            )
        ).order_by(desc(CardTrade.created_at)).limit(20).all()
        
        # Calculate statistics
        total_cards = len(cards)
        total_taps = sum(card.tap_counter or 0 for card in cards)
        last_activity = max((card.last_used_at for card in cards if card.last_used_at), default=None)
        
        # Format cards data
        cards_data = []
        for card in cards:
            cards_data.append({
                'id': card.id,
                'product_sku': card.product_sku,
                'serial_number': card.serial_number,
                'status': card.status,
                'activated_at': card.activated_at.isoformat() if card.activated_at else None,
                'last_used_at': card.last_used_at.isoformat() if card.last_used_at else None,
                'tap_counter': card.tap_counter or 0,
                'current_level': card.current_level or 1
            })
        
        # Format trades data
        trades_data = []
        for trade in trades:
            trades_data.append({
                'id': trade.id,
                'status': trade.status,
                'trade_value': float(trade.trade_value) if trade.trade_value else 0,
                'created_at': trade.created_at.isoformat() if trade.created_at else None,
                'role': 'seller' if trade.seller_player_id == player_id else 'buyer'
            })
        
        return jsonify({
            'player': {
                'id': player.id,
                'username': player.username,
                'email': player.email,
                'created_at': player.created_at.isoformat() if player.created_at else None,
                'updated_at': player.updated_at.isoformat() if player.updated_at else None,
                'admin_notes': player_notes.get(player_id, '')
            },
            'statistics': {
                'total_cards': total_cards,
                'total_taps': total_taps,
                'total_trades': len(trades),
                'last_activity': last_activity.isoformat() if last_activity else None
            },
            'cards': cards_data,
            'recent_trades': trades_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get player detail: {str(e)}'}), 500

@admin_players_bp.route('/<int:player_id>/notes', methods=['PUT'])
@auto_rbac_required()
def update_player_notes(player_id):
    """Update admin notes for a player"""
    try:
        data = request.get_json()
        notes = data.get('notes', '')
        
        # Verify player exists
        player = db.session.query(Player).filter(Player.id == player_id).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Update notes (in production, this would be stored in the database)
        player_notes[player_id] = notes
        
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
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 50)
        
        # Filter tickets
        filtered_tickets = support_tickets
        if status:
            filtered_tickets = [t for t in filtered_tickets if t['status'] == status]
        if priority:
            filtered_tickets = [t for t in filtered_tickets if t['priority'] == priority]
        
        # Sort by creation date (most recent first)
        filtered_tickets.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Paginate
        total_count = len(filtered_tickets)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tickets = filtered_tickets[start_idx:end_idx]
        
        return jsonify({
            'tickets': paginated_tickets,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
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
        
        # Verify player exists
        player = db.session.query(Player).filter(Player.id == data['player_id']).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        # Create ticket
        ticket = {
            'id': len(support_tickets) + 1,
            'player_id': data['player_id'],
            'player_username': player.username,
            'subject': data['subject'],
            'description': data['description'],
            'priority': data['priority'],  # 'low', 'medium', 'high', 'urgent'
            'status': 'open',
            'category': data.get('category', 'general'),
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',
            'assigned_to': data.get('assigned_to', ''),
            'responses': []
        }
        
        support_tickets.append(ticket)
        
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
        # Filter and sort reports
        status = request.args.get('status', '')
        filtered_reports = moderation_reports
        if status:
            filtered_reports = [r for r in filtered_reports if r['status'] == status]
        
        # Sort by severity and creation date
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        filtered_reports.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['created_at']), reverse=True)
        
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
        report = next((r for r in moderation_reports if r['id'] == report_id), None)
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
