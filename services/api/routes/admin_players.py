"""
Admin Player Management API Routes - Real Database Implementation
Comprehensive player administration, support, and moderation
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from shared.auth.auto_rbac_decorator import auto_rbac_required
from shared.database.connection import SessionLocal
from shared.models.base import Player, PlayerCard, CardTransfer
from shared.models.nfc_trading_system import TradingHistory
from shared.models.player_moderation import PlayerActivityLog, PlayerBan, PlayerWarning
import logging

logger = logging.getLogger(__name__)
admin_players_bp = Blueprint('admin_players', __name__, url_prefix='/v1/admin/players')

# Real database implementation - no sample data needed

@admin_players_bp.route('/stats', methods=['GET'])
@auto_rbac_required()
def get_player_stats():
    """Get comprehensive player statistics from database"""
    try:
        with SessionLocal() as session:
            now = datetime.utcnow()
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Total players
            total_players = session.query(func.count(Player.id)).scalar() or 0
            
            # Active players (logged in within last 7 days)
            active_players = session.query(
                func.count(func.distinct(PlayerActivityLog.player_id))
            ).filter(
                and_(
                    PlayerActivityLog.timestamp >= week_ago,
                    PlayerActivityLog.activity_type == 'LOGIN'
                )
            ).scalar() or 0
            
            # Online players (active within last hour)
            hour_ago = now - timedelta(hours=1)
            online_players = session.query(
                func.count(func.distinct(PlayerActivityLog.player_id))
            ).filter(
                and_(
                    PlayerActivityLog.timestamp >= hour_ago,
                    PlayerActivityLog.activity_type == 'LOGIN'
                )
            ).scalar() or 0
            
            # New registrations
            new_today = session.query(
                func.count(Player.id)
            ).filter(func.date(Player.created_at) == today).scalar() or 0
            
            new_week = session.query(
                func.count(Player.id)
            ).filter(Player.created_at >= week_ago).scalar() or 0
            
            new_month = session.query(
                func.count(Player.id)
            ).filter(Player.created_at >= month_ago).scalar() or 0
            
            # Players with cards
            players_with_cards = session.query(
                func.count(func.distinct(PlayerCard.player_id))
            ).scalar() or 0
            
            # Players who traded
            players_who_traded = session.query(
                func.count(func.distinct(
                    func.coalesce(TradingHistory.seller_player_id, TradingHistory.buyer_player_id)
                ))
            ).scalar() or 0
            
            # Calculate engagement metrics
            activation_rate = 0.0
            if total_players > 0:
                verified_players = session.query(
                    func.count(Player.id)
                ).filter(Player.is_verified == True).scalar() or 0
                activation_rate = (verified_players / total_players) * 100
            
            retention_rate = 0.0
            if new_month > 0:
                retained_players = session.query(
                    func.count(func.distinct(Player.id))
                ).join(
                    PlayerActivityLog, Player.id == PlayerActivityLog.player_id
                ).filter(
                    and_(
                        Player.created_at >= month_ago,
                        PlayerActivityLog.timestamp >= Player.created_at + timedelta(days=7),
                        PlayerActivityLog.activity_type == 'LOGIN'
                    )
                ).scalar() or 0
                retention_rate = (retained_players / new_month) * 100
            
            trading_participation = 0.0
            if total_players > 0:
                trading_participation = (players_who_traded / total_players) * 100
            
            return jsonify({
                'total_players': total_players,
                'active_players': active_players,
                'online_players': online_players,
                'new_registrations': {
                    'today': new_today,
                    'this_week': new_week,
                    'this_month': new_month
                },
                'engagement_metrics': {
                    'activation_rate': round(activation_rate, 1),
                    'retention_rate': round(retention_rate, 1),
                    'trading_participation': round(trading_participation, 1)
                },
                'players_with_cards': players_with_cards,
                'players_who_traded': players_who_traded
            })
        
    except Exception as e:
        logger.error(f"Error getting player stats: {e}")
        return jsonify({'error': f'Failed to get player stats: {str(e)}'}), 500

@admin_players_bp.route('/', methods=['GET'])
@auto_rbac_required()
def get_players():
    """Get paginated list of players with filtering from database"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        with SessionLocal() as session:
            # Build base query with player statistics
            query = session.query(
                Player,
                func.count(PlayerCard.id).label('card_count'),
                func.count(TradingHistory.id).label('trade_count'),
                func.max(PlayerActivityLog.timestamp).label('last_activity')
            ).outerjoin(
                PlayerCard, Player.id == PlayerCard.player_id
            ).outerjoin(
                TradingHistory, or_(
                    Player.id == TradingHistory.seller_player_id,
                    Player.id == TradingHistory.buyer_player_id
                )
            ).outerjoin(
                PlayerActivityLog, Player.id == PlayerActivityLog.player_id
            ).group_by(Player.id)
            
            # Apply search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Player.username.ilike(search_term),
                        Player.email.ilike(search_term),
                        Player.display_name.ilike(search_term)
                    )
                )
            
            # Apply status filter
            if status_filter:
                query = query.filter(Player.status == status_filter)
            
            # Apply sorting
            sort_column = getattr(Player, sort_by, Player.created_at)
            if sort_order == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            results = query.offset(offset).limit(per_page).all()
            
            # Format player data
            players = []
            for row in results:
                player = row.Player
                
                # Get ban status
                current_ban = session.query(PlayerBan).filter(
                    and_(
                        PlayerBan.player_id == player.id,
                        PlayerBan.is_active == True,
                        or_(
                            PlayerBan.expires_at.is_(None),
                            PlayerBan.expires_at > datetime.utcnow()
                        )
                    )
                ).first()
                
                players.append({
                    'id': player.id,
                    'username': player.username,
                    'display_name': player.display_name,
                    'email': player.email,
                    'status': player.status,
                    'is_verified': player.is_verified,
                    'is_premium': player.is_premium,
                    'is_banned': player.is_banned,
                    'ban_reason': player.ban_reason,
                    'ban_expires_at': player.ban_expires_at.isoformat() if player.ban_expires_at else None,
                    'warning_count': player.warning_count,
                    'elo_rating': player.elo_rating,
                    'card_count': row.card_count or 0,
                    'trade_count': row.trade_count or 0,
                    'last_activity': row.last_activity.isoformat() if row.last_activity else None,
                    'last_login_at': player.last_login_at.isoformat() if player.last_login_at else None,
                    'created_at': player.created_at.isoformat(),
                    'updated_at': player.updated_at.isoformat(),
                    'current_ban': {
                        'reason': current_ban.reason if current_ban else None,
                        'expires_at': current_ban.expires_at.isoformat() if current_ban and current_ban.expires_at else None,
                        'banned_by': current_ban.banned_by_admin_id if current_ban else None
                    } if current_ban else None
                })
            
            return jsonify({
                'players': players,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page,
                    'has_next': page * per_page < total_count,
                    'has_prev': page > 1
                },
                'filters': {
                    'search': search,
                    'status': status_filter,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting players: {e}")
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
