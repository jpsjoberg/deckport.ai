"""
Card catalog routes
"""

from flask import Blueprint, request, jsonify
from shared.database.connection import SessionLocal
from shared.models.base import CardCatalog

cards_bp = Blueprint('cards', __name__, url_prefix='/v1/catalog')

@cards_bp.route('/cards', methods=['GET'])
def list_cards():
    """Get card catalog with filtering"""
    # Get query parameters
    q = request.args.get('q', '').lower().strip()
    category = request.args.get('category', '').upper()
    color = request.args.get('color', '').upper()  
    rarity = request.args.get('rarity', '').upper()
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 20)), 100)  # Max 100 items per page
    
    try:
        with SessionLocal() as session:
            # Build query
            query = session.query(CardCatalog)
            
            # Apply filters
            if q:
                query = query.filter(CardCatalog.name.ilike(f'%{q}%'))
            if category:
                query = query.filter(CardCatalog.category == category)
            if rarity:
                query = query.filter(CardCatalog.rarity == rarity)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            cards = query.offset(offset).limit(page_size).all()
            
            # Format response
            items = []
            for card in cards:
                items.append({
                    "product_sku": card.product_sku,
                    "name": card.name,
                    "rarity": card.rarity.value if hasattr(card.rarity, 'value') else str(card.rarity),
                    "category": card.category.value if hasattr(card.category, 'value') else str(card.category),
                    "subtype": card.subtype,
                    "base_stats": card.base_stats,
                    "display_label": getattr(card, 'display_label', card.name)
                })
            
            return jsonify({
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": offset + len(items) < total
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to fetch cards"}), 500

@cards_bp.route('/cards/<product_sku>', methods=['GET'])
def get_card(product_sku):
    """Get detailed card information"""
    try:
        with SessionLocal() as session:
            card = session.query(CardCatalog).filter(
                CardCatalog.product_sku == product_sku.upper()
            ).first()
            
            if not card:
                return jsonify({"error": "Card not found"}), 404
            
            return jsonify({
                "product_sku": card.product_sku,
                "name": card.name,
                "rarity": card.rarity.value,
                "category": card.category.value,
                "subtype": card.subtype,
                "base_stats": card.base_stats,
                "attachment_rules": card.attachment_rules,
                "duration": card.duration,
                "token_spec": card.token_spec,
                "reveal_trigger": card.reveal_trigger,
                "display_label": card.display_label,
                "created_at": card.created_at.isoformat()
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to fetch card"}), 500
