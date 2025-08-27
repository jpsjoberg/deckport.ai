"""
Card Pack API for Console Loading
Provides card data and images in optimized packages for console caching
"""

from flask import Blueprint, jsonify, request
import json
import hashlib
import base64
import os
from datetime import datetime
from shared.database.connection import SessionLocal
from shared.models.base import CardCatalog
from sqlalchemy import func, text
import logging

logger = logging.getLogger(__name__)

card_pack_bp = Blueprint('card_pack', __name__, url_prefix='/api/v1/cards')

@card_pack_bp.route('/version', methods=['GET'])
def get_card_pack_version():
    """Get current card pack version for update checking"""
    
    try:
        with SessionLocal() as session:
            # Get latest update timestamp from cards
            latest_update = session.query(func.max(CardCatalog.created_at)).scalar()
            
            if not latest_update:
                version = "empty"
            else:
                # Generate version hash from timestamp
                version = hashlib.md5(str(latest_update).encode()).hexdigest()[:8]
            
            # Get card count for additional info
            card_count = session.query(func.count(CardCatalog.id)).scalar()
            
            return jsonify({
                "version": version,
                "card_count": card_count,
                "last_updated": latest_update.isoformat() if latest_update else None,
                "generated_at": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error getting card pack version: {e}")
        return jsonify({"error": "Failed to get version"}), 500

@card_pack_bp.route('/pack', methods=['GET'])
def get_card_pack():
    """
    Get complete card pack for console download
    Includes all published cards with embedded images
    """
    
    include_images = request.args.get('include_images', 'true').lower() == 'true'
    
    try:
        with SessionLocal() as session:
            # Get all cards from catalog
            cards = session.query(CardCatalog).order_by(CardCatalog.product_sku).all()
            
            # Generate version
            if cards:
                latest_update = max(card.updated_at for card in cards)
                version = hashlib.md5(str(latest_update).encode()).hexdigest()[:8]
            else:
                version = "empty"
            
            # Build card pack
            card_pack = {
                "version": version,
                "generated_at": datetime.now().isoformat(),
                "card_count": len(cards),
                "cards": [],
                "images": {} if include_images else None
            }
            
            for card in cards:
                # Card data for gameplay
                card_data = {
                    "product_sku": card.product_sku,
                    "name": card.name,
                    "description": card.description,
                    "flavor_text": card.flavor_text,
                    "rarity": card.rarity,
                    "category": card.category,
                    "color_code": card.color_code,
                    "base_stats": card.base_stats,
                    "attachment_rules": card.attachment_rules,
                    "duration": card.duration,
                    "token_spec": card.token_spec,
                    "reveal_trigger": card.reveal_trigger,
                    "display_label": card.display_label,
                    "image_url": card.image_url,
                    "thumbnail_url": card.thumbnail_url
                }
                card_pack["cards"].append(card_data)
                
                # Include base64 encoded image for offline use
                if include_images and card.image_url:
                    image_path = get_image_file_path(card.image_url)
                    if image_path and os.path.exists(image_path):
                        try:
                            with open(image_path, "rb") as img_file:
                                image_data = base64.b64encode(img_file.read()).decode()
                                card_pack["images"][card.product_sku] = image_data
                        except Exception as e:
                            logger.warning(f"Could not load image for {card.product_sku}: {e}")
            
            logger.info(f"Generated card pack v{version} with {len(cards)} cards")
            return jsonify(card_pack)
            
    except Exception as e:
        logger.error(f"Error generating card pack: {e}")
        return jsonify({"error": "Failed to generate card pack"}), 500

@card_pack_bp.route('/pack/lite', methods=['GET'])
def get_card_pack_lite():
    """
    Get lightweight card pack without images
    For quick updates or bandwidth-limited connections
    """
    
    try:
        with SessionLocal() as session:
            cards = session.query(CardProduct).filter(
                CardProduct.is_published == True
            ).order_by(CardProduct.product_sku).all()
            
            # Generate version
            if cards:
                latest_update = max(card.updated_at for card in cards)
                version = hashlib.md5(str(latest_update).encode()).hexdigest()[:8]
            else:
                version = "empty"
            
            card_pack = {
                "version": version,
                "generated_at": datetime.now().isoformat(),
                "card_count": len(cards),
                "cards": []
            }
            
            for card in cards:
                # Minimal card data
                card_data = {
                    "product_sku": card.product_sku,
                    "name": card.name,
                    "description": card.description,
                    "rarity": card.rarity,
                    "category": card.category,
                    "color_code": card.color_code,
                    "base_stats": card.base_stats,
                    "image_url": card.image_url  # URL only, no embedded image
                }
                card_pack["cards"].append(card_data)
            
            return jsonify(card_pack)
            
    except Exception as e:
        logger.error(f"Error generating lite card pack: {e}")
        return jsonify({"error": "Failed to generate lite card pack"}), 500

@card_pack_bp.route('/image/<product_sku>', methods=['GET'])
def get_card_image(product_sku):
    """
    Get individual card image
    Fallback for when console needs specific images
    """
    
    try:
        with SessionLocal() as session:
            card = session.query(CardProduct).filter(
                CardProduct.product_sku == product_sku,
                CardProduct.is_published == True
            ).first()
            
            if not card or not card.image_url:
                return jsonify({"error": "Card or image not found"}), 404
            
            image_path = get_image_file_path(card.image_url)
            if not image_path or not os.path.exists(image_path):
                return jsonify({"error": "Image file not found"}), 404
            
            # Return image as base64
            with open(image_path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode()
                
            return jsonify({
                "product_sku": product_sku,
                "image_data": image_data,
                "content_type": "image/png"  # Assume PNG for now
            })
            
    except Exception as e:
        logger.error(f"Error getting card image {product_sku}: {e}")
        return jsonify({"error": "Failed to get card image"}), 500

@card_pack_bp.route('/stats', methods=['GET'])
def get_card_pack_stats():
    """Get statistics about the card pack"""
    
    try:
        with SessionLocal() as session:
            stats = {
                "total_cards": session.query(func.count(CardCatalog.id)).scalar(),
                "published_cards": session.query(func.count(CardCatalog.id)).scalar(),
                "cards_with_images": session.query(func.count(CardCatalog.id)).filter(
                    CardCatalog.image_url.isnot(None)
                ).scalar()
            }
            
            # Get breakdown by rarity
            rarity_stats = session.execute(text("""
                SELECT rarity, COUNT(*) as count
                FROM card_catalog 
                GROUP BY rarity
                ORDER BY rarity
            """)).fetchall()
            
            stats["by_rarity"] = {row.rarity: row.count for row in rarity_stats}
            
            # Get breakdown by category
            category_stats = session.execute(text("""
                SELECT category, COUNT(*) as count
                FROM card_catalog 
                GROUP BY category
                ORDER BY category
            """)).fetchall()
            
            stats["by_category"] = {row.category: row.count for row in category_stats}
            
            return jsonify(stats)
            
    except Exception as e:
        logger.error(f"Error getting card pack stats: {e}")
        return jsonify({"error": "Failed to get stats"}), 500

def get_image_file_path(image_url):
    """Convert image URL to file system path"""
    if not image_url:
        return None
    
    # Remove leading slash and convert to file path
    if image_url.startswith('/static/'):
        relative_path = image_url[8:]  # Remove '/static/'
        return os.path.join('/home/jp/deckport.ai/frontend/static', relative_path)
    elif image_url.startswith('/'):
        return os.path.join('/home/jp/deckport.ai/frontend/static', image_url[1:])
    else:
        return os.path.join('/home/jp/deckport.ai/frontend/static', image_url)

# Health check for card pack system
@card_pack_bp.route('/health', methods=['GET'])
def card_pack_health():
    """Health check for card pack system"""
    
    try:
        with SessionLocal() as session:
            card_count = session.query(func.count(CardCatalog.id)).scalar()
            
            return jsonify({
                "status": "healthy",
                "published_cards": card_count,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Card pack health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
