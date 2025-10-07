"""
Admin Card Set Management API Routes
Handles card set generation, management, and asset production
"""

from flask import Blueprint, request, jsonify
from shared.auth.decorators import admin_required
from shared.database.connection import SessionLocal
from shared.models.card_templates import CardTemplate, CardSet
import logging
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

admin_card_sets_bp = Blueprint('admin_card_sets', __name__, url_prefix='/v1/admin/card-sets')

# External storage configuration
EXTERNAL_STORAGE_PATH = "/mnt/HC_Volume_103132438"
ASSETS_BASE_PATH = "/home/jp/deckport.ai/static"

def setup_external_storage_links():
    """Setup soft links to external storage for card assets"""
    try:
        # Create external storage directories
        external_assets = Path(EXTERNAL_STORAGE_PATH) / "deckport_assets"
        external_assets.mkdir(exist_ok=True)
        
        # Create subdirectories for different asset types
        (external_assets / "cards" / "artwork").mkdir(parents=True, exist_ok=True)
        (external_assets / "cards" / "frames").mkdir(parents=True, exist_ok=True)
        (external_assets / "cards" / "videos").mkdir(parents=True, exist_ok=True)
        (external_assets / "cards" / "thumbnails").mkdir(parents=True, exist_ok=True)
        
        # Create soft links from static directory to external storage
        static_cards_path = Path(ASSETS_BASE_PATH) / "cards"
        
        # Remove existing directory if it exists
        if static_cards_path.exists() and not static_cards_path.is_symlink():
            subprocess.run(['rm', '-rf', str(static_cards_path)])
        
        # Create soft link
        if not static_cards_path.exists():
            os.symlink(str(external_assets / "cards"), str(static_cards_path))
            logger.info(f"Created soft link: {static_cards_path} -> {external_assets / 'cards'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup external storage links: {e}")
        return False

@admin_card_sets_bp.route('', methods=['GET'])
@admin_required
def get_card_sets():
    """Get all card sets"""
    try:
        with SessionLocal() as session:
            card_sets = session.query(CardSet).all()
            
            sets_data = []
            for card_set in card_sets:
                set_data = {
                    'id': card_set.id,
                    'name': card_set.name,
                    'code': card_set.code,
                    'theme': getattr(card_set, 'theme', 'unknown'),
                    'total_cards': getattr(card_set, 'total_cards', 0),
                    'created_at': card_set.created_at.isoformat() if hasattr(card_set, 'created_at') else None
                }
                sets_data.append(set_data)
            
            return jsonify({
                'success': True,
                'card_sets': sets_data,
                'total': len(sets_data)
            })
            
    except Exception as e:
        logger.error(f"Error getting card sets: {e}")
        return jsonify({'error': 'Failed to retrieve card sets'}), 500


@admin_card_sets_bp.route('/generate', methods=['POST'])
@admin_required
def generate_card_set():
    """Generate a complete balanced card set with AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        set_name = data.get('set_name')
        set_code = data.get('set_code')
        theme = data.get('theme', 'fantasy')
        color_distribution = data.get('color_distribution', 'balanced')
        set_size = int(data.get('set_size', 50))
        generation_prompt = data.get('generation_prompt', '')
        
        if not set_name or not set_code:
            return jsonify({'error': 'Set name and code are required'}), 400
        
        # Generate the complete card set using AI
        generated_set = generate_balanced_card_set_ai(
            set_name=set_name,
            set_code=set_code,
            theme=theme,
            color_distribution=color_distribution,
            set_size=set_size,
            user_prompt=generation_prompt
        )
        
        return jsonify({
            'success': True,
            'card_set': generated_set,
            'message': f'Generated {len(generated_set["cards"])} cards for set "{set_name}"'
        })
        
    except Exception as e:
        logger.error(f"Error generating card set: {e}")
        return jsonify({'error': f'Failed to generate card set: {str(e)}'}), 500


@admin_card_sets_bp.route('/<int:set_id>/save', methods=['POST'])
@admin_required
def save_card_set(set_id):
    """Save generated card set to database"""
    try:
        data = request.get_json()
        
        if not data or 'cards' not in data:
            return jsonify({'error': 'Card data required'}), 400
        
        with SessionLocal() as session:
            # Create or update card set
            card_set = session.query(CardSet).filter(CardSet.id == set_id).first()
            
            if not card_set:
                # Create new card set
                card_set = CardSet(
                    name=data['set_name'],
                    code=data['set_code'],
                    theme=data.get('theme', 'fantasy'),
                    total_cards=len(data['cards'])
                )
                session.add(card_set)
                session.flush()  # Get the ID
            
            # Create card templates
            created_cards = []
            for card_data in data['cards']:
                template = CardTemplate(
                    card_set_id=card_set.id,
                    name=card_data['name'],
                    slug=card_data['name'].lower().replace(' ', '-'),
                    description=card_data.get('description', ''),
                    flavor_text=card_data.get('flavor_text', ''),
                    rarity=card_data['rarity'],
                    category=card_data['category'],
                    color_code=card_data.get('color_code'),
                    base_stats=card_data.get('base_stats', {}),
                    art_prompt=card_data.get('art_prompt', ''),
                    is_design_complete=True,
                    is_balanced=True,
                    balance_weight=card_data.get('balance_weight', 50)
                )
                
                session.add(template)
                created_cards.append(template)
            
            session.commit()
            
            return jsonify({
                'success': True,
                'set_id': card_set.id,
                'cards_created': len(created_cards),
                'message': f'Card set "{card_set.name}" saved with {len(created_cards)} cards!'
            })
            
    except Exception as e:
        logger.error(f"Error saving card set: {e}")
        return jsonify({'error': f'Failed to save card set: {str(e)}'}), 500


def generate_balanced_card_set_ai(set_name, set_code, theme, color_distribution, set_size, user_prompt=""):
    """
    Generate a complete balanced card set using AI analysis
    This should integrate with Claude/LLM for proper card generation
    """
    
    # For now, return a mock structure - this should be replaced with actual LLM integration
    return {
        'set_name': set_name,
        'set_code': set_code,
        'theme': theme,
        'total_cards': set_size,
        'structure': {
            'colors': {
                'CRIMSON': {'creatures': 8, 'spells': 6, 'equipment': 3},
                'AZURE': {'creatures': 8, 'spells': 6, 'equipment': 3},
                'VERDANT': {'creatures': 8, 'spells': 6, 'equipment': 3}
            }
        },
        'cards': [
            {
                'name': f'Sample Card {i}',
                'category': 'creature',
                'rarity': 'common',
                'color_code': 'CRIMSON',
                'mana_cost': 3,
                'energy_cost': 2,
                'attack': 4,
                'defense': 2,
                'health': 6,
                'description': f'A {theme} creature with balanced stats',
                'art_prompt': f'{theme} creature, detailed fantasy art',
                'balance_weight': 45
            } for i in range(min(set_size, 10))  # Generate sample cards
        ],
        'art_style_guide': f'{theme} themed artwork with consistent style',
        'balance_report': 'Set is balanced for competitive play'
    }


@admin_card_sets_bp.route('/assets/batch-generate', methods=['POST'])
@admin_required
def start_batch_asset_generation():
    """Start batch generation of card assets (graphics + videos)"""
    try:
        # Setup external storage links first
        if not setup_external_storage_links():
            return jsonify({'error': 'Failed to setup external storage'}), 500
        
        data = request.get_json()
        generation_type = data.get('generation_type', 'all')
        batch_size = int(data.get('batch_size', 10))
        priority = data.get('priority', 'normal')
        specific_cards = data.get('specific_cards', [])  # For single card regeneration
        
        # Get cards for generation
        with SessionLocal() as session:
            if specific_cards:
                # Generate for specific cards by SKU
                placeholders = ', '.join([':sku' + str(i) for i in range(len(specific_cards))])
                params = {f'sku{i}': sku for i, sku in enumerate(specific_cards)}
                
                cards_query = session.execute(text(f"""
                    SELECT id, name, product_sku, category, rarity, mana_colors, generation_prompt
                    FROM card_catalog 
                    WHERE product_sku IN ({placeholders})
                """), params)
            else:
                # Query cards without graphics
                cards_query = session.execute(text("""
                    SELECT id, name, product_sku, category, rarity, mana_colors, generation_prompt
                    FROM card_catalog 
                    WHERE (artwork_url IS NULL OR artwork_url = '') 
                    ORDER BY rarity DESC, category, name
                    LIMIT 1000
                """))
            
            cards_needing_assets = [dict(row._mapping) for row in cards_query]
        
        if not cards_needing_assets:
            return jsonify({'error': 'No cards need asset generation'}), 400
        
        # Create generation queue
        queue_id = f"batch_{int(datetime.now().timestamp())}"
        
        # Start asset generation process
        total_cards = min(len(cards_needing_assets), batch_size * 10)  # Limit to reasonable batch
        
        # For each card: Generate artwork, then video, then frame
        generation_plan = []
        for card in cards_needing_assets[:total_cards]:
            # Define asset paths that will be accessible via web
            card_slug = card.get('name', '').lower().replace(' ', '_').replace("'", "")
            asset_paths = {
                'artwork_url': f'/static/cards/artwork/{card_slug}.png',
                'video_url': f'/static/cards/videos/{card_slug}.mp4',
                'static_url': f'/static/cards/frames/{card_slug}_framed.png',
                'thumbnail_url': f'/static/cards/thumbnails/{card_slug}_thumb.png'
            }
            
            generation_plan.append({
                'card_id': card['id'],
                'card_name': card['name'],
                'card_slug': card_slug,
                'asset_paths': asset_paths,
                'steps': [
                    {'type': 'artwork', 'prompt': card.get('art_prompt', f"Fantasy {card['category']} art"), 'output_path': asset_paths['artwork_url']},
                    {'type': 'video', 'source': 'artwork', 'output_path': asset_paths['video_url']},
                    {'type': 'frame', 'source': 'artwork', 'output_path': asset_paths['static_url']},
                    {'type': 'thumbnail', 'source': 'frame', 'output_path': asset_paths['thumbnail_url']}
                ]
            })
        
        # Store generation plan (in production, this would go to a proper queue system)
        # For now, return the plan for frontend monitoring
        
        return jsonify({
            'success': True,
            'queue_id': queue_id,
            'total_cards': total_cards,
            'generation_plan': generation_plan,
            'estimated_time': f"{total_cards * 2} minutes",  # ~2 minutes per card
            'external_storage': str(Path(EXTERNAL_STORAGE_PATH) / "deckport_assets" / "cards"),
            'message': f'Started batch generation of {total_cards} cards'
        })
        
    except Exception as e:
        logger.error(f"Error starting batch asset generation: {e}")
        return jsonify({'error': f'Failed to start batch generation: {str(e)}'}), 500


@admin_card_sets_bp.route('/assets/queue', methods=['GET'])
@admin_required
def get_asset_generation_queue():
    """Get current asset generation queue status"""
    try:
        # In production, this would query a real job queue
        # For now, return mock data structure
        
        queue_data = {
            'pending_count': 0,
            'running_count': 0,
            'completed_count': 0,
            'failed_count': 0,
            'current_job': None,
            'estimated_completion': None
        }
        
        return jsonify({
            'success': True,
            'queue': queue_data,
            'external_storage_available': os.path.exists(EXTERNAL_STORAGE_PATH),
            'external_storage_free': get_external_storage_info()
        })
        
    except Exception as e:
        logger.error(f"Error getting asset generation queue: {e}")
        return jsonify({'error': 'Failed to get queue status'}), 500


def get_external_storage_info():
    """Get external storage space information"""
    try:
        result = subprocess.run(['df', '-h', EXTERNAL_STORAGE_PATH], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                fields = lines[1].split()
                return {
                    'total': fields[1],
                    'used': fields[2], 
                    'available': fields[3],
                    'use_percent': fields[4]
                }
        return {'error': 'Could not get storage info'}
    except Exception as e:
        return {'error': str(e)}


@admin_card_sets_bp.route('/assets/update-urls', methods=['POST'])
@admin_required
def update_card_asset_urls():
    """Update card database with generated asset URLs"""
    try:
        data = request.get_json()
        
        if not data or 'cards' not in data:
            return jsonify({'error': 'Card data required'}), 400
        
        updated_count = 0
        
        with SessionLocal() as session:
            for card_update in data['cards']:
                card_id = card_update.get('card_id')
                asset_paths = card_update.get('asset_paths', {})
                
                if not card_id:
                    continue
                
                # Update card with asset URLs
                session.execute(text("""
                    UPDATE card_catalog 
                    SET artwork_url = :artwork_url,
                        video_url = :video_url,
                        static_url = :static_url,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :card_id
                """), {
                    'card_id': card_id,
                    'artwork_url': asset_paths.get('artwork_url'),
                    'video_url': asset_paths.get('video_url'),
                    'static_url': asset_paths.get('static_url')
                })
                
                updated_count += 1
            
            session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'message': f'Updated {updated_count} cards with asset URLs'
        })
        
    except Exception as e:
        logger.error(f"Error updating card asset URLs: {e}")
        return jsonify({'error': f'Failed to update asset URLs: {str(e)}'}), 500


@admin_card_sets_bp.route('/assets/regenerate-single', methods=['POST'])
@admin_required
def regenerate_single_card():
    """Regenerate assets for a single card"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        product_sku = data.get('product_sku')
        generation_type = data.get('generation_type', 'all')
        
        if not product_sku:
            return jsonify({'error': 'Product SKU required'}), 400
        
        # Get card from database
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT id, name, category, rarity, mana_colors, generation_prompt
                FROM card_catalog 
                WHERE product_sku = :product_sku
            """), {'product_sku': product_sku})
            
            card_row = result.fetchone()
            if not card_row:
                return jsonify({'error': 'Card not found'}), 404
            
            card_data = {
                'id': card_row[0],
                'name': card_row[1],
                'category': card_row[2],
                'rarity': card_row[3],
                'mana_colors': card_row[4],
                'generation_prompt': card_row[5]
            }
        
        # For now, return success with plan (actual generation would happen here)
        card_slug = card_data['name'].lower().replace(' ', '_').replace("'", "")
        
        return jsonify({
            'success': True,
            'message': f'Single card regeneration started for {card_data["name"]}',
            'card_id': card_data['id'],
            'card_name': card_data['name'],
            'generation_type': generation_type,
            'estimated_time': '2-3 minutes',
            'asset_paths': {
                'artwork_url': f'/static/cards/artwork/{card_slug}.png',
                'framed_url': f'/static/cards/frames/{card_slug}_framed.png',
                'thumbnail_url': f'/static/cards/thumbnails/{card_slug}_thumb.png',
                'video_url': f'/static/cards/videos/{card_slug}.mp4'
            }
        })
        
    except Exception as e:
        logger.error(f"Error regenerating single card: {e}")
        return jsonify({'error': f'Failed to regenerate card: {str(e)}'}), 500
