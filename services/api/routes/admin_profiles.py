"""
Admin User Profiles Routes
Admin endpoints for managing user profiles
"""

import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, g
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload

from shared.database.connection import SessionLocal
from shared.models.base import Player, NFCCard
from shared.models.shop import ShopOrder
from shared.models.tournaments import TournamentParticipant
from shared.auth.decorators import admin_required

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_profiles_bp = Blueprint('admin_profiles', __name__, url_prefix='/v1/admin/profiles')


@admin_profiles_bp.route('', methods=['GET'])
@admin_required
def get_user_profiles():
    """Get user profiles with statistics"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', 'all')
        
        with SessionLocal() as session:
            # Build base query
            query = session.query(Player)
            
            # Apply filters
            if search:
                query = query.filter(
                    or_(
                        Player.username.ilike(f'%{search}%'),
                        Player.email.ilike(f'%{search}%')
                    )
                )
            
            if status_filter != 'all':
                if hasattr(Player, 'status'):
                    query = query.filter(Player.status == status_filter)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            players = query.order_by(desc(Player.created_at)).offset(offset).limit(page_size).all()
            
            profiles = []
            for player in players:
                # Get player statistics
                card_count = session.query(NFCCard).filter(NFCCard.owner_player_id == player.id).count()
                order_count = session.query(ShopOrder).filter(ShopOrder.customer_id == player.id).count()
                tournament_count = session.query(TournamentParticipant).filter(
                    TournamentParticipant.player_id == player.id
                ).count()
                
                # Calculate total spent
                total_spent = session.query(func.coalesce(func.sum(ShopOrder.total_amount), 0)).filter(
                    ShopOrder.customer_id == player.id,
                    ShopOrder.order_status == 'completed'
                ).scalar() or 0
                
                profile_data = {
                    'id': player.id,
                    'username': player.username,
                    'email': player.email,
                    'status': getattr(player, 'status', 'active'),
                    'is_banned': getattr(player, 'is_banned', False),
                    'warning_count': getattr(player, 'warning_count', 0),
                    'created_at': player.created_at.isoformat() if player.created_at else None,
                    'last_login_at': player.last_login_at.isoformat() if getattr(player, 'last_login_at', None) else None,
                    'statistics': {
                        'cards_owned': card_count,
                        'orders_placed': order_count,
                        'tournaments_joined': tournament_count,
                        'total_spent': float(total_spent)
                    }
                }
                profiles.append(profile_data)
            
            total_pages = (total + page_size - 1) // page_size
            
            return jsonify({
                'profiles': profiles,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting user profiles: {e}")
        return jsonify({'error': str(e)}), 500


@admin_profiles_bp.route('/<int:player_id>', methods=['GET'])
@admin_required
def get_user_profile_detail(player_id):
    """Get detailed user profile"""
    try:
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == player_id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # Get detailed statistics
            cards = session.query(NFCCard).filter(NFCCard.owner_player_id == player.id).all()
            orders = session.query(ShopOrder).filter(ShopOrder.customer_id == player.id).order_by(desc(ShopOrder.created_at)).limit(10).all()
            tournaments = session.query(TournamentParticipant).filter(
                TournamentParticipant.player_id == player.id
            ).order_by(desc(TournamentParticipant.registered_at)).limit(10).all()
            
            # Recent activity
            recent_cards = [
                {
                    'card_uid': card.card_uid,
                    'status': card.status,
                    'activated_at': card.activated_at.isoformat() if card.activated_at else None
                }
                for card in cards[-5:]  # Last 5 cards
            ]
            
            recent_orders = [
                {
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount),
                    'status': order.order_status,
                    'created_at': order.created_at.isoformat()
                }
                for order in orders
            ]
            
            return jsonify({
                'profile': {
                    'id': player.id,
                    'username': player.username,
                    'email': player.email,
                    'status': getattr(player, 'status', 'active'),
                    'is_banned': getattr(player, 'is_banned', False),
                    'warning_count': getattr(player, 'warning_count', 0),
                    'created_at': player.created_at.isoformat() if player.created_at else None,
                    'last_login_at': player.last_login_at.isoformat() if getattr(player, 'last_login_at', None) else None,
                },
                'statistics': {
                    'cards_owned': len(cards),
                    'orders_placed': len(orders),
                    'tournaments_joined': len(tournaments)
                },
                'recent_activity': {
                    'recent_cards': recent_cards,
                    'recent_orders': recent_orders
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting user profile detail: {e}")
        return jsonify({'error': str(e)}), 500
