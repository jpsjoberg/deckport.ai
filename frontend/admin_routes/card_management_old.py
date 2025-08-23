"""
Card Management Routes for Deckport Admin Panel
Handles card generation, review, balance management, and ComfyUI integration
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from . import admin_bp

# Import our services
from ..services.simple_card_service import get_simple_card_service
from ..services.comfyui_service import get_comfyui_service

# Configuration for ComfyUI and card generation
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "http://localhost:8188")
COMFYUI_TIMEOUT = int(os.environ.get("COMFYUI_TIMEOUT", "120"))
CARDMAKER_DB_PATH = os.environ.get("CARDMAKER_DB_PATH", "/home/jp/deckport.ai/cardmaker.ai/deckport.sqlite3")
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


def get_db_connection():
    """Get SQLite database connection for card data"""
    try:
        conn = sqlite3.connect(CARDMAKER_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        current_app.logger.error(f"Database connection failed: {e}")
        return None


def call_comfyui_api(endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
    """Call ComfyUI API on external server"""
    try:
        url = f"{COMFYUI_HOST}{endpoint}"
        if method == 'GET':
            response = requests.get(url, timeout=COMFYUI_TIMEOUT)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=COMFYUI_TIMEOUT)
        else:
            return None
            
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f"ComfyUI API error: {response.status_code} - {response.text}")
            return None
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
    comfyui_service = get_comfyui_service()
    comfyui_status = comfyui_service.is_online()
    
    return render_template('admin/card_management/generate.html',
                         mana_colors=MANA_COLORS,
                         rarities=RARITIES,
                         categories=CATEGORIES,
                         comfyui_status=comfyui_status,
                         comfyui_host=comfyui_service.host)


@admin_bp.route('/cards/generate', methods=['POST'])
def generate_card():
    """Generate a new card using ComfyUI"""
    try:
        # Get form data
        card_data = {
            'name': request.form.get('name'),
            'category': request.form.get('category'),
            'rarity': request.form.get('rarity'),
            'color_code': request.form.get('color_code'),
            'mana_cost': int(request.form.get('mana_cost', 0)),
            'energy_cost': int(request.form.get('energy_cost', 0)),
            'attack': int(request.form.get('attack', 0)),
            'defense': int(request.form.get('defense', 0)),
            'health': int(request.form.get('health', 0)),
            'base_energy_per_turn': int(request.form.get('base_energy_per_turn', 0)),
            'equipment_slots': int(request.form.get('equipment_slots', 0)),
            'image_prompt': request.form.get('image_prompt', ''),
            'keywords': request.form.get('keywords', ''),
        }
        
        # Validate required fields
        if not all([card_data['name'], card_data['category'], card_data['image_prompt']]):
            flash('Name, category, and image prompt are required', 'error')
            return redirect(url_for('admin.card_generation'))
        
        # Generate slug from name
        slug = card_data['name'].lower().replace(' ', '-').replace("'", "")
        
        # Load ComfyUI workflow template
        workflow_path = '/home/jp/deckport.ai/cardmaker.ai/art-generation.json'
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Update workflow with card prompt
        if "6" in workflow and "inputs" in workflow["6"]:
            workflow["6"]["inputs"]["text"] = card_data['image_prompt']
        
        # Generate art via ComfyUI
        prompt_data = {"prompt": workflow, "client_id": "deckport-admin"}
        result = call_comfyui_api('/prompt', 'POST', prompt_data)
        
        if not result:
            flash('Failed to generate card art via ComfyUI', 'error')
            return redirect(url_for('admin.card_generation'))
        
        prompt_id = result.get('prompt_id')
        if not prompt_id:
            flash('Invalid response from ComfyUI', 'error')
            return redirect(url_for('admin.card_generation'))
        
        # Store card in database (without art initially)
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin.card_generation'))
        
        try:
            cursor = conn.cursor()
            
            # Insert card
            cursor.execute("""
                INSERT INTO cards (slug, name, category, rarity, legendary, color_code, 
                                 energy_cost, equipment_slots, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug, card_data['name'], card_data['category'], card_data['rarity'],
                1 if card_data['rarity'] == 'LEGENDARY' else 0, card_data['color_code'],
                card_data['energy_cost'], card_data['equipment_slots'], 
                datetime.now().isoformat()
            ))
            
            card_id = cursor.lastrowid
            
            # Insert stats
            cursor.execute("""
                INSERT INTO card_stats (card_id, attack, defense, health, base_energy_per_turn)
                VALUES (?, ?, ?, ?, ?)
            """, (card_id, card_data['attack'], card_data['defense'], 
                  card_data['health'], card_data['base_energy_per_turn']))
            
            # Insert mana cost
            cursor.execute("""
                INSERT INTO card_mana_costs (card_id, color_code, amount)
                VALUES (?, ?, ?)
            """, (card_id, card_data['color_code'], card_data['mana_cost']))
            
            # Insert targeting (default values)
            cursor.execute("""
                INSERT INTO card_targeting (card_id, target_friendly, target_enemy, target_self)
                VALUES (?, ?, ?, ?)
            """, (card_id, 0, 1, 0))
            
            conn.commit()
            
            flash(f'Card "{card_data["name"]}" created successfully! Art generation in progress (ID: {prompt_id})', 'success')
            return redirect(url_for('admin.card_review'))
            
        finally:
            conn.close()
            
    except Exception as e:
        current_app.logger.error(f"Card generation error: {e}")
        flash(f'Card generation failed: {str(e)}', 'error')
        return redirect(url_for('admin.card_generation'))


@admin_bp.route('/cards/review')
def card_review():
    """Card Review and Management Interface"""
    # Get filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    rarity = request.args.get('rarity', '')
    color = request.args.get('color', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'error')
        return render_template('admin/card_management/review.html', cards=[], pagination={})
    
    try:
        cursor = conn.cursor()
        
        # Build query with filters
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("(c.name LIKE ? OR c.slug LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category:
            where_clauses.append("c.category = ?")
            params.append(category)
            
        if rarity:
            where_clauses.append("c.rarity = ?")
            params.append(rarity)
            
        if color:
            where_clauses.append("c.color_code = ?")
            params.append(color)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) FROM cards c WHERE {where_sql}"
        cursor.execute(count_query, params)
        total_cards = cursor.fetchone()[0]
        
        # Get cards with stats
        offset = (page - 1) * per_page
        query = f"""
            SELECT c.*, s.attack, s.defense, s.health, s.base_energy_per_turn,
                   mc.amount as mana_cost
            FROM cards c
            LEFT JOIN card_stats s ON c.id = s.card_id
            LEFT JOIN card_mana_costs mc ON c.id = mc.card_id
            WHERE {where_sql}
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        cursor.execute(query, params)
        cards = [dict(row) for row in cursor.fetchall()]
        
        # Calculate pagination
        total_pages = (total_cards + per_page - 1) // per_page
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_cards,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None
        }
        
        return render_template('admin/card_management/review.html',
                             cards=cards,
                             pagination=pagination,
                             filters={
                                 'search': search,
                                 'category': category,
                                 'rarity': rarity,
                                 'color': color
                             },
                             mana_colors=MANA_COLORS,
                             categories=CATEGORIES,
                             rarities=RARITIES)
    finally:
        conn.close()


@admin_bp.route('/cards/<int:card_id>')
def card_detail(card_id):
    """Individual Card Detail and Edit Interface"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'error')
        return redirect(url_for('admin.card_review'))
    
    try:
        cursor = conn.cursor()
        
        # Get card with all related data
        cursor.execute("""
            SELECT c.*, s.attack, s.defense, s.health, s.base_energy_per_turn,
                   mc.amount as mana_cost, mc.color_code as mana_color,
                   t.target_friendly, t.target_enemy, t.target_self
            FROM cards c
            LEFT JOIN card_stats s ON c.id = s.card_id
            LEFT JOIN card_mana_costs mc ON c.id = mc.card_id
            LEFT JOIN card_targeting t ON c.id = t.card_id
            WHERE c.id = ?
        """, (card_id,))
        
        card = cursor.fetchone()
        if not card:
            flash('Card not found', 'error')
            return redirect(url_for('admin.card_review'))
        
        card = dict(card)
        
        # Check for generated art file
        art_filename = f"{card['slug']}.png"
        art_path = os.path.join(CARDMAKER_OUTPUT_DIR, art_filename)
        card['has_art'] = os.path.exists(art_path)
        card['art_url'] = f"/static/cards/{art_filename}" if card['has_art'] else None
        
        return render_template('admin/card_management/detail.html',
                             card=card,
                             mana_colors=MANA_COLORS,
                             categories=CATEGORIES,
                             rarities=RARITIES)
    finally:
        conn.close()


@admin_bp.route('/cards/<int:card_id>/edit', methods=['POST'])
def edit_card(card_id):
    """Edit card details"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'error')
        return redirect(url_for('admin.card_detail', card_id=card_id))
    
    try:
        # Get form data
        name = request.form.get('name')
        category = request.form.get('category')
        rarity = request.form.get('rarity')
        color_code = request.form.get('color_code')
        mana_cost = int(request.form.get('mana_cost', 0))
        energy_cost = int(request.form.get('energy_cost', 0))
        attack = int(request.form.get('attack', 0))
        defense = int(request.form.get('defense', 0))
        health = int(request.form.get('health', 0))
        base_energy_per_turn = int(request.form.get('base_energy_per_turn', 0))
        equipment_slots = int(request.form.get('equipment_slots', 0))
        
        cursor = conn.cursor()
        
        # Update card
        cursor.execute("""
            UPDATE cards 
            SET name=?, category=?, rarity=?, legendary=?, color_code=?, 
                energy_cost=?, equipment_slots=?, updated_at=?
            WHERE id=?
        """, (name, category, rarity, 1 if rarity == 'LEGENDARY' else 0,
              color_code, energy_cost, equipment_slots, 
              datetime.now().isoformat(), card_id))
        
        # Update stats
        cursor.execute("""
            UPDATE card_stats 
            SET attack=?, defense=?, health=?, base_energy_per_turn=?
            WHERE card_id=?
        """, (attack, defense, health, base_energy_per_turn, card_id))
        
        # Update mana cost
        cursor.execute("""
            UPDATE card_mana_costs 
            SET color_code=?, amount=?
            WHERE card_id=?
        """, (color_code, mana_cost, card_id))
        
        conn.commit()
        flash('Card updated successfully', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Card edit error: {e}")
        flash(f'Failed to update card: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.card_detail', card_id=card_id))


@admin_bp.route('/cards/<int:card_id>/delete', methods=['POST'])
def delete_card(card_id):
    """Delete a card"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'error')
        return redirect(url_for('admin.card_review'))
    
    try:
        cursor = conn.cursor()
        
        # Get card name for confirmation
        cursor.execute("SELECT name FROM cards WHERE id = ?", (card_id,))
        card = cursor.fetchone()
        if not card:
            flash('Card not found', 'error')
            return redirect(url_for('admin.card_review'))
        
        # Delete card (cascade will handle related tables)
        cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.commit()
        
        flash(f'Card "{card[0]}" deleted successfully', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Card deletion error: {e}")
        flash(f'Failed to delete card: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.card_review'))


@admin_bp.route('/api/comfyui/status')
def comfyui_status():
    """Check ComfyUI server status"""
    status = call_comfyui_api('/system_stats')
    return jsonify({
        'online': status is not None,
        'stats': status if status else {}
    })


@admin_bp.route('/api/cards/bulk-action', methods=['POST'])
def bulk_card_action():
    """Perform bulk actions on multiple cards"""
    action = request.json.get('action')
    card_ids = request.json.get('card_ids', [])
    
    if not action or not card_ids:
        return jsonify({'error': 'Action and card IDs required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        if action == 'delete':
            placeholders = ','.join(['?' for _ in card_ids])
            cursor.execute(f"DELETE FROM cards WHERE id IN ({placeholders})", card_ids)
            conn.commit()
            return jsonify({'message': f'{len(card_ids)} cards deleted successfully'})
        
        elif action == 'update_rarity':
            new_rarity = request.json.get('value')
            if not new_rarity:
                return jsonify({'error': 'New rarity value required'}), 400
            
            placeholders = ','.join(['?' for _ in card_ids])
            cursor.execute(f"""
                UPDATE cards 
                SET rarity=?, legendary=?, updated_at=?
                WHERE id IN ({placeholders})
            """, [new_rarity, 1 if new_rarity == 'LEGENDARY' else 0, 
                  datetime.now().isoformat()] + card_ids)
            conn.commit()
            return jsonify({'message': f'{len(card_ids)} cards updated to {new_rarity}'})
        
        else:
            return jsonify({'error': 'Unknown action'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Bulk action error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
