"""
Admin Cards Statistics API Routes
Provides real card statistics for admin panel
"""

from flask import Blueprint, request, jsonify
from shared.auth.decorators import admin_required
from shared.database.connection import SessionLocal
from sqlalchemy import text, func
import logging

logger = logging.getLogger(__name__)

admin_cards_stats_bp = Blueprint('admin_cards_stats', __name__, url_prefix='/v1/admin/cards')

@admin_cards_stats_bp.route('/stats', methods=['GET'])
@admin_required
def get_card_statistics():
    """Get real card statistics from database"""
    try:
        with SessionLocal() as session:
            # Get total cards
            total_result = session.execute(text("SELECT COUNT(*) FROM card_catalog"))
            total_cards = total_result.scalar() or 0
            
            # Get cards with graphics (check artwork_url and static_url)
            graphics_result = session.execute(text("""
                SELECT COUNT(*) FROM card_catalog 
                WHERE (artwork_url IS NOT NULL AND artwork_url != '') 
                   OR (static_url IS NOT NULL AND static_url != '')
            """))
            cards_with_graphics = graphics_result.scalar() or 0
            
            # Get cards with videos
            videos_result = session.execute(text("""
                SELECT COUNT(*) FROM card_catalog 
                WHERE video_url IS NOT NULL AND video_url != ''
            """))
            cards_with_videos = videos_result.scalar() or 0
            
            # Get rarity distribution
            rarity_result = session.execute(text("""
                SELECT rarity, COUNT(*) as count
                FROM card_catalog 
                GROUP BY rarity
            """))
            rarity_stats = {row[0]: row[1] for row in rarity_result}
            
            # Get color distribution (using mana_colors column)
            color_result = session.execute(text("""
                SELECT mana_colors, COUNT(*) as count
                FROM card_catalog 
                WHERE mana_colors IS NOT NULL AND mana_colors != '[]'
                GROUP BY mana_colors
            """))
            color_stats = {}
            for row in color_result:
                # mana_colors is a JSON array, extract first color for stats
                mana_colors = row[0]
                if mana_colors and mana_colors != '[]':
                    # Parse JSON array to get primary color
                    try:
                        import json
                        colors = json.loads(mana_colors) if isinstance(mana_colors, str) else mana_colors
                        if colors and len(colors) > 0:
                            primary_color = colors[0]
                            color_stats[primary_color] = color_stats.get(primary_color, 0) + row[1]
                    except:
                        pass
            
            # Get category distribution
            category_result = session.execute(text("""
                SELECT category, COUNT(*) as count
                FROM card_catalog 
                GROUP BY category
            """))
            category_stats = {row[0]: row[1] for row in category_result}
            
            # Get recent cards (last 20)
            recent_result = session.execute(text("""
                SELECT id, name, category, rarity, mana_colors, created_at
                FROM card_catalog 
                ORDER BY created_at DESC 
                LIMIT 20
            """))
            recent_cards = []
            for row in recent_result:
                recent_cards.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'rarity': row[3],
                    'color_code': row[4],  # This is actually mana_colors now
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return jsonify({
                'success': True,
                'total_cards': total_cards,
                'total_templates': total_cards,  # Template compatibility
                'published_templates': cards_with_graphics,  # Cards with graphics are "published"
                'draft_templates': total_cards - cards_with_graphics,  # Cards without graphics are "drafts"
                'nfc_instances': 0,  # Will be populated when NFC system is active
                'total_nfc_cards': 0,  # Will be populated when NFC system is active
                'cards_with_graphics': cards_with_graphics,
                'cards_with_videos': cards_with_videos,
                'cards_without_graphics': total_cards - cards_with_graphics,
                'graphics_completion_percent': round((cards_with_graphics / total_cards * 100), 1) if total_cards > 0 else 0,
                'videos_completion_percent': round((cards_with_videos / total_cards * 100), 1) if total_cards > 0 else 0,
                'by_rarity': {
                    'COMMON': rarity_stats.get('COMMON', 0),
                    'RARE': rarity_stats.get('RARE', 0),
                    'EPIC': rarity_stats.get('EPIC', 0),
                    'LEGENDARY': rarity_stats.get('LEGENDARY', 0)
                },
                'by_color': {
                    'CRIMSON': color_stats.get('CRIMSON', 0),
                    'AZURE': color_stats.get('AZURE', 0),
                    'VERDANT': color_stats.get('VERDANT', 0),
                    'OBSIDIAN': color_stats.get('OBSIDIAN', 0),
                    'RADIANT': color_stats.get('RADIANT', 0),
                    'AETHER': color_stats.get('AETHER', 0)
                },
                'by_category': {
                    'CREATURE': category_stats.get('CREATURE', 0),
                    'ACTION': category_stats.get('ACTION', 0),
                    'STRUCTURE': category_stats.get('STRUCTURE', 0),
                    'EQUIPMENT': category_stats.get('EQUIPMENT', 0),
                    'SPECIAL': category_stats.get('SPECIAL', 0)
                },
                'recent_cards': recent_cards
            })
            
    except Exception as e:
        logger.error(f"Error getting card statistics: {e}")
        return jsonify({'error': f'Failed to get card statistics: {str(e)}'}), 500


@admin_cards_stats_bp.route('/list', methods=['GET'])
@admin_required
def get_cards_list():
    """Get paginated list of cards"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 24))
        
        with SessionLocal() as session:
            # Get total count
            total_result = session.execute(text("SELECT COUNT(*) FROM card_catalog"))
            total_cards = total_result.scalar() or 0
            
            # Get paginated cards
            offset = (page - 1) * per_page
            cards_result = session.execute(text("""
                SELECT id, name, category, rarity, color_code, image_url, video_url, created_at
                FROM card_catalog 
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """), {'limit': per_page, 'offset': offset})
            
            cards = []
            for row in cards_result:
                cards.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'rarity': row[3],
                    'color_code': row[4],
                    'image_url': row[5],
                    'video_url': row[6],
                    'created_at': row[7].isoformat() if row[7] else None,
                    'has_graphics': bool(row[5]),
                    'has_video': bool(row[6])
                })
            
            return jsonify({
                'success': True,
                'cards': cards,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_cards,
                    'pages': (total_cards + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting cards list: {e}")
        return jsonify({'error': f'Failed to get cards list: {str(e)}'}), 500
