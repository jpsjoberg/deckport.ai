import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
Card Management Routes for Deckport Admin Panel
Updated to use PostgreSQL card templates and NFC instances
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from functools import wraps
from . import admin_bp

def require_admin_auth(f):
    """Decorator to require admin authentication for frontend routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# Import our services
try:
    from services.card_service import get_card_service
    from services.comfyui_service import get_comfyui_service
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Card services not available: {e}")
    SERVICES_AVAILABLE = False
    
    # Create stub services
    def get_card_service():
        return None
    
    def get_comfyui_service():
        return None

# Configuration for ComfyUI and card generation
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "https://c.getvideo.ai")
COMFYUI_TIMEOUT = int(os.environ.get("COMFYUI_TIMEOUT", "120"))
CARDMAKER_OUTPUT_DIR = os.environ.get("CARDMAKER_OUTPUT_DIR", "/home/jp/deckport.ai/cardmaker.ai/cards_output")
CARDMAKER_ELEMENTS_DIR = os.environ.get("CARDMAKER_ELEMENTS_DIR", "/home/jp/deckport.ai/cardmaker.ai/card_elements")

# Mana color mappings
MANA_COLORS = {
    'CRIMSON': {'name': 'Crimson', 'icon': 'mana_red.png', 'color': '#DC2626'},
    'AZURE': {'name': 'Azure', 'icon': 'mana_blue.png', 'color': '#2563EB'},
    'VERDANT': {'name': 'Verdant', 'icon': 'mana_green.png', 'color': '#16A34A'},
    'OBSIDIAN': {'name': 'Obsidian', 'icon': 'mana_black.png', 'color': '#1F2937'},
    'RADIANT': {'name': 'Radiant', 'icon': 'mana_white.png', 'color': '#F59E0B'},
    'AETHER': {'name': 'Aether', 'icon': 'mana_orange.png', 'color': '#EA580C'}
}

RARITIES = ['COMMON', 'RARE', 'EPIC', 'LEGENDARY']
CATEGORIES = ['CREATURE', 'STRUCTURE', 'ACTION', 'SPECIAL', 'EQUIPMENT']

def create_pagination_object(page=1, total=0, per_page=20):
    """Create a pagination object with all required attributes"""
    pages = max(1, (total + per_page - 1) // per_page)  # Ceiling division
    return {
        'page': page,
        'pages': pages,
        'total': total,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < pages else None
    }


def call_comfyui_api(endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
    """Call ComfyUI API endpoint"""
    try:
        url = f"{COMFYUI_HOST}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, timeout=COMFYUI_TIMEOUT)
        else:
            response = requests.post(url, json=data, timeout=COMFYUI_TIMEOUT)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        current_app.logger.error(f"ComfyUI API call failed: {e}")
        return None


@admin_bp.route('/cards')
@require_admin_auth
def card_management_index():
    """Card Management Dashboard with Pagination and Filters"""
    
    # Get filter and pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 24, type=int), 100)  # Max 100 per page
    
    # Filter parameters (excluding artwork & video status as requested)
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').lower()
    rarity_filter = request.args.get('rarity', '').lower()
    mana_color_filter = request.args.get('mana_color', '').upper()  # Keep uppercase for mana colors
    
    # Always use API service for real data
    from services.api_service import APIService
    api_service = APIService()
    
    # Get real card data directly from database (bypassing API auth issues)
    try:
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            # Build WHERE clause for filters
            where_conditions = []
            params = {}
            
            if search_query:
                where_conditions.append("(name ILIKE :search OR product_sku ILIKE :search)")
                params['search'] = f'%{search_query}%'
            
            if category_filter:
                where_conditions.append("category = :category")
                params['category'] = category_filter
                
            if rarity_filter:
                where_conditions.append("rarity = :rarity")
                params['rarity'] = rarity_filter
                
            if mana_color_filter:
                where_conditions.append("mana_colors::text ILIKE :mana_color")
                params['mana_color'] = f'%{mana_color_filter}%'
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get total count for pagination
            count_query = f"SELECT COUNT(*) FROM card_catalog {where_clause}"
            total_result = session.execute(text(count_query), params)
            total_cards = total_result.scalar() or 0
            
            # Calculate pagination
            total_pages = (total_cards + per_page - 1) // per_page if total_cards > 0 else 1
            offset = (page - 1) * per_page
            
            # Get cards with graphics for stats
            graphics_result = session.execute(text("""
                SELECT COUNT(*) FROM card_catalog 
                WHERE (artwork_url IS NOT NULL AND artwork_url != '') 
                   OR (static_url IS NOT NULL AND static_url != '')
            """))
            cards_with_graphics = graphics_result.scalar() or 0
            
            # Get filtered and paginated cards
            cards_query = f"""
                SELECT id, name, product_sku, rarity, category, mana_colors, artwork_url, static_url, video_url, created_at
                FROM card_catalog 
                {where_clause}
                ORDER BY id DESC
                LIMIT :limit OFFSET :offset
            """
            params.update({'limit': per_page, 'offset': offset})
            
            cards_result = session.execute(text(cards_query), params)
            
            cards = []
            for row in cards_result:
                cards.append({
                    'id': row[0],
                    'name': row[1],
                    'product_sku': row[2],
                    'rarity': row[3],
                    'category': row[4],
                    'mana_colors': row[5],
                    'artwork_url': row[6],
                    'static_url': row[7],
                    'video_url': row[8],
                    'created_at': row[9]
                })
            
            # Create stats object
            class StatsObject:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
            
            completion_percent = round((cards_with_graphics / total_cards * 100), 1) if total_cards > 0 else 0
            
            stats = StatsObject({
                'total_templates': total_cards,
                'published_templates': cards_with_graphics,
                'draft_templates': total_cards - cards_with_graphics,
                'nfc_instances': 0,
                'total_nfc_cards': 0,
                'graphics_completion_percent': completion_percent,
                'by_rarity': {'COMMON': 0, 'RARE': 0, 'EPIC': 0, 'LEGENDARY': 0},
                'by_category': {'CRIMSON': 0, 'AZURE': 0, 'VERDANT': 0, 'OBSIDIAN': 0, 'RADIANT': 0, 'AETHER': 0}
            })
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"Error getting card data from database: {e}")
        # Fallback empty data
        class StatsObject:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        stats = StatsObject({
            'total_templates': 0,
            'published_templates': 0,
            'draft_templates': 0,
            'nfc_instances': 0,
            'total_nfc_cards': 0,
            'by_rarity': {'COMMON': 0, 'RARE': 0, 'EPIC': 0, 'LEGENDARY': 0},
            'by_category': {'CRIMSON': 0, 'AZURE': 0, 'VERDANT': 0, 'OBSIDIAN': 0, 'RADIANT': 0, 'AETHER': 0}
        })
        cards = []
        total_cards = 0
        total_pages = 1
    
    return render_template('admin/card_management/index_deckport.html', 
                         stats=stats, 
                         cards=cards,
                         mana_colors=MANA_COLORS,
                         # Pagination data
                         page=page, per_page=per_page, total=total_cards, total_pages=total_pages,
                         # Filter data
                         filters={
                             'q': search_query,
                             'category': category_filter,
                             'rarity': rarity_filter,
                             'mana_color': mana_color_filter
                         })


@admin_bp.route('/cards/generate')
@require_admin_auth
def card_generation():
    """Generate Graphics for Existing Cards"""
    from services.api_service import APIService
    api_service = APIService()
    
    try:
        # Get cards without graphics
        cards_response = api_service.get('/v1/admin/cards/stats')
        
        if cards_response and cards_response.get('success'):
            total_cards = cards_response.get('total_templates', 0)
            cards_with_graphics = cards_response.get('cards_with_graphics', 0)
            cards_without_graphics = total_cards - cards_with_graphics
            
            return render_template('admin/card_management/generate_graphics.html',
                                 total_cards=total_cards,
                                 cards_with_graphics=cards_with_graphics,
                                 cards_without_graphics=cards_without_graphics,
                                 completion_percent=cards_response.get('graphics_completion_percent', 0))
        else:
            flash('Unable to load card statistics', 'error')
            return redirect('/admin/cards')
            
    except Exception as e:
        flash(f'Error loading card data: {str(e)}', 'error')
        return redirect('/admin/cards')


@admin_bp.route('/cards/production')
@require_admin_auth
def card_production_dashboard():
    """Card Production Dashboard - Generate graphics for all cards"""
    try:
        from services.card_database_processor import get_card_database_processor
        from services.comfyui_service import get_comfyui_service
        from services.card_generation_queue import get_card_generation_queue
        
        processor = get_card_database_processor()
        db_status = processor.get_processing_status()
        
        comfyui = get_comfyui_service()
        comfyui_status = {
            'online': comfyui.is_online(),
            'host': comfyui.host
        }
        
        queue = get_card_generation_queue()
        recent_jobs = queue.get_all_jobs(limit=10)
        
        return render_template('admin/card_management/production.html', 
                             db_status=db_status,
                             comfyui_status=comfyui_status,
                             recent_jobs=recent_jobs)
        
    except Exception as e:
        flash(f'Error loading production dashboard: {e}', 'error')
        return redirect(url_for('admin.card_management_index'))

@admin_bp.route('/cards/production/start', methods=['POST'])
@require_admin_auth
def start_card_production():
    """Start card graphics production"""
    try:
        from services.card_generation_queue import get_card_generation_queue, JobType
        
        data = request.get_json() if request.is_json else request.form
        
        # Configuration
        config = {
            'max_workers': int(data.get('max_workers', 4)),
            'generate_videos': data.get('generate_videos') == 'true',
            'generate_thumbnails': data.get('generate_thumbnails', 'true') == 'true',
            'skip_existing_assets': data.get('skip_existing_assets', 'true') == 'true'
        }
        
        production_type = data.get('production_type', 'all')
        
        # Add job to queue
        queue = get_card_generation_queue()
        
        if production_type == 'all':
            job_id = queue.add_job(JobType.FULL_PRODUCTION, config)
            message = f'Started full production job: {job_id}'
        else:
            start_index = int(data.get('start_index', 0))
            end_index = data.get('end_index')
            if end_index:
                end_index = int(end_index)
            
            config.update({
                'start_index': start_index,
                'end_index': end_index
            })
            
            job_id = queue.add_job(JobType.BATCH_CARDS, config)
            message = f'Started batch production job: {job_id}'
        
        if request.is_json:
            return jsonify({'success': True, 'job_id': job_id, 'message': message})
        else:
            flash(message, 'success')
            return redirect(url_for('admin.card_production_dashboard'))
            
    except Exception as e:
        error_msg = f'Production start failed: {e}'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('admin.card_production_dashboard'))

@admin_bp.route('/cards/production/status/<job_id>')
@require_admin_auth
def get_production_status(job_id):
    """Get production job status"""
    try:
        from services.card_generation_queue import get_card_generation_queue
        
        queue = get_card_generation_queue()
        job = queue.get_job(job_id)
        
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': {
                'id': job.id,
                'status': job.status.value,
                'progress': job.progress,
                'total_cards': job.total_cards,
                'processed_cards': job.processed_cards,
                'successful_cards': job.successful_cards,
                'failed_cards': job.failed_cards,
                'error_message': job.error_message
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/cards/video-production')
@require_admin_auth
def video_production_dashboard():
    """Video Production Dashboard - Generate videos for cards that already have artwork"""
    try:
        from services.card_database_processor import get_card_database_processor
        from services.comfyui_service import get_comfyui_service
        from services.card_generation_queue import get_card_generation_queue
        
        processor = get_card_database_processor()
        db_status = processor.get_processing_status()
        
        comfyui = get_comfyui_service()
        comfyui_status = {
            'online': comfyui.is_online(),
            'host': comfyui.host,
            'authenticated': bool(comfyui.username and comfyui.password)
        }
        
        # Get video-specific stats
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            # Cards with artwork but no video
            cards_ready_for_video = session.execute(text('''
                SELECT COUNT(*) FROM card_catalog 
                WHERE artwork_url IS NOT NULL 
                AND (video_url IS NULL OR video_url = '')
                AND generation_prompt IS NOT NULL
            ''')).fetchone()[0]
            
            # Cards with videos
            cards_with_videos = session.execute(text('''
                SELECT COUNT(*) FROM card_catalog 
                WHERE video_url IS NOT NULL AND video_url != ''
            ''')).fetchone()[0]
            
            video_status = {
                'cards_ready_for_video': cards_ready_for_video,
                'cards_with_videos': cards_with_videos,
                'total_cards_with_artwork': db_status['cards_with_artwork']
            }
            
        finally:
            session.close()
        
        queue = get_card_generation_queue()
        recent_jobs = queue.get_all_jobs(limit=10)
        
        return render_template('admin/card_management/video_production.html', 
                             db_status=db_status,
                             video_status=video_status,
                             comfyui_status=comfyui_status,
                             recent_jobs=recent_jobs)
        
    except Exception as e:
        flash(f'Error loading video production dashboard: {e}', 'error')
        return redirect(url_for('admin.card_management_index'))

@admin_bp.route('/cards/video-production/start', methods=['POST'])
@require_admin_auth
def start_video_production():
    """Start video generation for cards that already have artwork"""
    try:
        from services.card_generation_queue import get_card_generation_queue, JobType
        
        data = request.get_json() if request.is_json else request.form
        
        # Video-specific configuration
        config = {
            'max_workers': int(data.get('max_workers', 2)),  # Lower for videos
            'generate_videos': True,  # Only videos
            'generate_thumbnails': False,  # Don't regenerate
            'skip_existing_assets': True,  # Skip existing videos
            'video_only_mode': True,  # New flag for video-only processing
            'comfyui_timeout': int(data.get('comfyui_timeout', 600))  # Longer timeout for videos
        }
        
        production_type = data.get('production_type', 'all')
        
        # Add job to queue
        queue = get_card_generation_queue()
        
        if production_type == 'all':
            job_id = queue.add_job(JobType.FULL_PRODUCTION, config)
            message = f'Started video production job: {job_id}'
        else:
            start_index = int(data.get('start_index', 0))
            end_index = data.get('end_index')
            if end_index:
                end_index = int(end_index)
            
            config.update({
                'start_index': start_index,
                'end_index': end_index
            })
            
            job_id = queue.add_job(JobType.BATCH_CARDS, config)
            message = f'Started video batch job: {job_id}'
        
        if request.is_json:
            return jsonify({'success': True, 'job_id': job_id, 'message': message})
        else:
            flash(message, 'success')
            return redirect(url_for('admin.video_production_dashboard'))
            
    except Exception as e:
        error_msg = f'Video production start failed: {e}'
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('admin.video_production_dashboard'))

@admin_bp.route('/cards/generate', methods=['POST'])
def generate_card():
    """Generate a new card template using ComfyUI"""
    try:
        # Get form data
        form_data = {
            'name': request.form.get('name'),
            'category': request.form.get('category'),
            'rarity': request.form.get('rarity'),
            'color_code': request.form.get('color_code'),
            'mana_cost': int(request.form.get('mana_cost', 0)),
            'attack': int(request.form.get('attack', 0)),
            'defense': int(request.form.get('defense', 0)),
            'health': int(request.form.get('health', 0)),
            'base_energy_per_turn': int(request.form.get('base_energy_per_turn', 0)),
            'image_prompt': request.form.get('image_prompt', ''),
            'description': request.form.get('description', ''),
            'flavor_text': request.form.get('flavor_text', ''),
        }
        
        # Validate required fields
        if not all([form_data['name'], form_data['category'], form_data['image_prompt']]):
            flash('Name, category, and image prompt are required', 'error')
            return redirect(url_for('admin.card_generation'))
        
        # Generate slug from name
        slug = form_data['name'].lower().replace(' ', '-').replace("'", "").replace('"', '')
        
        # Prepare template data
        template_data = {
            'name': form_data['name'],
            'slug': slug,
            'description': form_data['description'],
            'flavor_text': form_data['flavor_text'],
            'rarity': form_data['rarity'],
            'category': form_data['category'],
            'color_code': form_data['color_code'],
            'art_prompt': form_data['image_prompt'],
            'art_style': 'fantasy_digital_art',
            'is_published': False,  # Templates start as drafts
            'stats': {
                'attack': form_data['attack'],
                'defense': form_data['defense'],
                'health': form_data['health'],
                'base_energy_per_turn': form_data['base_energy_per_turn']
            },
            'mana_costs': [{
                'color_code': form_data['color_code'],
                'amount': form_data['mana_cost']
            }] if form_data['mana_cost'] > 0 else [],
            'targeting': {
                'target_friendly': False,
                'target_enemy': True,
                'target_self': False
            }
        }
        
        # Create card template
        card_service = get_card_service()
        template_id = card_service.create_card_template(template_data)
        
        if not template_id:
            flash('Failed to create card template', 'error')
            return redirect(url_for('admin.card_generation'))
        
        # Generate art via ComfyUI (optional, can be done later)
        comfyui_service = get_comfyui_service()
        if comfyui_service.is_online():
            try:
                # Load ComfyUI workflow template
                workflow_path = '/home/jp/deckport.ai/cardmaker.ai/art-generation.json'
                with open(workflow_path, 'r') as f:
                    workflow = json.load(f)
                
                # Update workflow with card prompt
                if "6" in workflow and "inputs" in workflow["6"]:
                    workflow["6"]["inputs"]["text"] = form_data['image_prompt']
                
                # Generate art via ComfyUI
                prompt_data = {"prompt": workflow, "client_id": "deckport-admin"}
                result = call_comfyui_api('/prompt', 'POST', prompt_data)
                
                if result and result.get('prompt_id'):
                    flash(f'Card template "{form_data["name"]}" created successfully! Art generation in progress (ID: {result["prompt_id"]})', 'success')
                else:
                    flash(f'Card template "{form_data["name"]}" created successfully! (Art generation failed)', 'warning')
            except Exception as e:
                current_app.logger.warning(f"ComfyUI art generation failed: {e}")
                flash(f'Card template "{form_data["name"]}" created successfully! (Art generation failed)', 'warning')
        else:
            flash(f'Card template "{form_data["name"]}" created successfully! (ComfyUI offline - art can be generated later)', 'success')
        
        return redirect(url_for('admin.card_review'))
        
    except Exception as e:
        current_app.logger.error(f"Card generation failed: {e}")
        flash(f'Card generation failed: {str(e)}', 'error')
        return redirect(url_for('admin.card_generation'))


@admin_bp.route('/cards/review')
def card_review():
    """Card Template Review and Management Interface"""
    if not SERVICES_AVAILABLE:
        # Return with empty data when services are not available
        templates = []
        pagination = create_pagination_object(page=1, total=0, per_page=20)
        flash('Card services are currently unavailable. No templates to display.', 'warning')
    else:
        # Get filter parameters
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        rarity = request.args.get('rarity', '')
        color = request.args.get('color', '')
        page = int(request.args.get('page', 1))
        
        # Build filters
        filters = {}
        if search:
            filters['search'] = search
        if category:
            filters['category'] = category
        if rarity:
            filters['rarity'] = rarity
        if color:
            filters['color'] = color
        
        # Get templates
        card_service = get_card_service()
        if card_service:
            result = card_service.get_card_templates(filters=filters, page=page, per_page=20)
            templates = result.get('templates', [])
            raw_pagination = result.get('pagination', {})
            
            # Ensure pagination has all required attributes
            pagination = create_pagination_object(
                page=raw_pagination.get('page', page),
                total=raw_pagination.get('total', 0),
                per_page=raw_pagination.get('per_page', 20)
            )
            
            # Check for generated art files
            for template in templates:
                art_filename = f"{template['slug']}.png"
                art_path = os.path.join(CARDMAKER_OUTPUT_DIR, art_filename)
                template['has_art'] = os.path.exists(art_path)
                template['art_url'] = f"/static/cards/{art_filename}" if template['has_art'] else None
        else:
            templates = []
            pagination = create_pagination_object(page=1, total=0, per_page=20)
    
    # Create filters object for template
    filters = {
        'search': request.args.get('search', ''),
        'category': request.args.get('category', ''),
        'rarity': request.args.get('rarity', ''),
        'color': request.args.get('color', '')
    }
    
    return render_template('admin/card_management/review.html',
                         templates=templates,
                         pagination=pagination,
                         filters=filters,
                         search=filters['search'],
                         selected_category=filters['category'],
                         selected_rarity=filters['rarity'],
                         selected_color=filters['color'],
                         mana_colors=MANA_COLORS,
                         categories=CATEGORIES,
                         rarities=RARITIES)


@admin_bp.route('/cards/<int:template_id>')
def card_detail(template_id):
    """Individual Card Template Detail and Edit Interface"""
    card_service = get_card_service()
    template = card_service.get_card_template(template_id)
    
    if not template:
        flash('Card template not found', 'error')
        return redirect(url_for('admin.card_review'))
    
    # Check for generated art file
    art_filename = f"{template['slug']}.png"
    art_path = os.path.join(CARDMAKER_OUTPUT_DIR, art_filename)
    template['has_art'] = os.path.exists(art_path)
    template['art_url'] = f"/static/cards/{art_filename}" if template['has_art'] else None
    
    return render_template('admin/card_management/detail.html',
                         template=template,
                         mana_colors=MANA_COLORS,
                         categories=CATEGORIES,
                         rarities=RARITIES)


@admin_bp.route('/cards/<int:template_id>/publish', methods=['POST'])
def publish_template(template_id):
    """Publish a card template (make it available for NFC production)"""
    # This would update the is_published field in the database
    # For now, just show a success message
    flash('Card template published successfully!', 'success')
    return redirect(url_for('admin.card_detail', template_id=template_id))


@admin_bp.route('/cards/<int:template_id>/create-nfc', methods=['POST'])
def create_nfc_from_template(template_id):
    """Create NFC card instance from template"""
    try:
        nfc_uid = request.form.get('nfc_uid')
        serial_number = request.form.get('serial_number')
        
        if not nfc_uid:
            flash('NFC UID is required', 'error')
            return redirect(url_for('admin.card_detail', template_id=template_id))
        
        card_service = get_card_service()
        instance_id = card_service.create_nfc_card_instance(
            template_id=template_id,
            nfc_uid=nfc_uid,
            serial_number=serial_number,
            status='provisioned'
        )
        
        if instance_id:
            flash(f'NFC card instance created successfully! (ID: {instance_id})', 'success')
        else:
            flash('Failed to create NFC card instance', 'error')
            
    except Exception as e:
        current_app.logger.error(f"NFC creation failed: {e}")
        flash(f'NFC creation failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.card_detail', template_id=template_id))


# NFC Card Instance Management Routes

@admin_bp.route('/nfc-cards')
def nfc_card_index():
    """NFC Card Instance Dashboard"""
    # This would show NFC card instance statistics
    return render_template('admin/nfc_management/index.html')


@admin_bp.route('/nfc-cards/production')
def nfc_production():
    """NFC Card Production Interface"""
    # This would show published templates available for NFC production
    return render_template('admin/nfc_management/production.html')


@admin_bp.route('/nfc-cards/tracking')
def nfc_tracking():
    """NFC Card Tracking and Ownership"""
    # This would show NFC card ownership and evolution tracking
    return render_template('admin/nfc_management/tracking.html')


@admin_bp.route('/cards/<product_sku>')
@require_admin_auth
def card_detail_admin(product_sku):
    """Individual card management page with asset viewing and regeneration (using SKU like public frontend)"""
    import os
    
    try:
        # Get card details using product SKU (same as public frontend)
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text("""
                SELECT id, name, product_sku, rarity, category, mana_colors, 
                       artwork_url, static_url, video_url, flavor_text, rules_text,
                       base_stats, generation_prompt
                FROM card_catalog 
                WHERE product_sku = :product_sku
            """), {'product_sku': product_sku})
            
            card_row = result.fetchone()
            if not card_row:
                flash('Card not found', 'error')
                return redirect('/admin/cards')
            
            card = {
                'id': card_row[0],
                'name': card_row[1],
                'product_sku': card_row[2],
                'rarity': card_row[3],
                'category': card_row[4],
                'mana_colors': card_row[5],
                'artwork_url': card_row[6],
                'static_url': card_row[7],
                'video_url': card_row[8],
                'flavor_text': card_row[9],
                'rules_text': card_row[10],
                'base_stats': card_row[11],
                'generation_prompt': card_row[12]
            }
            
        finally:
            session.close()
        
        # Check asset availability on correct disk with multiple path checking
        card_slug = card.get('name', '').lower().replace(' ', '_').replace("'", "")
        
        # Check multiple possible paths for assets
        artwork_paths = [
            f'/mnt/HC_Volume_103279349/deckport_assets/cards/artwork/{card_slug}.png',
            f'/home/jp/deckport.ai/static/cards/artwork/{card_slug}.png'
        ]
        
        framed_paths = [
            f'/mnt/HC_Volume_103279349/deckport_assets/cards/frames/{card_slug}_framed.png',
            f'/mnt/HC_Volume_103279349/deckport_assets/cards/frames/{card_slug}_frame.png',  # Check both naming patterns
            f'/home/jp/deckport.ai/static/cards/frames/{card_slug}_framed.png',
            f'/home/jp/deckport.ai/static/cards/frames/{card_slug}_frame.png',
            f'/home/jp/deckport.ai/static/cards/composite/{card_slug}_composite.png'
        ]
        
        thumbnail_paths = [
            f'/mnt/HC_Volume_103279349/deckport_assets/cards/thumbnails/{card_slug}_thumb.png',
            f'/home/jp/deckport.ai/static/cards/thumbnails/{card_slug}_thumb.png'
        ]
        
        video_paths = [
            f'/mnt/HC_Volume_103279349/deckport_assets/cards/videos/{card_slug}.mp4',
            f'/home/jp/deckport.ai/static/cards/videos/{card_slug}.mp4'
        ]
        
        asset_status = {
            'artwork': any(os.path.exists(path) for path in artwork_paths),
            'framed': any(os.path.exists(path) for path in framed_paths),
            'thumbnail': any(os.path.exists(path) for path in thumbnail_paths),
            'video': any(os.path.exists(path) for path in video_paths)
        }
        
        return render_template('admin/card_management/card_detail.html',
                             card=card,
                             card_slug=card_slug,
                             asset_status=asset_status,
                             mana_colors=MANA_COLORS)
                             
    except Exception as e:
        flash(f'Error loading card: {str(e)}', 'error')
        return redirect('/admin/cards')


@admin_bp.route('/cards/<product_sku>/regenerate', methods=['POST'])
@require_admin_auth  
def regenerate_card_assets(product_sku):
    """Regenerate assets for a single card directly via ComfyUI"""
    try:
        data = request.get_json() if request.is_json else request.form
        generation_type = data.get('generation_type', 'all')
        
        # Get card data from database
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text("""
                SELECT id, name, category, rarity, mana_colors, generation_prompt
                FROM card_catalog 
                WHERE product_sku = :product_sku
            """), {'product_sku': product_sku})
            
            card_row = result.fetchone()
            if not card_row:
                return jsonify({'success': False, 'error': 'Card not found'}), 404
            
            card_data = {
                'id': card_row[0],
                'name': card_row[1],
                'category': card_row[2],
                'rarity': card_row[3],
                'mana_colors': card_row[4],
                'generation_prompt': card_row[5]
            }
            
        finally:
            session.close()
        
        # Generate frame-aware artwork using ComfyUI
        if generation_type in ['all', 'artwork']:
            success = generate_frame_aware_artwork(card_data, generation_type)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Frame-aware asset regeneration completed for {card_data["name"]}',
                    'card_name': card_data['name'],
                    'generation_type': generation_type,
                    'improvement': 'Enhanced with frame-aware composition guidance'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'ComfyUI generation failed'
                }), 500
        else:
            return jsonify({
                'success': True,
                'message': f'Asset regeneration queued for {card_data["name"]}',
                'card_name': card_data['name'],
                'generation_type': generation_type,
                'note': 'Video generation would happen here'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



def generate_frame_aware_artwork(card_data, generation_type):
    """Generate artwork with frame-aware composition guidance"""
    try:
        from services.comfyui_service import ComfyUIService
        import json
        
        # Create frame-aware prompt
        def create_frame_aware_prompt(card_data):
            # Use the card's specific original prompt from database
            original_card_prompt = card_data.get('generation_prompt', '')
            
            # If no specific prompt, use card name and type as base
            if not original_card_prompt:
                original_card_prompt = f"Fantasy {card_data['category']} card art, {card_data['rarity']} quality, detailed digital painting, trading card game style, {card_data['name']}"
            
            # Frame guidance based on card type
            frame_guidance = {
                'hero': "heroic portrait composition, character centered and fully visible, dramatic pose within frame boundaries, leave space for frame overlay, character fits in central safe area",
                'creature': "centered portrait composition, full character visible within frame borders, leave 20% margin around character, character positioned in middle 70% of image area",
                'action_fast': "dynamic action scene, main subject centered, all important elements within frame borders, composition respects card frame area",
                'structure': "architectural composition, structure centered and complete, no edge cropping, building fits within frame boundaries"
            }
            
            rarity_guidance = {
                'rare': "enhanced composition, dramatic angles within frame bounds, artistic framing",
                'epic': "cinematic composition, epic scale but contained within frame",
                'legendary': "masterpiece composition, perfect framing, legendary character positioning"
            }
            
            category_guide = frame_guidance.get(card_data['category'], frame_guidance['creature'])
            rarity_guide = rarity_guidance.get(card_data['rarity'], "simple composition, clear subject placement")
            
            # Combine card's original prompt + frame guidance (keep each card unique)
            enhanced_prompt = f"""{original_card_prompt}

COMPOSITION GUIDANCE: {category_guide}, {rarity_guide}

FRAME REQUIREMENTS: Trading card game layout, character/subject must fit within central frame area, leave 15-20% padding on all edges for card frame overlay, no important elements touching image borders, composition designed for rectangular card frame, portrait orientation optimized for trading card display."""
            
            return enhanced_prompt
        
        # Generate with ComfyUI
        comfyui = ComfyUIService()
        
        if not comfyui.is_online():
            print("ComfyUI not online")
            return False
        
        # Load workflow and update with frame-aware prompt
        with open('/home/jp/deckport.ai/cardmaker.ai/art-generation.json', 'r') as f:
            workflow = json.load(f)
        
        enhanced_prompt = create_frame_aware_prompt(card_data)
        
        if "6" in workflow and "inputs" in workflow["6"]:
            workflow["6"]["inputs"]["text"] = enhanced_prompt
        
        # Submit to ComfyUI
        prompt_id = comfyui.submit_prompt(workflow)
        
        if prompt_id:
            # Wait for completion
            result = comfyui.wait_for_completion(prompt_id, max_wait=180)
            
            if result:
                # Save the improved artwork
                card_slug = card_data['name'].lower().replace(' ', '_').replace("'", "")
                
                # Save to all asset types
                artwork_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/artwork/{card_slug}.png"
                framed_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/frames/{card_slug}_frame.png"
                thumbnail_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/thumbnails/{card_slug}_thumb.png"
                
                # Save artwork
                with open(artwork_path, 'wb') as f:
                    f.write(result)
                
                # Use EXACT SAME pipeline as batch generation - generate all asset types correctly
                try:
                    from services.card_compositor import CardCompositor
                    from PIL import Image
                    import os
                    
                    # Initialize compositor like batch system
                    compositor = CardCompositor()
                    
                    # Define all asset paths
                    composite_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/composite/{card_slug}_composite.png"
                    frame_template_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/frames/{card_slug}_frame.png"
                    thumbnail_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/thumbnails/{card_slug}_thumb.png"
                    
                    # Step 1: Generate COMPOSITE (artwork + frame + text + stats + glow)
                    composite_img = compositor.compose_card(card_data, artwork_path, transparent_bg=False)
                    
                    if composite_img:
                        # Save complete composite card
                        composite_img.convert('RGB').save(composite_path, format='PNG', quality=95)
                        print(f"✅ Complete composite card created: {composite_path}")
                        
                        # Step 2: Generate FRAME TEMPLATE (transparent artwork area + frame + text + glow)
                        # Create transparent artwork for frame template
                        transparent_art = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
                        temp_art_path = f"/tmp/transparent_{card_slug}.png"
                        transparent_art.save(temp_art_path, format='PNG')
                        
                        # Generate transparent frame overlay
                        frame_template = compositor.compose_card(card_data, temp_art_path, transparent_bg=True)
                        
                        if frame_template:
                            frame_template.save(frame_template_path, format='PNG')
                            print(f"✅ Transparent frame template created: {frame_template_path}")
                        
                        # Clean up temp file
                        if os.path.exists(temp_art_path):
                            os.remove(temp_art_path)
                        
                        # Step 3: Generate THUMBNAIL (resized composite)
                        thumbnail_size = (200, 280)
                        thumbnail_img = composite_img.resize(thumbnail_size, Image.Resampling.LANCZOS)
                        thumbnail_img.convert('RGB').save(thumbnail_path, format='PNG', quality=85)
                        print(f"✅ Thumbnail from composite created: {thumbnail_path}")
                        
                    else:
                        print("❌ Composite generation failed - frame elements missing?")
                        # Fallback: save raw artwork to all locations
                        with open(composite_path, 'wb') as f:
                            f.write(result)
                        with open(frame_template_path, 'wb') as f:
                            f.write(result)
                        with open(thumbnail_path, 'wb') as f:
                            f.write(result)
                        
                except Exception as e:
                    print(f"❌ Asset generation error: {e}")
                    # Fallback: save raw artwork
                    with open(composite_path, 'wb') as f:
                        f.write(result)
                    with open(frame_template_path, 'wb') as f:
                        f.write(result)
                    with open(thumbnail_path, 'wb') as f:
                        f.write(result)
                
                # Update database with new URLs
                from shared.database.connection import SessionLocal
                from sqlalchemy import text
                
                session = SessionLocal()
                try:
                    session.execute(text("""
                        UPDATE card_catalog 
                        SET artwork_url = :composite_url,
                            static_url = :composite_url,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :card_id
                    """), {
                        'card_id': card_data['id'],
                        'composite_url': f'/static/cards/composite/{card_slug}_composite.png'
                    })
                    session.commit()
                finally:
                    session.close()
                
                print(f"Frame-aware artwork generated and saved for {card_data['name']}")
                return True
            else:
                print("ComfyUI generation failed")
                return False
        else:
            print("Failed to submit to ComfyUI")
            return False
    
    except Exception as e:
        print(f"Frame-aware generation error: {e}")
        return False


@admin_bp.route('/cards/<product_sku>/reposition', methods=['POST'])
@require_admin_auth
def reposition_card_artwork(product_sku):
    """Manually reposition artwork within frame and save composite"""
    try:
        data = request.get_json()
        x_offset = int(data.get('x_offset', 0))
        y_offset = int(data.get('y_offset', 0))
        scale = float(data.get('scale', 100)) / 100.0  # Convert percentage to decimal
        
        # Get card data
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text("""
                SELECT id, name, product_sku, category, rarity, mana_colors, base_stats
                FROM card_catalog 
                WHERE product_sku = :product_sku
            """), {'product_sku': product_sku})
            
            card_row = result.fetchone()
            if not card_row:
                return jsonify({'success': False, 'error': 'Card not found'}), 404
            
            card_data = {
                'id': card_row[0],
                'name': card_row[1],
                'product_sku': card_row[2],
                'category': card_row[3],
                'rarity': card_row[4],
                'mana_colors': card_row[5],
                'base_stats': card_row[6]
            }
            
        finally:
            session.close()
        
        # Create positioned and scaled composite using Pillow
        success = create_positioned_composite(card_data, x_offset, y_offset, scale)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Composite created with offset X:{x_offset}, Y:{y_offset}, Scale:{int(scale*100)}%',
                'card_name': card_data['name'],
                'positioning': {'x_offset': x_offset, 'y_offset': y_offset}
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create positioned composite'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def create_positioned_composite(card_data, x_offset, y_offset, scale=1.0):
    """Create composite with manual artwork positioning"""
    try:
        from PIL import Image
        import os
        
        card_slug = card_data['name'].lower().replace(' ', '_').replace("'", "")
        
        # Load original artwork
        artwork_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/artwork/{card_slug}.png"
        
        if not os.path.exists(artwork_path):
            print(f"Artwork not found: {artwork_path}")
            return False
        
        # Create positioned artwork temporarily, then use CardCompositor for full composite
        artwork_img = Image.open(artwork_path).convert('RGBA')
        
        # Create positioned artwork file (use same dimensions as CardCompositor)
        canvas_width, canvas_height = 1500, 2100  # Match CardCompositor canvas size
        positioned_artwork = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Use CORRECT artwork area dimensions (from frame analysis)
        art_w, art_h = artwork_img.size
        
        # Scale artwork to fit within frame's artwork area (not entire canvas)
        artwork_area_width = 1156   # Actual artwork area in frame
        artwork_area_height = 1692  # Actual artwork area in frame
        
        # Calculate scale to fit artwork area (preserving aspect ratio)
        scale_to_fit = min(artwork_area_width / art_w, artwork_area_height / art_h)
        art_width = max(1, int(art_w * scale_to_fit))
        art_height = max(1, int(art_h * scale_to_fit))
        
        # Apply additional scale factor
        art_width = int(art_width * scale)
        art_height = int(art_height * scale)
        
        # Position artwork in frame's artwork area (not canvas center)
        artwork_area_x = 168  # Artwork area starts at x=168
        artwork_area_y = 203  # Artwork area starts at y=203
        
        # Center within artwork area
        base_x = artwork_area_x + (artwork_area_width - art_width) // 2
        base_y = artwork_area_y + (artwork_area_height - art_height) // 2
        
        # Apply offset
        positioned_x = base_x + x_offset
        positioned_y = base_y + y_offset
        
        # Apply scale factor to artwork dimensions
        scaled_art_width = int(art_width * scale)
        scaled_art_height = int(art_height * scale)
        
        # Resize artwork preserving aspect ratio with scale
        artwork_resized = artwork_img.resize((scaled_art_width, scaled_art_height), Image.Resampling.LANCZOS)
        positioned_artwork.paste(artwork_resized, (positioned_x, positioned_y), artwork_resized)
        
        # Save positioned artwork temporarily
        temp_positioned_path = f"/tmp/positioned_{card_slug}.png"
        positioned_artwork.save(temp_positioned_path, format='PNG')
        
        # Use CardCompositor to create full composite with positioned artwork
        from services.card_compositor import CardCompositor
        compositor = CardCompositor()
        
        # Generate COMPLETE composite (positioned artwork + frame + glow + text + icons)
        full_composite = compositor.compose_card(card_data, temp_positioned_path, transparent_bg=False)
        
        if full_composite:
            # Save paths
            composite_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/composite/{card_slug}_composite.png"
            thumbnail_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/thumbnails/{card_slug}_thumb.png"
            
            # Save complete composite (not just artwork!)
            full_composite.convert('RGB').save(composite_path, format='PNG', quality=95)
            
            # Generate thumbnail from complete composite
            thumbnail_img = full_composite.resize((200, 280), Image.Resampling.LANCZOS)
            thumbnail_img.convert('RGB').save(thumbnail_path, format='PNG', quality=85)
            
            # Clean up temp file
            if os.path.exists(temp_positioned_path):
                os.remove(temp_positioned_path)
        else:
            print("Failed to create full composite, saving positioned artwork only")
            # Fallback: save positioned artwork
            composite_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/composite/{card_slug}_composite.png"
            thumbnail_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/thumbnails/{card_slug}_thumb.png"
            
            positioned_artwork.convert('RGB').save(composite_path, format='PNG', quality=95)
            thumbnail_img = positioned_artwork.resize((200, 280), Image.Resampling.LANCZOS)
            thumbnail_img.convert('RGB').save(thumbnail_path, format='PNG', quality=85)
        
        print(f"Positioned composite created for {card_data['name']} with offset X:{x_offset}, Y:{y_offset}")
        return True
        
    except Exception as e:
        print(f"Positioning error: {e}")
        return False


@admin_bp.route('/cards/<product_sku>/generate-video', methods=['POST'])
@require_admin_auth
def generate_card_video(product_sku):
    """Generate video clip for card using CardVideo.json workflow"""
    try:
        data = request.get_json() if request.is_json else request.form
        generation_type = data.get('generation_type', 'video_clip')
        
        # Get card data
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            result = session.execute(text("""
                SELECT id, name, product_sku, category, rarity, mana_colors
                FROM card_catalog 
                WHERE product_sku = :product_sku
            """), {'product_sku': product_sku})
            
            card_row = result.fetchone()
            if not card_row:
                return jsonify({'success': False, 'error': 'Card not found'}), 404
            
            card_data = {
                'id': card_row[0],
                'name': card_row[1],
                'product_sku': card_row[2],
                'category': card_row[3],
                'rarity': card_row[4],
                'mana_colors': card_row[5]
            }
            
        finally:
            session.close()
        
        # Generate video clip using existing artwork
        success = generate_video_from_artwork(card_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Video clip generated for {card_data["name"]}',
                'card_name': card_data['name'],
                'generation_type': 'video_clip',
                'video_url': f'/static/cards/videos/{card_data["name"].lower().replace(" ", "_").replace("'", "")}.mp4'
            })
        else:
            return jsonify({'success': False, 'error': 'Video generation failed'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_video_from_artwork(card_data):
    """Generate video clip using CardVideo.json workflow"""
    try:
        from services.comfyui_service import ComfyUIService
        import json
        import os
        
        card_slug = card_data['name'].lower().replace(' ', '_').replace("'", "")
        
        # Check if artwork exists
        artwork_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/artwork/{card_slug}.png"
        if not os.path.exists(artwork_path):
            print(f"Artwork not found for video generation: {artwork_path}")
            return False
        
        # Initialize ComfyUI
        comfyui = ComfyUIService()
        if not comfyui.is_online():
            print("ComfyUI not online for video generation")
            return False
        
        # Load CardVideo.json workflow
        video_workflow_path = '/home/jp/deckport.ai/cardmaker.ai/CardVideo.json'
        with open(video_workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Create video prompt based on card
        video_prompt = create_video_prompt_for_card(card_data)
        
        # Update workflow to use NFS mounted path for remote ComfyUI server
        # ComfyUI server should mount: 5.161.100.149:/mnt/HC_Volume_103279349/deckport_assets
        # to: /mnt/deckport_assets
        
        mounted_artwork_path = f"/mnt/deckport_assets/cards/artwork/{card_slug}.png"
        
        if "148" in workflow:
            workflow["148"]["inputs"]["image"] = mounted_artwork_path
        
        if "105" in workflow and "inputs" in workflow["105"]:
            workflow["105"]["inputs"]["text"] = video_prompt
        
        if "69" in workflow:
            # Save to mounted storage path so we can access the video
            workflow["69"]["inputs"]["filename_prefix"] = f"/mnt/deckport_assets/cards/videos/{card_slug}"
        
        print(f"Generating video for {card_data['name']} with prompt: {video_prompt}")
        
        # Submit to ComfyUI
        prompt_id = comfyui.submit_prompt(workflow)
        
        if prompt_id:
            print(f"Video generation submitted: {prompt_id}")
            
            # Return immediately - don't wait for completion (async generation)
            # Video generation will complete in background
            return True  # Success - job started
        else:
            return False  # Failed to start
            
        # Note: The following code is for reference but not executed due to async return
        if False:  # Placeholder for future sync implementation
            result = comfyui.wait_for_completion(prompt_id, max_wait=300)
            
            if result:
                # Save video
                video_path = f"/mnt/HC_Volume_103279349/deckport_assets/cards/videos/{card_slug}.mp4"
                
                with open(video_path, 'wb') as f:
                    f.write(result)
                
                # Update database
                from shared.database.connection import SessionLocal
                from sqlalchemy import text
                
                session = SessionLocal()
                try:
                    session.execute(text("""
                        UPDATE card_catalog 
                        SET video_url = :video_url,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :card_id
                    """), {
                        'card_id': card_data['id'],
                        'video_url': f'/static/cards/videos/{card_slug}.mp4'
                    })
                    session.commit()
                finally:
                    session.close()
                
                print(f"Video generated for {card_data['name']}")
                return True
            else:
                return False
        else:
            return False
    
    except Exception as e:
        print(f"Video generation error: {e}")
        return False


def create_video_prompt_for_card(card_data):
    """Create video-specific prompt based on card properties"""
    
    video_prompts = {
        'hero': "Epic hero with subtle cape movement, commanding aura, gentle breathing animation",
        'creature': "Living creature with natural breathing, subtle movement, ambient magical effects",
        'action_fast': "Dynamic energy effects, magical power manifestation, swirling energy",
        'structure': "Architectural ambiance, mystical atmosphere, environmental effects"
    }
    
    rarity_effects = {
        'rare': "enhanced magical effects, more dynamic animation", 
        'epic': "powerful magical aura, dramatic effects",
        'legendary': "legendary power manifestation, intense magical effects"
    }
    
    base_prompt = video_prompts.get(card_data['category'], video_prompts['creature'])
    rarity_effect = rarity_effects.get(card_data['rarity'], "subtle effects")
    
    return f"{base_prompt}, {rarity_effect}, seamless 3-second loop, cinemagraph style"


@admin_bp.route('/cards/<product_sku>/update', methods=['POST'])
@require_admin_auth
def update_card_details(product_sku):
    """Update card details (name, rarity, category, flavor text, prompts)"""
    try:
        data = request.get_json()
        
        # Get update data
        name = data.get('name', '').strip()
        rarity = data.get('rarity', '').strip()
        category = data.get('category', '').strip()
        flavor_text = data.get('flavor_text', '').strip()
        generation_prompt = data.get('generation_prompt', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Card name is required'}), 400
        
        # Update card in database
        from shared.database.connection import SessionLocal
        from sqlalchemy import text
        
        session = SessionLocal()
        try:
            # Update card details
            session.execute(text("""
                UPDATE card_catalog 
                SET name = :name,
                    rarity = :rarity,
                    category = :category,
                    flavor_text = :flavor_text,
                    generation_prompt = :generation_prompt,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_sku = :product_sku
            """), {
                'product_sku': product_sku,
                'name': name,
                'rarity': rarity,
                'category': category,
                'flavor_text': flavor_text,
                'generation_prompt': generation_prompt
            })
            
            # Check if update was successful
            result = session.execute(text("""
                SELECT COUNT(*) FROM card_catalog WHERE product_sku = :product_sku
            """), {'product_sku': product_sku})
            
            if result.scalar() > 0:
                session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Card {name} updated successfully',
                    'updated_fields': {
                        'name': name,
                        'rarity': rarity,
                        'category': category,
                        'flavor_text': flavor_text,
                        'generation_prompt': generation_prompt
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Card not found'}), 404
                
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
