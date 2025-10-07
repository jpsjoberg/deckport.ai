"""
Card catalog routes
"""

from flask import Blueprint, request, jsonify
from shared.database.connection import SessionLocal
from shared.models.base import CardCatalog
from sqlalchemy import Integer, cast, func

cards_bp = Blueprint('cards', __name__, url_prefix='/v1/catalog')

@cards_bp.route('/cards', methods=['GET'])
def list_cards():
    """Get card catalog with advanced filtering"""
    # Get query parameters
    q = request.args.get('q', '').lower().strip()
    category = request.args.get('category', '').upper()
    color = request.args.get('color', '').upper()  
    rarity = request.args.get('rarity', '').upper()
    card_set = request.args.get('card_set', '').lower().strip()
    
    # Advanced filters
    mana_cost_min = request.args.get('mana_cost_min', type=int)
    mana_cost_max = request.args.get('mana_cost_max', type=int)
    energy_cost_min = request.args.get('energy_cost_min', type=int)
    energy_cost_max = request.args.get('energy_cost_max', type=int)
    attack_min = request.args.get('attack_min', type=int)
    attack_max = request.args.get('attack_max', type=int)
    health_min = request.args.get('health_min', type=int)
    health_max = request.args.get('health_max', type=int)
    has_artwork = request.args.get('has_artwork')
    has_video = request.args.get('has_video')
    
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 20)), 100)  # Max 100 items per page
    
    try:
        with SessionLocal() as session:
            # Build query
            query = session.query(CardCatalog)
            
            # Apply basic filters
            if q:
                query = query.filter(CardCatalog.name.ilike(f'%{q}%'))
            if category:
                query = query.filter(CardCatalog.category == category)
            if rarity:
                query = query.filter(CardCatalog.rarity == rarity)
            if color:
                query = query.filter(CardCatalog.mana_colors.contains([color]))
            if card_set:
                query = query.filter(CardCatalog.card_set_id == card_set)
            
            # Apply advanced stat filters using JSON operators
            if mana_cost_min is not None:
                query = query.filter(cast(CardCatalog.base_stats['mana_cost'], Integer) >= mana_cost_min)
            if mana_cost_max is not None:
                query = query.filter(cast(CardCatalog.base_stats['mana_cost'], Integer) <= mana_cost_max)
            if energy_cost_min is not None:
                query = query.filter(cast(CardCatalog.base_stats['energy_cost'], Integer) >= energy_cost_min)
            if energy_cost_max is not None:
                query = query.filter(cast(CardCatalog.base_stats['energy_cost'], Integer) <= energy_cost_max)
            if attack_min is not None:
                query = query.filter(cast(CardCatalog.base_stats['attack'], Integer) >= attack_min)
            if attack_max is not None:
                query = query.filter(cast(CardCatalog.base_stats['attack'], Integer) <= attack_max)
            if health_min is not None:
                query = query.filter(cast(CardCatalog.base_stats['health'], Integer) >= health_min)
            if health_max is not None:
                query = query.filter(cast(CardCatalog.base_stats['health'], Integer) <= health_max)
            
            # Apply asset filters
            if has_artwork == 'true':
                query = query.filter(CardCatalog.artwork_url.isnot(None))
            elif has_artwork == 'false':
                query = query.filter(CardCatalog.artwork_url.is_(None))
            
            if has_video == 'true':
                query = query.filter(CardCatalog.video_url.isnot(None))
            elif has_video == 'false':
                query = query.filter(CardCatalog.video_url.is_(None))
            
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
                    "artwork_url": card.artwork_url,
                    "static_url": card.static_url,
                    "video_url": card.video_url,
                    "has_animation": card.has_animation,
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
                "rarity": card.rarity.value if hasattr(card.rarity, 'value') else str(card.rarity),
                "category": card.category.value if hasattr(card.category, 'value') else str(card.category),
                "subtype": card.subtype,
                "base_stats": card.base_stats,
                "attachment_rules": card.attachment_rules,
                "duration": card.duration,
                "token_spec": card.token_spec,
                "artwork_url": card.artwork_url,
                "static_url": card.static_url,
                "video_url": card.video_url,
                "has_animation": card.has_animation,
                "rules_text": card.rules_text,
                "flavor_text": card.flavor_text,
                "display_label": getattr(card, 'display_label', card.name),
                "created_at": card.created_at.isoformat()
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to fetch card"}), 500

@cards_bp.route('/filters', methods=['GET'])
def get_filter_options():
    """Get available filter options for the card catalog"""
    try:
        with SessionLocal() as session:
            from sqlalchemy import text, distinct
            
            # Get available categories
            categories = session.execute(text(
                "SELECT DISTINCT category FROM card_catalog ORDER BY category"
            )).fetchall()
            
            # Get available rarities
            rarities = session.execute(text(
                "SELECT DISTINCT rarity FROM card_catalog ORDER BY rarity"
            )).fetchall()
            
            # Get available mana colors
            colors = session.execute(text("""
                SELECT DISTINCT unnest(mana_colors) as color 
                FROM card_catalog 
                WHERE mana_colors IS NOT NULL 
                ORDER BY color
            """)).fetchall()
            
            # Get available card sets
            card_sets = session.execute(text(
                "SELECT DISTINCT card_set_id FROM card_catalog WHERE card_set_id IS NOT NULL ORDER BY card_set_id"
            )).fetchall()
            
            # Get stat ranges
            stat_ranges = session.execute(text("""
                SELECT 
                    MIN(CAST(base_stats->>'mana_cost' AS INTEGER)) as min_mana,
                    MAX(CAST(base_stats->>'mana_cost' AS INTEGER)) as max_mana,
                    MIN(CAST(base_stats->>'energy_cost' AS INTEGER)) as min_energy,
                    MAX(CAST(base_stats->>'energy_cost' AS INTEGER)) as max_energy,
                    MIN(CAST(base_stats->>'attack' AS INTEGER)) as min_attack,
                    MAX(CAST(base_stats->>'attack' AS INTEGER)) as max_attack,
                    MIN(CAST(base_stats->>'health' AS INTEGER)) as min_health,
                    MAX(CAST(base_stats->>'health' AS INTEGER)) as max_health
                FROM card_catalog 
                WHERE base_stats IS NOT NULL
            """)).fetchone()
            
            return jsonify({
                "categories": [cat[0] for cat in categories],
                "rarities": [rar[0] for rar in rarities],
                "colors": [col[0] for col in colors],
                "card_sets": [cs[0] for cs in card_sets],
                "stat_ranges": {
                    "mana_cost": {"min": stat_ranges[0] or 0, "max": stat_ranges[1] or 10},
                    "energy_cost": {"min": stat_ranges[2] or 0, "max": stat_ranges[3] or 6},
                    "attack": {"min": stat_ranges[4] or 0, "max": stat_ranges[5] or 15},
                    "health": {"min": stat_ranges[6] or 0, "max": stat_ranges[7] or 20}
                }
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to fetch filter options"}), 500
