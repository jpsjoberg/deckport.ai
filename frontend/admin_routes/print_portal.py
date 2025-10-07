"""
Print Portal Routes for Card Production Suppliers
Handles print orders, file downloads, and logistics tracking
"""

from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, session
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, func, and_, or_
from shared.database.connection import SessionLocal
from shared.models.base import CardCatalog
from shared.auth.decorators import admin_required
import os
import json
import zipfile
import tempfile
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

print_portal_bp = Blueprint('print_portal', __name__, url_prefix='/print-portal')

# Card production costs per rarity
CARD_COSTS = {
    'common': Decimal('1.29'),
    'rare': Decimal('1.99'), 
    'epic': Decimal('3.99'),
    'legendary': Decimal('5.99')
}

# Mana colors and their themes
MANA_COLORS = {
    'CRIMSON': {'name': 'Crimson Dominion', 'theme': 'Aggressive damage and direct effects', 'color': '#DC2626'},
    'AZURE': {'name': 'Azure Depths', 'theme': 'Control and card manipulation', 'color': '#2563EB'},
    'VERDANT': {'name': 'Verdant Wilds', 'theme': 'Healing and growth mechanics', 'color': '#16A34A'},
    'OBSIDIAN': {'name': 'Obsidian Shadows', 'theme': 'Dark magic and life drain', 'color': '#1F2937'},
    'RADIANT': {'name': 'Radiant Light', 'theme': 'Light magic and protection', 'color': '#F59E0B'},
    'AETHER': {'name': 'Aether Nexus', 'theme': 'Artifacts and colorless flexibility', 'color': '#EA580C'}
}

@print_portal_bp.route('/')
def print_portal_dashboard():
    """Print supplier portal dashboard"""
    try:
        with SessionLocal() as session:
            # Get card statistics
            stats = get_card_statistics(session)
            
            # Get available print orders
            active_orders = get_active_print_orders()
            
            # Calculate production costs
            production_costs = calculate_production_costs(stats)
            
            return render_template('print_portal/dashboard.html', 
                                 stats=stats,
                                 active_orders=active_orders,
                                 production_costs=production_costs,
                                 mana_colors=MANA_COLORS,
                                 card_costs=CARD_COSTS)
    
    except Exception as e:
        logger.error(f"Error loading print portal dashboard: {e}")
        return render_template('print_portal/error.html', 
                             error="Failed to load dashboard"), 500

@print_portal_bp.route('/sets')
def available_sets():
    """Show available card sets for printing"""
    try:
        with SessionLocal() as session:
            # Get cards by mana color
            color_sets = {}
            
            for color_code, color_info in MANA_COLORS.items():
                # Get cards for this color
                cards_query = text("""
                    SELECT id, product_sku, name, rarity, category, 
                           artwork_url, static_url, base_stats
                    FROM card_catalog 
                    WHERE mana_colors = :mana_color
                    ORDER BY rarity, name
                """)
                
                cards_result = session.execute(cards_query, {'mana_color': f'{{{color_code}}}'})
                cards = []
                
                for row in cards_result:
                    cards.append({
                        'id': row[0],
                        'product_sku': row[1],
                        'name': row[2],
                        'rarity': row[3],
                        'category': row[4],
                        'artwork_url': row[5],
                        'static_url': row[6],
                        'cost': float(CARD_COSTS.get(row[3], Decimal('1.29')))
                    })
                
                # Calculate set statistics
                rarity_counts = {}
                total_cost = Decimal('0.00')
                
                for card in cards:
                    rarity = card['rarity']
                    rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
                    total_cost += CARD_COSTS.get(rarity, Decimal('1.29'))
                
                color_sets[color_code] = {
                    'info': color_info,
                    'cards': cards,
                    'total_cards': len(cards),
                    'rarity_distribution': rarity_counts,
                    'total_production_cost': float(total_cost),
                    'average_cost_per_card': float(total_cost / len(cards)) if cards else 0
                }
            
            return render_template('print_portal/sets.html', 
                                 color_sets=color_sets,
                                 card_costs=CARD_COSTS)
    
    except Exception as e:
        logger.error(f"Error loading available sets: {e}")
        return render_template('print_portal/error.html', 
                             error="Failed to load card sets"), 500

@print_portal_bp.route('/create-order')
def create_print_order():
    """Create new print order interface"""
    try:
        with SessionLocal() as session:
            # Get available cards by color for selection
            color_stats = {}
            
            for color_code, color_info in MANA_COLORS.items():
                # Get card count and cost breakdown by rarity
                rarity_query = text("""
                    SELECT rarity, COUNT(*) as count
                    FROM card_catalog 
                    WHERE mana_colors = :mana_color
                    GROUP BY rarity
                """)
                
                rarity_result = session.execute(rarity_query, {'mana_color': f'{{{color_code}}}'})
                rarity_breakdown = {row[0]: row[1] for row in rarity_result}
                
                # Calculate costs
                color_cost = Decimal('0.00')
                for rarity, count in rarity_breakdown.items():
                    color_cost += CARD_COSTS.get(rarity, Decimal('1.29')) * count
                
                color_stats[color_code] = {
                    'info': color_info,
                    'total_cards': sum(rarity_breakdown.values()),
                    'rarity_breakdown': rarity_breakdown,
                    'total_cost': float(color_cost),
                    'average_cost': float(color_cost / sum(rarity_breakdown.values())) if rarity_breakdown else 0
                }
            
            return render_template('print_portal/create_order.html',
                                 color_stats=color_stats,
                                 card_costs=CARD_COSTS)
    
    except Exception as e:
        logger.error(f"Error creating print order interface: {e}")
        return render_template('print_portal/error.html', 
                             error="Failed to load order creation"), 500

@print_portal_bp.route('/download/set/<color>')
def download_color_set(color):
    """Download print files for a specific color set"""
    if color not in MANA_COLORS:
        return jsonify({"error": "Invalid color specified"}), 400
    
    try:
        # Create temporary ZIP file with all print files for this color
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f'{color}_print_package.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add print manifest
            manifest = generate_print_manifest(color)
            manifest_path = os.path.join(temp_dir, 'print_manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            zip_file.write(manifest_path, 'print_manifest.json')
            
            # Add card images (if they exist)
            with SessionLocal() as session:
                cards_query = text("""
                    SELECT product_sku, name, rarity, static_url, artwork_url
                    FROM card_catalog 
                    WHERE mana_colors = :mana_color
                    ORDER BY rarity, name
                """)
                
                cards_result = session.execute(cards_query, {'mana_color': f'{{{color}}}'})
                
                for row in cards_result:
                    product_sku, name, rarity, static_url, artwork_url = row
                    
                    # Try to find card image files
                    image_url = static_url or artwork_url
                    if image_url:
                        # Convert URL to file path
                        image_path = convert_url_to_path(image_url)
                        if os.path.exists(image_path):
                            zip_file.write(image_path, f'{product_sku}_{name.replace(" ", "_")}.png')
            
            # Add quality specifications
            specs_path = '/home/jp/deckport.ai/static/print_specs/card_specifications.pdf'
            if os.path.exists(specs_path):
                zip_file.write(specs_path, 'card_specifications.pdf')
        
        return send_file(zip_path, as_attachment=True, 
                        download_name=f'{color}_print_package.zip')
    
    except Exception as e:
        logger.error(f"Error creating print package for {color}: {e}")
        return jsonify({"error": "Failed to create print package"}), 500

@print_portal_bp.route('/manifest/<color>')
def get_print_manifest(color):
    """Get print manifest for a color set"""
    if color not in MANA_COLORS:
        return jsonify({"error": "Invalid color specified"}), 400
    
    try:
        manifest = generate_print_manifest(color)
        return jsonify(manifest)
    
    except Exception as e:
        logger.error(f"Error generating manifest for {color}: {e}")
        return jsonify({"error": "Failed to generate manifest"}), 500

@print_portal_bp.route('/order', methods=['POST'])
def submit_print_order():
    """Submit new print order"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No order data provided"}), 400
        
        # Validate order data
        color = data.get('color')
        pack_quantity = data.get('pack_quantity', 0)
        
        if color not in MANA_COLORS:
            return jsonify({"error": "Invalid color specified"}), 400
        
        if pack_quantity <= 0:
            return jsonify({"error": "Invalid pack quantity"}), 400
        
        # Create print order
        order = create_print_order(color, pack_quantity)
        
        return jsonify({
            "success": True,
            "order_id": order['order_id'],
            "order_number": order['order_number'],
            "total_cards": order['total_cards'],
            "estimated_cost": order['estimated_cost'],
            "estimated_delivery": order['estimated_delivery']
        })
    
    except Exception as e:
        logger.error(f"Error submitting print order: {e}")
        return jsonify({"error": "Failed to submit order"}), 500

def get_card_statistics(session):
    """Get comprehensive card statistics"""
    try:
        # Total cards
        total_result = session.execute(text("SELECT COUNT(*) FROM card_catalog"))
        total_cards = total_result.scalar() or 0
        
        # Cards with graphics
        graphics_result = session.execute(text("""
            SELECT COUNT(*) FROM card_catalog 
            WHERE static_url IS NOT NULL OR artwork_url IS NOT NULL
        """))
        cards_with_graphics = graphics_result.scalar() or 0
        
        # Rarity distribution
        rarity_result = session.execute(text("""
            SELECT rarity, COUNT(*) as count
            FROM card_catalog 
            GROUP BY rarity
        """))
        rarity_stats = {row[0]: row[1] for row in rarity_result}
        
        # Color distribution
        color_result = session.execute(text("""
            SELECT mana_colors, COUNT(*) as count
            FROM card_catalog 
            WHERE mana_colors IS NOT NULL
            GROUP BY mana_colors
        """))
        color_stats = {row[0][0] if row[0] else 'UNKNOWN': row[1] for row in color_result}
        
        return {
            'total_cards': total_cards,
            'cards_with_graphics': cards_with_graphics,
            'graphics_completion': round((cards_with_graphics / total_cards * 100), 1) if total_cards > 0 else 0,
            'by_rarity': rarity_stats,
            'by_color': color_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting card statistics: {e}")
        return {}

def calculate_production_costs(stats):
    """Calculate production costs based on card distribution and rarity costs"""
    costs = {}
    
    # Calculate cost per color set
    for color_code, color_info in MANA_COLORS.items():
        color_cards = stats['by_color'].get(color_code, 0)
        
        # Estimate cost based on rarity distribution
        if color_cards > 0:
            # Assume same rarity distribution as overall catalog
            total_rarity_cards = sum(stats['by_rarity'].values())
            
            estimated_cost = Decimal('0.00')
            for rarity, count in stats['by_rarity'].items():
                rarity_percentage = count / total_rarity_cards
                estimated_color_cards = int(color_cards * rarity_percentage)
                estimated_cost += CARD_COSTS.get(rarity, Decimal('1.29')) * estimated_color_cards
            
            costs[color_code] = {
                'total_cards': color_cards,
                'estimated_cost': float(estimated_cost),
                'average_cost_per_card': float(estimated_cost / color_cards) if color_cards > 0 else 0
            }
    
    return costs

def generate_print_manifest(color):
    """Generate print manifest for a color set"""
    try:
        with SessionLocal() as session:
            # Get cards for this color
            cards_query = text("""
                SELECT id, product_sku, name, rarity, category, 
                       static_url, artwork_url, base_stats
                FROM card_catalog 
                WHERE mana_colors = :mana_color
                ORDER BY rarity, name
            """)
            
            cards_result = session.execute(cards_query, {'mana_color': f'{{{color}}}'})
            
            manifest = {
                'order_info': {
                    'color_set': color,
                    'color_name': MANA_COLORS[color]['name'],
                    'generated_date': datetime.now().isoformat(),
                    'total_cards': 0,
                    'estimated_cost': 0.0
                },
                'cards': [],
                'rarity_summary': {'common': 0, 'rare': 0, 'epic': 0, 'legendary': 0},
                'production_specs': {
                    'card_dimensions': '63mm × 88mm',
                    'card_thickness': '0.76mm',
                    'material': 'Premium PVC with embedded NFC',
                    'nfc_chip': 'NTAG 424 DNA',
                    'print_resolution': '300 DPI',
                    'finish': 'Matte with UV coating'
                }
            }
            
            total_cost = Decimal('0.00')
            
            for row in cards_result:
                card_id, product_sku, name, rarity, category, static_url, artwork_url = row[:7]
                
                card_cost = CARD_COSTS.get(rarity, Decimal('1.29'))
                total_cost += card_cost
                
                manifest['cards'].append({
                    'id': card_id,
                    'product_sku': product_sku,
                    'name': name,
                    'rarity': rarity,
                    'category': category,
                    'production_cost': float(card_cost),
                    'print_file': f'{product_sku}_300dpi.pdf',
                    'image_url': static_url or artwork_url,
                    'nfc_programming': {
                        'chip_type': 'NTAG_424_DNA',
                        'security_level': 'AES-128',
                        'batch_prefix': f'{color[:2]}{card_id:03d}'
                    },
                    'batch_tracking': {
                        'batch_number': f'{product_sku}-{datetime.now().strftime("%Y%m%d")}-001',
                        'print_date': datetime.now().date().isoformat(),
                        'quality_requirements': 'Premium gaming grade'
                    }
                })
                
                # Update rarity summary
                manifest['rarity_summary'][rarity] = manifest['rarity_summary'].get(rarity, 0) + 1
            
            manifest['order_info']['total_cards'] = len(manifest['cards'])
            manifest['order_info']['estimated_cost'] = float(total_cost)
            
            return manifest
    
    except Exception as e:
        logger.error(f"Error generating print manifest for {color}: {e}")
        return {}

def get_active_print_orders():
    """Get active print orders (placeholder for now)"""
    return [
        {
            'order_id': 'PO-2025-001',
            'order_name': 'Crimson Dominion Starter Set',
            'color': 'CRIMSON',
            'status': 'pending',
            'total_cards': 15000,
            'estimated_cost': 19350.00,
            'created_date': '2025-09-15',
            'estimated_delivery': '2025-09-25'
        },
        {
            'order_id': 'PO-2025-002', 
            'order_name': 'Azure Depths Starter Set',
            'color': 'AZURE',
            'status': 'in_production',
            'total_cards': 15000,
            'estimated_cost': 19350.00,
            'created_date': '2025-09-10',
            'estimated_delivery': '2025-09-20'
        }
    ]

def create_print_order(color, pack_quantity):
    """Create new print order"""
    order_id = f'PO-{datetime.now().strftime("%Y%m%d")}-{color}'
    
    # Calculate cards per pack (15 cards, weighted by rarity)
    cards_per_pack = 15
    total_cards = pack_quantity * cards_per_pack
    
    # Estimate cost based on rarity distribution
    # Assume pack distribution: 10 common, 3 rare, 1 epic, 1 legendary
    pack_cost = (
        CARD_COSTS['common'] * 10 +
        CARD_COSTS['rare'] * 3 +
        CARD_COSTS['epic'] * 1 +
        CARD_COSTS['legendary'] * 1
    )
    
    total_cost = pack_cost * pack_quantity
    
    order = {
        'order_id': order_id,
        'order_number': f'PRINT-{datetime.now().strftime("%Y%m%d")}-{color}',
        'color': color,
        'pack_quantity': pack_quantity,
        'total_cards': total_cards,
        'estimated_cost': float(total_cost),
        'cost_per_pack': float(pack_cost),
        'estimated_delivery': (datetime.now() + timedelta(days=14)).date().isoformat(),
        'created_date': datetime.now().date().isoformat()
    }
    
    return order

def convert_url_to_path(image_url):
    """Convert image URL to file system path"""
    if not image_url:
        return None
    
    # Convert URL to file path
    if image_url.startswith('/static/'):
        return f'/home/jp/deckport.ai{image_url}'
    elif image_url.startswith('http'):
        # Extract path from full URL
        from urllib.parse import urlparse
        parsed = urlparse(image_url)
        return f'/home/jp/deckport.ai{parsed.path}'
    
    return None
