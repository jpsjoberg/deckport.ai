import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Card Database Production Admin Routes
Database-only production interface - no CSV dependency
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from shared.auth.decorators import admin_required
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

card_db_bp = Blueprint('card_database', __name__, url_prefix='/admin/card-database')

try:
    from services.card_database_processor import get_card_database_processor, DatabaseProcessingConfig
    from services.card_generation_queue import get_card_generation_queue, JobType
    DATABASE_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Database processing service not available: {e}")
    DATABASE_SERVICE_AVAILABLE = False

@card_db_bp.route('/', methods=['GET'])
@admin_required
def database_dashboard():
    """Database-only production dashboard"""
    if not DATABASE_SERVICE_AVAILABLE:
        flash('Database processing service not available', 'error')
        return redirect(url_for('admin.index'))
    
    try:
        # Get processing status from database
        processor = get_card_database_processor()
        db_status = processor.get_processing_status()
        
        # Check ComfyUI status
        from services.comfyui_service import get_comfyui_service
        comfyui = get_comfyui_service()
        comfyui_status = {
            'online': comfyui.is_online(),
            'host': comfyui.host
        }
        
        # Get queue status
        queue = get_card_generation_queue()
        recent_jobs = queue.get_all_jobs(limit=10)
        
        return render_template('admin/card_database/dashboard.html', 
                             db_status=db_status,
                             comfyui_status=comfyui_status,
                             recent_jobs=recent_jobs)
        
    except Exception as e:
        logger.error(f"Database dashboard error: {e}")
        flash(f'Error loading dashboard: {e}', 'error')
        return redirect(url_for('admin.index'))

@card_db_bp.route('/start-production', methods=['POST'])
@admin_required
def start_database_production():
    """Start database-only production processing"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        data = request.get_json()
        
        # Configuration from form
        config = {
            'max_workers': int(data.get('max_workers', 4)),
            'generate_videos': data.get('generate_videos', True),
            'generate_thumbnails': data.get('generate_thumbnails', True),
            'quality_checks': data.get('quality_checks', True),
            'comfyui_timeout': int(data.get('comfyui_timeout', 300)),
            'skip_existing_assets': data.get('skip_existing_assets', True)
        }
        
        # Processing options
        production_type = data.get('production_type', 'all')  # 'all', 'range', 'missing'
        start_index = int(data.get('start_index', 0))
        end_index = data.get('end_index')
        if end_index:
            end_index = int(end_index)
        
        # Add job to queue
        queue = get_card_generation_queue()
        
        if production_type == 'all':
            job_type = JobType.FULL_PRODUCTION
            job_config = config
        else:
            job_type = JobType.BATCH_CARDS
            job_config = {**config, 'start_index': start_index, 'end_index': end_index}
        
        job_id = queue.add_job(job_type, job_config)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Production job queued successfully: {job_id}'
        })
        
    except Exception as e:
        logger.error(f"Database production error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_db_bp.route('/process-single', methods=['POST'])
@admin_required
def process_single_card_db():
    """Process a single card by ID from database"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        data = request.get_json()
        card_id = int(data.get('card_id', 0))
        
        if not card_id:
            return jsonify({'success': False, 'error': 'Card ID required'}), 400
        
        # Add single card job to queue
        queue = get_card_generation_queue()
        job_id = queue.add_job(JobType.SINGLE_CARD, {'card_id': card_id})
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Single card job queued: {job_id}'
        })
        
    except Exception as e:
        logger.error(f"Single card processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_db_bp.route('/job-status/<job_id>', methods=['GET'])
@admin_required
def get_job_status(job_id):
    """Get status of a specific job"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        queue = get_card_generation_queue()
        job = queue.get_job(job_id)
        
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': {
                'id': job.id,
                'job_type': job.job_type.value,
                'status': job.status.value,
                'progress': job.progress,
                'total_cards': job.total_cards,
                'processed_cards': job.processed_cards,
                'successful_cards': job.successful_cards,
                'failed_cards': job.failed_cards,
                'error_message': job.error_message,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Job status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_db_bp.route('/cancel-job/<job_id>', methods=['POST'])
@admin_required
def cancel_job(job_id):
    """Cancel a pending job"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        queue = get_card_generation_queue()
        success = queue.cancel_job(job_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Job cancelled successfully'})
        else:
            return jsonify({'success': False, 'error': 'Could not cancel job (may not be pending)'}), 400
        
    except Exception as e:
        logger.error(f"Job cancellation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_db_bp.route('/database-stats', methods=['GET'])
@admin_required
def get_database_stats():
    """Get current database statistics"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        processor = get_card_database_processor()
        stats = processor.get_processing_status()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Database stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_db_bp.route('/cards-with-prompts', methods=['GET'])
@admin_required
def get_cards_with_prompts():
    """Get list of cards that have generation prompts"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        from shared.database.connection import SessionLocal
        from shared.models.base import CardCatalog
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        session = SessionLocal()
        try:
            # Get cards with prompts
            query = session.query(CardCatalog).filter(
                CardCatalog.generation_prompt.isnot(None)
            ).order_by(CardCatalog.name)
            
            # Pagination
            total = query.count()
            cards = query.offset((page - 1) * per_page).limit(per_page).all()
            
            card_list = []
            for card in cards:
                card_list.append({
                    'id': card.id,
                    'name': card.name,
                    'rarity': card.rarity.value if hasattr(card.rarity, 'value') else str(card.rarity),
                    'category': card.category.value if hasattr(card.category, 'value') else str(card.category),
                    'has_artwork': bool(card.artwork_url),
                    'has_static': bool(card.static_url),
                    'has_video': bool(card.video_url),
                    'prompt_length': len(card.generation_prompt) if card.generation_prompt else 0,
                    'mana_colors': card.mana_colors
                })
            
            return jsonify({
                'success': True,
                'cards': card_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Cards with prompts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_db_bp.route('/missing-prompts', methods=['GET'])
@admin_required
def get_missing_prompts():
    """Get list of cards that are missing generation prompts"""
    if not DATABASE_SERVICE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Database service not available'}), 500
    
    try:
        from shared.database.connection import SessionLocal
        from shared.models.base import CardCatalog
        
        session = SessionLocal()
        try:
            # Get cards without prompts
            cards = session.query(CardCatalog).filter(
                CardCatalog.generation_prompt.is_(None)
            ).order_by(CardCatalog.name).limit(100).all()
            
            card_list = []
            for card in cards:
                card_list.append({
                    'id': card.id,
                    'name': card.name,
                    'rarity': card.rarity.value if hasattr(card.rarity, 'value') else str(card.rarity),
                    'category': card.category.value if hasattr(card.category, 'value') else str(card.category),
                    'mana_colors': card.mana_colors
                })
            
            return jsonify({
                'success': True,
                'missing_cards': card_list,
                'count': len(card_list)
            })
            
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Missing prompts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
