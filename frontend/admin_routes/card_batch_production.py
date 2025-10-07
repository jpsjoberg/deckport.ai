import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Card Batch Production Admin Routes
Production-ready batch processing interface for CSV to graphics pipeline
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from shared.auth.decorators import admin_required
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

card_batch_bp = Blueprint('card_batch', __name__, url_prefix='/admin/card-batch')

try:
    from services.card_batch_processor import get_card_batch_processor, BatchProcessingConfig
    BATCH_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Batch processing service not available: {e}")
    BATCH_SERVICE_AVAILABLE = False

@card_batch_bp.route('/', methods=['GET'])
@admin_required
def batch_dashboard():
    """Batch processing dashboard"""
    if not BATCH_SERVICE_AVAILABLE:
        flash('Batch processing service not available', 'error')
        return redirect(url_for('admin.index'))
    
    try:
        # Check CSV file status
        art_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_art.csv'
        gameplay_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_gameplay.csv'
        
        csv_status = {
            'art_csv_exists': os.path.exists(art_csv_path),
            'gameplay_csv_exists': os.path.exists(gameplay_csv_path),
            'art_csv_size': os.path.getsize(art_csv_path) if os.path.exists(art_csv_path) else 0,
            'gameplay_csv_size': os.path.getsize(gameplay_csv_path) if os.path.exists(gameplay_csv_path) else 0
        }
        
        # Count lines in CSV files to estimate card count
        if csv_status['art_csv_exists']:
            with open(art_csv_path, 'r') as f:
                csv_status['estimated_cards'] = sum(1 for line in f) - 1  # -1 for header
        else:
            csv_status['estimated_cards'] = 0
        
        # Check ComfyUI status
        from services.comfyui_service import get_comfyui_service
        comfyui = get_comfyui_service()
        comfyui_status = {
            'online': comfyui.is_online(),
            'host': comfyui.host
        }
        
        return render_template('admin/card_batch/dashboard.html', 
                             csv_status=csv_status,
                             comfyui_status=comfyui_status)
        
    except Exception as e:
        logger.error(f"Batch dashboard error: {e}")
        flash(f'Error loading dashboard: {e}', 'error')
        return redirect(url_for('admin.index'))

@card_batch_bp.route('/start-batch', methods=['POST'])
@admin_required
def start_batch_processing():
    """Start batch processing"""
    if not BATCH_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Batch service not available'}), 500
    
    try:
        data = request.get_json()
        
        # Configuration from form
        config = BatchProcessingConfig(
            max_workers=int(data.get('max_workers', 4)),
            generate_videos=data.get('generate_videos', True),
            generate_thumbnails=data.get('generate_thumbnails', True),
            quality_checks=data.get('quality_checks', True),
            comfyui_timeout=int(data.get('comfyui_timeout', 300))
        )
        
        # Processing range
        start_index = int(data.get('start_index', 0))
        end_index = data.get('end_index')
        if end_index:
            end_index = int(end_index)
        
        resume_from_existing = data.get('resume_from_existing', True)
        
        # CSV file paths - PRODUCTION READY FILES
        art_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_art_production_ready.csv'
        gameplay_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_gameplay_final.csv'
        
        # Validate files exist
        if not os.path.exists(art_csv_path):
            return jsonify({'success': False, 'error': 'Art CSV file not found'}), 400
        if not os.path.exists(gameplay_csv_path):
            return jsonify({'success': False, 'error': 'Gameplay CSV file not found'}), 400
        
        # Start processing (this will run in background)
        processor = get_card_batch_processor(config)
        
        # For production, you'd want to run this in a background task (Celery, etc.)
        # For now, we'll run it synchronously with a smaller batch
        if not end_index:
            end_index = start_index + 10  # Process 10 cards at a time for testing
        
        logger.info(f"Starting batch processing: {start_index} to {end_index}")
        
        results = processor.process_csv_batch(
            art_csv_path=art_csv_path,
            gameplay_csv_path=gameplay_csv_path,
            start_index=start_index,
            end_index=end_index,
            resume_from_existing=resume_from_existing
        )
        
        # Return results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return jsonify({
            'success': True,
            'message': f'Batch processing completed: {successful} successful, {failed} failed',
            'results': {
                'total_processed': len(results),
                'successful': successful,
                'failed': failed,
                'failed_cards': [r.card_name for r in results if not r.success]
            }
        })
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_batch_bp.route('/process-single', methods=['POST'])
@admin_required
def process_single_card():
    """Process a single card by name"""
    if not BATCH_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Batch service not available'}), 500
    
    try:
        data = request.get_json()
        card_name = data.get('card_name', '').strip()
        
        if not card_name:
            return jsonify({'success': False, 'error': 'Card name required'}), 400
        
        # Load CSV data to find the specific card - PRODUCTION READY FILES
        art_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_art_production_ready.csv'
        gameplay_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_gameplay_final.csv'
        
        processor = get_card_batch_processor()
        art_data = processor._load_csv_data(art_csv_path)
        gameplay_data = processor._load_csv_data(gameplay_csv_path)
        merged_cards = processor._merge_card_data(art_data, gameplay_data)
        
        # Find the specific card
        target_card = None
        for card in merged_cards:
            if card.get('name', '').lower() == card_name.lower():
                target_card = card
                break
        
        if not target_card:
            return jsonify({'success': False, 'error': f'Card not found: {card_name}'}), 404
        
        # Process the single card
        result = processor._process_single_card(target_card, 0, False)
        
        if result.success:
            return jsonify({
                'success': True,
                'message': f'Successfully processed: {card_name}',
                'card_id': result.card_id,
                'assets': result.assets,
                'processing_time': result.processing_time
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Processing failed: {result.errors}',
                'processing_time': result.processing_time
            }), 500
            
    except Exception as e:
        logger.error(f"Single card processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_batch_bp.route('/csv-preview', methods=['GET'])
@admin_required
def csv_preview():
    """Preview CSV data"""
    if not BATCH_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Batch service not available'}), 500
    
    try:
        csv_type = request.args.get('type', 'art')  # 'art' or 'gameplay'
        limit = int(request.args.get('limit', 10))
        
        if csv_type == 'art':
            csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_art_production_ready.csv'
        else:
            csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_gameplay_final.csv'
        
        if not os.path.exists(csv_path):
            return jsonify({'success': False, 'error': f'CSV file not found: {csv_path}'}), 404
        
        processor = get_card_batch_processor()
        data = processor._load_csv_data(csv_path)
        
        return jsonify({
            'success': True,
            'total_rows': len(data),
            'preview': data[:limit],
            'columns': list(data[0].keys()) if data else []
        })
        
    except Exception as e:
        logger.error(f"CSV preview error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_batch_bp.route('/validate-csv', methods=['POST'])
@admin_required
def validate_csv():
    """Validate CSV files for batch processing"""
    if not BATCH_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Batch service not available'}), 500
    
    try:
        art_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_art_production_ready.csv'
        gameplay_csv_path = '/home/jp/deckport.ai/cardmaker.ai/data/cards_gameplay_final.csv'
        
        processor = get_card_batch_processor()
        
        # Load and validate CSV files
        art_data = processor._load_csv_data(art_csv_path)
        gameplay_data = processor._load_csv_data(gameplay_csv_path)
        
        validation_results = {
            'art_csv': {
                'exists': os.path.exists(art_csv_path),
                'rows': len(art_data),
                'columns': list(art_data[0].keys()) if art_data else [],
                'required_columns': ['name', 'image_prompt', 'mana_color_code'],
                'missing_columns': []
            },
            'gameplay_csv': {
                'exists': os.path.exists(gameplay_csv_path),
                'rows': len(gameplay_data),
                'columns': list(gameplay_data[0].keys()) if gameplay_data else [],
                'required_columns': ['name', 'category', 'rarity', 'mana_cost'],
                'missing_columns': []
            }
        }
        
        # Check for required columns
        for csv_type, info in validation_results.items():
            for req_col in info['required_columns']:
                if req_col not in info['columns']:
                    info['missing_columns'].append(req_col)
        
        # Try to merge data
        merged_cards = processor._merge_card_data(art_data, gameplay_data)
        
        validation_results['merge_result'] = {
            'art_cards': len(art_data),
            'gameplay_cards': len(gameplay_data),
            'merged_cards': len(merged_cards),
            'merge_success_rate': (len(merged_cards) / max(1, len(art_data))) * 100
        }
        
        # Overall validation status
        all_valid = (
            validation_results['art_csv']['exists'] and
            validation_results['gameplay_csv']['exists'] and
            not validation_results['art_csv']['missing_columns'] and
            not validation_results['gameplay_csv']['missing_columns'] and
            validation_results['merge_result']['merge_success_rate'] > 90
        )
        
        return jsonify({
            'success': True,
            'valid': all_valid,
            'validation_results': validation_results
        })
        
    except Exception as e:
        logger.error(f"CSV validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
