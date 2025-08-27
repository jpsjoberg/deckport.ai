"""
User Profile and Dashboard API Routes
Handles user profile, inventory, analytics, and personal data management
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload
import logging

from shared.database.connection import SessionLocal
from shared.models.base import Player, Match, MatchParticipant, Console
from shared.models.nfc_trading_system import (
    EnhancedNFCCard, TradeOffer, CardAuction, TradingHistory,
    TradeStatus, TradeType, AuctionStatus
)
from shared.models.shop import ShopOrder, ShopOrderItem
from shared.auth.decorators import player_required

logger = logging.getLogger(__name__)

user_profile_bp = Blueprint('user_profile', __name__, url_prefix='/v1/me')

# === USER PROFILE ===

@user_profile_bp.route('', methods=['GET'])
@player_required
def get_user_profile():
    """Get user profile and dashboard data"""
    try:
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == g.current_player.id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # Get card statistics
            total_cards = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.owner_player_id == player.id,
                EnhancedNFCCard.status == NFCCardStatus.activated
            ).count()
            
            # Get recent matches
            recent_matches = session.query(Match).join(MatchParticipant).filter(
                MatchParticipant.player_id == player.id
            ).order_by(desc(Match.created_at)).limit(5).all()
            
            # Get active trades
            active_trades = session.query(CardTrade).filter(
                or_(
                    CardTrade.seller_player_id == player.id,
                    CardTrade.buyer_player_id == player.id
                ),
                CardTrade.status == TradeStatus.pending
            ).count()
            
            # Get recent orders
            recent_orders = session.query(ShopOrder).filter(
                ShopOrder.customer_id == player.id
            ).order_by(desc(ShopOrder.created_at)).limit(3).all()
            
            # Calculate win rate
            match_results = session.query(MatchParticipant.result).filter(
                MatchParticipant.player_id == player.id
            ).all()
            
            wins = sum(1 for r in match_results if r[0].value == 'win')
            total_matches = len(match_results)
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            
            return jsonify({
                'profile': {
                    'id': player.id,
                    'email': player.email,
                    'display_name': player.display_name,
                    'username': player.username,
                    'avatar_url': player.avatar_url,
                    'elo_rating': player.elo_rating,
                    'created_at': player.created_at.isoformat(),
                    'updated_at': player.updated_at.isoformat()
                },
                'stats': {
                    'total_cards': total_cards,
                    'total_matches': total_matches,
                    'win_rate': round(win_rate, 1),
                    'active_trades': active_trades,
                    'total_orders': len(recent_orders)
                },
                'recent_activity': {
                    'matches': [{
                        'id': match.id,
                        'created_at': match.created_at.isoformat(),
                        'status': match.status.value,
                        'participant_count': len(match.participants)
                    } for match in recent_matches],
                    'orders': [{
                        'id': order.id,
                        'order_number': order.order_number,
                        'total_amount': float(order.total_amount),
                        'status': order.order_status.value,
                        'created_at': order.created_at.isoformat()
                    } for order in recent_orders]
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@user_profile_bp.route('', methods=['PATCH'])
@player_required
def update_user_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            player = session.query(Player).filter(Player.id == g.current_player.id).first()
            
            if not player:
                return jsonify({'error': 'Player not found'}), 404
            
            # Update allowed fields
            if 'display_name' in data:
                player.display_name = data['display_name'].strip()
            if 'username' in data:
                # Check if username is unique
                existing = session.query(Player).filter(
                    Player.username == data['username'],
                    Player.id != player.id
                ).first()
                if existing:
                    return jsonify({'error': 'Username already taken'}), 400
                player.username = data['username'].strip()
            if 'avatar_url' in data:
                player.avatar_url = data['avatar_url']
            
            player.updated_at = datetime.now(timezone.utc)
            session.commit()
            
            return jsonify({
                'success': True,
                'profile': {
                    'id': player.id,
                    'display_name': player.display_name,
                    'username': player.username,
                    'avatar_url': player.avatar_url,
                    'updated_at': player.updated_at.isoformat()
                }
            })
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

# === USER INVENTORY ===

@user_profile_bp.route('/cards', methods=['GET'])
@player_required
def get_user_cards():
    """Get user's card collection"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        search = request.args.get('search', '').strip()
        rarity = request.args.get('rarity', '').upper()
        sort_by = request.args.get('sort_by', 'activated_at')  # activated_at, tap_counter, level
        
        with SessionLocal() as session:
            # Build query
            query = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.owner_player_id == g.current_player.id,
                EnhancedNFCCard.status == NFCCardStatus.activated
            ).options(joinedload(EnhancedNFCCard.public_page))
            
            # Apply filters
            if search:
                query = query.filter(
                    or_(
                        EnhancedNFCCard.product_sku.ilike(f'%{search}%'),
                        EnhancedNFCCard.serial_number.ilike(f'%{search}%')
                    )
                )
            
            # Apply sorting
            if sort_by == 'tap_counter':
                query = query.order_by(desc(EnhancedNFCCard.tap_counter))
            elif sort_by == 'level':
                # Sort by highest level from upgrades (subquery)
                latest_upgrade_subquery = session.query(
                    CardUpgrade.nfc_card_id,
                    func.max(CardUpgrade.new_level).label('max_level')
                ).group_by(CardUpgrade.nfc_card_id).subquery()
                
                query = query.outerjoin(
                    latest_upgrade_subquery,
                    EnhancedNFCCard.id == latest_upgrade_subquery.c.nfc_card_id
                ).order_by(desc(func.coalesce(latest_upgrade_subquery.c.max_level, 1)))
            else:  # activated_at
                query = query.order_by(desc(EnhancedNFCCard.activated_at))
            
            # Get total count
            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            
            # Apply pagination
            cards = query.offset((page - 1) * page_size).limit(page_size).all()
            
            # Format response
            cards_data = []
            for card in cards:
                # Get recent upgrades
                recent_upgrades = session.query(CardUpgrade).filter(
                    CardUpgrade.nfc_card_id == card.id
                ).order_by(desc(CardUpgrade.upgraded_at)).limit(3).all()
                
                # Calculate current level from upgrades
                latest_upgrade = session.query(CardUpgrade).filter(
                    CardUpgrade.nfc_card_id == card.id
                ).order_by(desc(CardUpgrade.upgraded_at)).first()
                current_level = latest_upgrade.new_level if latest_upgrade else 1
                
                cards_data.append({
                    'id': card.id,
                    'product_sku': card.product_sku,
                    'serial_number': card.serial_number,
                    'current_level': current_level,
                    'current_xp': card.tap_counter,  # Use tap_counter as XP proxy
                    'tap_counter': card.tap_counter,
                    'activated_at': card.activated_at.isoformat() if card.activated_at else None,
                    'last_used_at': card.updated_at.isoformat() if card.updated_at else None,  # Use updated_at as proxy
                    'public_url': f"/cards/public/{card.public_page.public_slug}" if card.public_page else None,
                    'recent_upgrades': [{
                        'type': upgrade.upgrade_type,
                        'old_level': upgrade.old_level,
                        'new_level': upgrade.new_level,
                        'upgraded_at': upgrade.upgraded_at.isoformat()
                    } for upgrade in recent_upgrades]
                })
            
            return jsonify({
                'cards': cards_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            })
            
    except Exception as e:
        logger.error(f"Error getting user cards: {e}")
        return jsonify({'error': 'Failed to get cards'}), 500

# === USER ANALYTICS ===

@user_profile_bp.route('/analytics', methods=['GET'])
@player_required
def get_user_analytics():
    """Get user analytics and performance data"""
    try:
        with SessionLocal() as session:
            # Get match statistics
            matches = session.query(MatchParticipant).filter(
                MatchParticipant.player_id == g.current_player.id
            ).order_by(desc(MatchParticipant.joined_at)).all()
            
            # Calculate statistics
            total_matches = len(matches)
            wins = sum(1 for m in matches if m.result.value == 'win')
            losses = sum(1 for m in matches if m.result.value == 'loss')
            draws = sum(1 for m in matches if m.result.value == 'draw')
            
            # ELO history (last 30 matches)
            elo_history = []
            current_elo = g.current_player.elo_rating
            for match in matches[:30]:
                elo_history.append({
                    'match_id': match.match_id,
                    'date': match.joined_at.isoformat(),
                    'elo_change': match.elo_change or 0,
                    'elo_after': current_elo
                })
                current_elo -= (match.elo_change or 0)
            
            # Card usage statistics
            card_stats = session.query(
                EnhancedNFCCard.product_sku,
                func.sum(EnhancedNFCCard.tap_counter).label('total_taps'),
                func.count(EnhancedNFCCard.id).label('card_count')
            ).filter(
                EnhancedNFCCard.owner_player_id == g.current_player.id
            ).group_by(EnhancedNFCCard.product_sku).all()
            
            # Recent activity timeline
            recent_activity = []
            
            # Add recent matches
            for match in matches[:10]:
                recent_activity.append({
                    'type': 'match',
                    'date': match.joined_at.isoformat(),
                    'data': {
                        'match_id': match.match_id,
                        'result': match.result.value,
                        'elo_change': match.elo_change
                    }
                })
            
            # Add recent card activations
            recent_cards = session.query(EnhancedNFCCard).filter(
                EnhancedNFCCard.owner_player_id == g.current_player.id,
                EnhancedNFCCard.activated_at.isnot(None)
            ).order_by(desc(EnhancedNFCCard.activated_at)).limit(5).all()
            
            for card in recent_cards:
                recent_activity.append({
                    'type': 'card_activation',
                    'date': card.activated_at.isoformat(),
                    'data': {
                        'card_id': card.id,
                        'product_sku': card.product_sku,
                        'serial_number': card.serial_number
                    }
                })
            
            # Sort activity by date
            recent_activity.sort(key=lambda x: x['date'], reverse=True)
            
            return jsonify({
                'match_statistics': {
                    'total_matches': total_matches,
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'win_rate': round((wins / total_matches * 100) if total_matches > 0 else 0, 1)
                },
                'elo_history': elo_history,
                'card_statistics': [{
                    'product_sku': stat.product_sku,
                    'total_taps': int(stat.total_taps or 0),
                    'card_count': int(stat.card_count)
                } for stat in card_stats],
                'recent_activity': recent_activity[:20]
            })
            
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return jsonify({'error': 'Failed to get analytics'}), 500

# === USER ORDERS ===

@user_profile_bp.route('/orders', methods=['GET'])
@player_required
def get_user_orders():
    """Get user's order history"""
    try:
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 10)), 50)
        
        with SessionLocal() as session:
            query = session.query(ShopOrder).filter(
                ShopOrder.customer_id == g.current_player.id
            ).options(joinedload(ShopOrder.order_items))
            
            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            
            orders = query.order_by(desc(ShopOrder.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount),
                    'currency': order.currency,
                    'order_status': order.order_status.value,
                    'payment_status': order.payment_status.value,
                    'shipping_status': order.shipping_status.value,
                    'created_at': order.created_at.isoformat(),
                    'items': [{
                        'product_name': item.product_name,
                        'product_sku': item.product_sku,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_price': float(item.total_price)
                    } for item in order.order_items]
                })
            
            return jsonify({
                'orders': orders_data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            })
            
    except Exception as e:
        logger.error(f"Error getting user orders: {e}")
        return jsonify({'error': 'Failed to get orders'}), 500
