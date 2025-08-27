"""
NFC Card Admin Routes
Admin endpoints for NFC card management and statistics
"""

import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, g
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload

from shared.database.connection import SessionLocal
from shared.models.base import NFCCard, CardCatalog, Player
from shared.models.nfc_trading_system import EnhancedNFCCard, TradeOffer, CardAuction, TradingHistory
from shared.auth.decorators import admin_required

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
nfc_admin_bp = Blueprint('nfc_admin', __name__, url_prefix='/v1/nfc-cards/admin')


@nfc_admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_nfc_card_statistics():
    """Get comprehensive NFC card statistics"""
    try:
        with SessionLocal() as session:
            # Basic card counts
            total_cards = session.query(NFCCard).count()
            activated_cards = session.query(NFCCard).filter(NFCCard.status == 'activated').count()
            provisioned_cards = session.query(NFCCard).filter(NFCCard.status == 'provisioned').count()
            sold_cards = session.query(NFCCard).filter(NFCCard.status == 'sold').count()
            revoked_cards = session.query(NFCCard).filter(NFCCard.status == 'revoked').count()
            
            # Enhanced NFC cards
            enhanced_cards = session.query(EnhancedNFCCard).count()
            
            # Trading statistics
            total_trades = session.query(TradingHistory).count()
            active_trade_offers = session.query(TradeOffer).filter(TradeOffer.status == 'PENDING').count()
            active_auctions = session.query(CardAuction).filter(CardAuction.status == 'ACTIVE').count()
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_activations = session.query(NFCCard).filter(
                NFCCard.activated_at >= yesterday
            ).count()
            
            recent_trades = session.query(TradingHistory).filter(
                TradingHistory.traded_at >= yesterday
            ).count()
            
            # Card distribution by rarity
            rarity_stats = session.query(
                CardCatalog.rarity,
                func.count(NFCCard.id).label('count')
            ).join(
                NFCCard, CardCatalog.id == NFCCard.card_template_id
            ).group_by(CardCatalog.rarity).all()
            
            rarity_distribution = {}
            for rarity, count in rarity_stats:
                rarity_key = rarity.value if hasattr(rarity, 'value') else str(rarity)
                rarity_distribution[rarity_key] = count
            
            # Top traded cards (by volume)
            top_traded = session.query(
                CardCatalog.name,
                CardCatalog.product_sku,
                func.count(TradingHistory.id).label('trade_count')
            ).join(
                NFCCard, CardCatalog.id == NFCCard.card_template_id
            ).join(
                TradingHistory, TradingHistory.card_id == NFCCard.id
            ).group_by(
                CardCatalog.id, CardCatalog.name, CardCatalog.product_sku
            ).order_by(desc('trade_count')).limit(10).all()
            
            top_traded_list = []
            for card_name, product_sku, trade_count in top_traded:
                top_traded_list.append({
                    'name': card_name,
                    'product_sku': product_sku,
                    'trade_count': trade_count
                })
            
            # Player engagement
            players_with_cards = session.query(NFCCard.owner_player_id).filter(NFCCard.owner_player_id.isnot(None)).distinct().count()
            players_trading = session.query(TradingHistory.seller_player_id).distinct().count()
            
            return jsonify({
                'card_statistics': {
                    'total_cards': total_cards,
                    'activated_cards': activated_cards,
                    'provisioned_cards': provisioned_cards,
                    'sold_cards': sold_cards,
                    'revoked_cards': revoked_cards,
                    'enhanced_cards': enhanced_cards,
                    'activation_rate': round((activated_cards / total_cards * 100) if total_cards > 0 else 0, 1)
                },
                'trading_statistics': {
                    'total_trades': total_trades,
                    'active_trade_offers': active_trade_offers,
                    'active_auctions': active_auctions,
                    'recent_trades_24h': recent_trades
                },
                'recent_activity': {
                    'activations_24h': recent_activations,
                    'trades_24h': recent_trades
                },
                'rarity_distribution': rarity_distribution,
                'top_traded_cards': top_traded_list,
                'player_engagement': {
                    'players_with_cards': players_with_cards,
                    'players_trading': players_trading,
                    'trading_participation': round((players_trading / players_with_cards * 100) if players_with_cards > 0 else 0, 1)
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting NFC card statistics: {e}")
        return jsonify({'error': str(e)}), 500


@nfc_admin_bp.route('/recent-activity', methods=['GET'])
@admin_required
def get_recent_nfc_activity():
    """Get recent NFC card activity"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))
        
        with SessionLocal() as session:
            # Recent activations
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            recent_activations = session.query(NFCCard).options(
                joinedload(NFCCard.card_template),
                joinedload(NFCCard.owner)
            ).filter(
                NFCCard.activated_at >= cutoff_date
            ).order_by(desc(NFCCard.activated_at)).limit(limit).all()
            
            activations = []
            for card in recent_activations:
                activations.append({
                    'card_id': card.id,
                    'card_uid': card.card_uid,
                    'card_name': card.card_template.name if card.card_template else 'Unknown',
                    'product_sku': card.card_template.product_sku if card.card_template else 'Unknown',
                    'owner_username': card.owner.username if card.owner else 'Unknown',
                    'activated_at': card.activated_at.isoformat() if card.activated_at else None
                })
            
            # Recent trades - simplified without relationships for now
            recent_trades = session.query(TradingHistory).filter(
                TradingHistory.traded_at >= cutoff_date
            ).order_by(desc(TradingHistory.traded_at)).limit(limit).all()
            
            trades = []
            for trade in recent_trades:
                trades.append({
                    'trade_id': trade.id,
                    'seller_player_id': trade.seller_player_id,
                    'buyer_player_id': trade.buyer_player_id,
                    'trade_type': trade.trade_type.value if hasattr(trade.trade_type, 'value') else str(trade.trade_type),
                    'price': float(trade.price) if trade.price else None,
                    'traded_at': trade.traded_at.isoformat() if trade.traded_at else None
                })
            
            return jsonify({
                'recent_activations': activations,
                'recent_trades': trades,
                'period_days': days
            })
            
    except Exception as e:
        logger.error(f"Error getting recent NFC activity: {e}")
        return jsonify({'error': str(e)}), 500
