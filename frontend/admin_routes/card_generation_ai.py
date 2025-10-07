import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
AI-Powered Card Generation Admin Interface
Generates balanced cards using AI analysis of existing cards
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
# Use same admin auth as working routes
def require_admin_auth(f):
    from functools import wraps
    from flask import request, redirect, url_for
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function
from services.api_service import APIService
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

card_gen_bp = Blueprint('card_generation', __name__, url_prefix='/admin/cards')

@card_gen_bp.route('/generate', methods=['GET', 'POST'])
@require_admin_auth
def generate_card():
    """AI-powered card generation with balance analysis"""
    
    if request.method == 'GET':
        # Show the generation form
        with SessionLocal() as session:
            card_sets = session.query(CardSet).filter(CardSet.is_active == True).all()
            
        return render_template('admin/cards/generate_ai.html', card_sets=card_sets)
    
    # POST: Generate new card
    try:
        data = request.get_json() if request.is_json else request.form
        
        card_set_id = int(data.get('card_set_id'))
        rarity = data.get('rarity')
        category = data.get('category') 
        color_code = data.get('color_code')
        generation_prompt = data.get('generation_prompt', '')
        
        # Generate balanced card using AI
        generated_card = generate_balanced_card_ai(
            card_set_id=card_set_id,
            rarity=rarity,
            category=category,
            color_code=color_code,
            user_prompt=generation_prompt
        )
        
        if request.is_json:
            return jsonify({
                'success': True,
                'card': generated_card,
                'message': 'Card generated successfully! Review before adding to set.'
            })
        else:
            flash('Card generated successfully! Review the stats and abilities.', 'success')
            return render_template('admin/cards/review_generated.html', 
                                 card=generated_card)
            
    except Exception as e:
        logger.error(f"Error generating card: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            flash(f'Error generating card: {e}', 'error')
            return redirect(url_for('card_generation.generate_card'))

@card_gen_bp.route('/analyze-balance', methods=['POST'])
@require_admin_auth
def analyze_balance():
    """Analyze balance of cards in a set/color"""
    
    try:
        data = request.get_json()
        card_set_id = int(data.get('card_set_id'))
        color_code = data.get('color_code')
        rarity = data.get('rarity')
        
        balance_analysis = analyze_card_balance(card_set_id, color_code, rarity)
        
        return jsonify({
            'success': True,
            'analysis': balance_analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing balance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@card_gen_bp.route('/save-generated', methods=['POST'])
@require_admin_auth
def save_generated_card():
    """Save a generated card as a template"""
    
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            # Create new card template
            template = CardTemplate(
                card_set_id=data['card_set_id'],
                name=data['name'],
                slug=data['name'].lower().replace(' ', '-'),
                description=data.get('description', ''),
                flavor_text=data.get('flavor_text', ''),
                rarity=data['rarity'],
                category=data['category'],
                color_code=data.get('color_code'),
                base_stats=data.get('base_stats', {}),
                attachment_rules=data.get('attachment_rules'),
                duration=data.get('duration'),
                token_spec=data.get('token_spec'),
                reveal_trigger=data.get('reveal_trigger'),
                display_label=data.get('display_label'),
                product_sku=generate_product_sku(data['card_set_id'], data['color_code']),
                art_prompt=data.get('art_prompt', ''),
                art_style=data.get('art_style', 'painterly'),
                is_ready_for_production=False,  # Needs review
                is_published=False,
                balance_weight=data.get('balance_weight', 50),
                generation_prompt=data.get('generation_context', ''),
                last_balance_check=datetime.now(timezone.utc)
            )
            
            session.add(template)
            session.commit()
            
            logger.info(f"Created new card template: {template.name} ({template.product_sku})")
            
            return jsonify({
                'success': True,
                'template_id': template.id,
                'product_sku': template.product_sku,
                'message': f'Card "{template.name}" saved as template!'
            })
            
    except Exception as e:
        logger.error(f"Error saving generated card: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_balanced_card_ai(card_set_id, rarity, category, color_code, user_prompt=""):
    """
    Generate a balanced card using AI analysis of existing cards
    """
    
    with SessionLocal() as session:
        # Get existing cards for balance analysis
        existing_cards = session.query(CardTemplate).filter(
            CardTemplate.card_set_id == card_set_id,
            CardTemplate.color_code == color_code,
            CardTemplate.is_published == True
        ).all()
        
        # Analyze balance
        balance_context = calculate_balance_context(existing_cards, rarity, category)
        
        # Generate AI prompt
        ai_prompt = build_generation_prompt(
            rarity=rarity,
            category=category, 
            color_code=color_code,
            balance_context=balance_context,
            user_prompt=user_prompt,
            existing_cards=existing_cards
        )
        
        # For now, return a mock generated card
        # In production, this would call your AI service
        generated_card = generate_mock_card(rarity, category, color_code, balance_context)
        
        return generated_card

def calculate_balance_context(existing_cards, target_rarity, target_category):
    """Calculate balance metrics for AI generation"""
    
    # Filter cards by rarity and category
    similar_cards = [
        card for card in existing_cards 
        if card.rarity == target_rarity and card.category == target_category
    ]
    
    if not similar_cards:
        # Use default values if no similar cards exist
        return get_default_balance_values(target_rarity, target_category)
    
    # Calculate averages
    stats_list = [card.base_stats or {} for card in similar_cards]
    
    avg_stats = {}
    for stat in ['attack', 'health', 'defense', 'energy_cost', 'mana_cost']:
        values = [stats.get(stat, 0) for stats in stats_list if isinstance(stats.get(stat), (int, float))]
        if values:
            avg_stats[f'avg_{stat}'] = sum(values) / len(values)
    
    return {
        'similar_card_count': len(similar_cards),
        'avg_stats': avg_stats,
        'stat_ranges': calculate_stat_ranges(stats_list),
        'mana_curve_gaps': identify_mana_gaps(existing_cards),
        'balance_recommendation': 'balanced'  # Could be 'underpowered', 'balanced', 'overpowered'
    }

def build_generation_prompt(rarity, category, color_code, balance_context, user_prompt, existing_cards):
    """Build the AI prompt for card generation"""
    
    existing_names = [card.name for card in existing_cards[-5:]]  # Last 5 cards for context
    
    prompt = f"""
Generate a {rarity} {category} card for the {color_code} color.

BALANCE REQUIREMENTS:
- Similar cards average: {balance_context.get('avg_stats', {})}
- Recommended stat ranges: {balance_context.get('stat_ranges', {})}
- Mana curve needs: {balance_context.get('mana_curve_gaps', [])}

EXISTING CARDS FOR REFERENCE:
{', '.join(existing_names)}

USER REQUEST:
{user_prompt}

REQUIREMENTS:
1. Create balanced stats that fit the power level
2. Include unique but not overpowered abilities
3. Provide flavor text that fits the {color_code} theme
4. Suggest art prompt for image generation
5. Return as JSON with all required fields

RESPONSE FORMAT:
{{
    "name": "Card Name",
    "description": "Card ability text",
    "flavor_text": "Flavor text",
    "base_stats": {{"attack": 3, "health": 5, "energy_cost": 2}},
    "art_prompt": "Art description for AI generation",
    "balance_weight": 50,
    "display_label": "{rarity.title()} {category.title()}"
}}
"""
    
    return prompt

def generate_mock_card(rarity, category, color_code, balance_context):
    """Generate a mock card for testing (replace with real AI call)"""
    
    # Mock card generation based on balance context
    base_stats = {}
    
    if category == 'creature':
        base_stats = {
            'attack': int(balance_context.get('avg_stats', {}).get('avg_attack', 3)),
            'health': int(balance_context.get('avg_stats', {}).get('avg_health', 4)),
            'defense': int(balance_context.get('avg_stats', {}).get('avg_defense', 2)),
            'energy_cost': int(balance_context.get('avg_stats', {}).get('avg_energy_cost', 0))
        }
    elif category in ['action_fast', 'action_slow']:
        base_stats = {
            'damage': int(balance_context.get('avg_stats', {}).get('avg_attack', 3)),
            'energy_cost': int(balance_context.get('avg_stats', {}).get('avg_energy_cost', 2))
        }
    
    return {
        'name': f'Generated {color_code} {category.title()}',
        'description': f'A balanced {rarity} {category} with carefully tuned stats.',
        'flavor_text': f'The power of {color_code.lower()} flows through this {category}.',
        'rarity': rarity,
        'category': category,
        'color_code': color_code,
        'base_stats': base_stats,
        'art_prompt': f'A {rarity} {color_code.lower()} {category}, fantasy art style',
        'art_style': 'painterly',
        'balance_weight': 50,
        'display_label': f'{rarity.title()} {category.title()}',
        'generation_context': f'Generated with balance analysis of {balance_context.get("similar_card_count", 0)} similar cards'
    }

def get_default_balance_values(rarity, category):
    """Default balance values when no similar cards exist"""
    
    defaults = {
        'common': {'creature': {'attack': 2, 'health': 3, 'energy_cost': 0}},
        'rare': {'creature': {'attack': 3, 'health': 4, 'energy_cost': 0}},
        'epic': {'creature': {'attack': 4, 'health': 6, 'energy_cost': 0}},
        'legendary': {'creature': {'attack': 5, 'health': 8, 'energy_cost': 0}}
    }
    
    return {
        'similar_card_count': 0,
        'avg_stats': defaults.get(rarity, {}).get(category, {}),
        'stat_ranges': {},
        'mana_curve_gaps': [],
        'balance_recommendation': 'use_defaults'
    }

def calculate_stat_ranges(stats_list):
    """Calculate min/max ranges for each stat"""
    ranges = {}
    
    for stat in ['attack', 'health', 'defense', 'energy_cost']:
        values = [stats.get(stat, 0) for stats in stats_list if isinstance(stats.get(stat), (int, float))]
        if values:
            ranges[stat] = {'min': min(values), 'max': max(values)}
    
    return ranges

def identify_mana_gaps(existing_cards):
    """Identify gaps in the mana curve"""
    # Simplified implementation
    mana_costs = []
    for card in existing_cards:
        if card.base_stats and 'energy_cost' in card.base_stats:
            mana_costs.append(card.base_stats['energy_cost'])
    
    if not mana_costs:
        return [1, 2, 3]  # Default gaps
    
    # Find missing costs in range 0-6
    all_costs = set(range(0, 7))
    existing_costs = set(mana_costs)
    gaps = list(all_costs - existing_costs)
    
    return gaps[:3]  # Return top 3 gaps

def generate_product_sku(card_set_id, color_code):
    """Generate a unique product SKU"""
    with SessionLocal() as session:
        card_set = session.query(CardSet).get(card_set_id)
        set_code = card_set.code if card_set else 'UNK'
        
        # Find next number for this color in this set
        existing_skus = session.query(CardTemplate.product_sku).filter(
            CardTemplate.card_set_id == card_set_id,
            CardTemplate.product_sku.like(f'{color_code}-%')
        ).all()
        
        numbers = []
        for (sku,) in existing_skus:
            try:
                number = int(sku.split('-')[-1])
                numbers.append(number)
            except:
                continue
        
        next_number = max(numbers) + 1 if numbers else 1
        
        return f'{color_code}-{next_number:03d}'
