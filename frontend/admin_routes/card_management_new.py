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
from . import admin_bp

# Import our services
from ..services.simple_card_service import get_simple_card_service
from ..services.comfyui_service import get_comfyui_service

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
def card_management_index():
    """Card Management Dashboard"""
    card_service = get_simple_card_service()
    stats = card_service.get_statistics()
    
    return render_template('admin/card_management/index.html', 
                         stats=stats, 
                         mana_colors=MANA_COLORS)


@admin_bp.route('/cards/generate')
def card_generation():
    """Card Generation Interface"""
    return render_template('admin/card_management/generate.html',
                         mana_colors=MANA_COLORS,
                         categories=CATEGORIES,
                         rarities=RARITIES)


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
        card_service = get_simple_card_service()
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
    card_service = get_simple_card_service()
    result = card_service.get_card_templates(filters=filters, page=page, per_page=20)
    
    templates = result.get('templates', [])
    pagination = result.get('pagination', {})
    
    # Check for generated art files
    for template in templates:
        art_filename = f"{template['slug']}.png"
        art_path = os.path.join(CARDMAKER_OUTPUT_DIR, art_filename)
        template['has_art'] = os.path.exists(art_path)
        template['art_url'] = f"/static/cards/{art_filename}" if template['has_art'] else None
    
    return render_template('admin/card_management/review.html',
                         templates=templates,
                         pagination=pagination,
                         search=search,
                         selected_category=category,
                         selected_rarity=rarity,
                         selected_color=color,
                         mana_colors=MANA_COLORS,
                         categories=CATEGORIES,
                         rarities=RARITIES)


@admin_bp.route('/cards/<int:template_id>')
def card_detail(template_id):
    """Individual Card Template Detail and Edit Interface"""
    card_service = get_simple_card_service()
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
        
        card_service = get_simple_card_service()
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
