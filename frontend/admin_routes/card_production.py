import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Card Production Admin Routes
Complete asset generation workflow for cards
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from shared.auth.decorators import admin_required
import logging
import json

logger = logging.getLogger(__name__)

card_production_bp = Blueprint('card_production', __name__, url_prefix='/admin/card-production')

try:
    from services.card_production_service import get_card_production_service
    PRODUCTION_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Card production service not available: {e}")
    PRODUCTION_SERVICE_AVAILABLE = False

@card_production_bp.route('/', methods=['GET'])
@admin_required
def production_dashboard():
    """Card production dashboard"""
    if not PRODUCTION_SERVICE_AVAILABLE:
        flash('Card production service not available', 'error')
        return redirect(url_for('admin.index'))
    
    try:
        production_service = get_card_production_service()
        status = production_service.get_generation_status()
        
        return render_template('admin/card_production/dashboard.html', status=status)
        
    except Exception as e:
        logger.error(f"Production dashboard error: {e}")
        flash(f'Error loading production dashboard: {e}', 'error')
        return redirect(url_for('admin.index'))

@card_production_bp.route('/generate-single', methods=['POST'])
@admin_required
def generate_single_card():
    """Generate complete assets for a single card"""
    if not PRODUCTION_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Production service not available'}), 500
    
    try:
        data = request.get_json()
        card_id = int(data.get('card_id'))
        art_prompt = data.get('art_prompt', '')
        
        if not card_id or not art_prompt:
            return jsonify({'success': False, 'error': 'Card ID and art prompt required'}), 400
        
        production_service = get_card_production_service()
        
        # Generate complete assets
        assets = production_service.generate_complete_card_assets(card_id, art_prompt)
        
        # Check success
        successful_assets = sum(1 for path in assets.values() if path and os.path.exists(path))
        
        if successful_assets >= 3:  # At least static, frame, composite
            return jsonify({
                'success': True,
                'assets': assets,
                'message': f'Generated {successful_assets} assets successfully'
            })
        else:
            return jsonify({
                'success': False,
                'assets': assets,
                'error': f'Only {successful_assets} assets generated successfully'
            }), 500
            
    except Exception as e:
        logger.error(f"Single card generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_production_bp.route('/generate-batch', methods=['POST'])
@admin_required
def generate_batch_cards():
    """Generate assets for multiple cards"""
    if not PRODUCTION_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Production service not available'}), 500
    
    try:
        data = request.get_json()
        card_ids = data.get('card_ids', [])
        
        if not card_ids:
            return jsonify({'success': False, 'error': 'No card IDs provided'}), 400
        
        production_service = get_card_production_service()
        
        # Start batch generation
        def progress_callback(current, total, message):
            # In production, you could emit WebSocket events here for real-time progress
            logger.info(f"Batch progress: {current}/{total} - {message}")
        
        results = production_service.batch_generate_cards(card_ids, progress_callback)
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f'Batch generation complete: {results["successful"]}/{results["total_cards"]} cards processed'
        })
        
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_production_bp.route('/test-legendary', methods=['POST'])
@admin_required
def test_legendary_generation():
    """Test generation with Burn Knight legendary card"""
    if not PRODUCTION_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Production service not available'}), 500
    
    try:
        production_service = get_card_production_service()
        
        # Find Burn Knight card ID
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text('''
                SELECT c.id, c.name FROM card_catalog c 
                WHERE c.name = 'Burn Knight' AND c.rarity = 'legendary'
            '''))
            card_row = result.fetchone()
            
            if not card_row:
                return jsonify({'success': False, 'error': 'Burn Knight not found'}), 404
            
            card_id = card_row[0]
            card_name = card_row[1]
            
        finally:
            session.close()
        
        # Get art prompt
        art_prompts = production_service._load_art_prompts()
        art_prompt = art_prompts.get(card_name)
        
        if not art_prompt:
            return jsonify({'success': False, 'error': 'No art prompt found for Burn Knight'}), 400
        
        # Generate complete assets
        assets = production_service.generate_complete_card_assets(card_id, art_prompt)
        
        # Count successful assets
        successful_assets = sum(1 for path in assets.values() if path and os.path.exists(path))
        
        return jsonify({
            'success': successful_assets >= 3,
            'card_name': card_name,
            'card_id': card_id,
            'assets': assets,
            'successful_assets': successful_assets,
            'message': f'Legendary test: {successful_assets} assets generated for {card_name}'
        })
        
    except Exception as e:
        logger.error(f"Legendary test error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_production_bp.route('/status', methods=['GET'])
@admin_required
def get_production_status():
    """Get current production status"""
    if not PRODUCTION_SERVICE_AVAILABLE:
        return jsonify({'error': 'Production service not available'}), 500
    
    try:
        production_service = get_card_production_service()
        status = production_service.get_generation_status()
        
        # Add ComfyUI status
        comfyui_online = production_service.comfyui.is_online()
        status['comfyui_online'] = comfyui_online
        
        if comfyui_online:
            queue_status = production_service.comfyui.get_queue_status()
            if queue_status:
                status['queue_running'] = len(queue_status.get('queue_running', []))
                status['queue_pending'] = len(queue_status.get('queue_pending', []))
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500

@card_production_bp.route('/assets/<product_sku>', methods=['GET'])
@admin_required
def get_card_assets(product_sku):
    """Get asset URLs for a specific card"""
    try:
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text('''
                SELECT name, artwork_url, static_url, video_url, has_animation
                FROM card_catalog WHERE product_sku = :sku
            '''), {'sku': product_sku.upper()})
            
            card_row = result.fetchone()
            if not card_row:
                return jsonify({'error': 'Card not found'}), 404
            
            return jsonify({
                'name': card_row[0],
                'artwork_url': card_row[1],
                'static_url': card_row[2],
                'video_url': card_row[3],
                'has_animation': card_row[4]
            })
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Asset lookup error: {e}")
        return jsonify({'error': str(e)}), 500
