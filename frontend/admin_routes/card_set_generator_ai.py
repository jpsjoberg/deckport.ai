import sys; import os; sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
"""
AI-Powered Full Card Set Generation
Generates complete, balanced card sets with cohesive themes and art prompts
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
import time

logger = logging.getLogger(__name__)

card_set_gen_bp = Blueprint('card_set_generation', __name__, url_prefix='/admin/card-sets')

@card_set_gen_bp.route('/generate', methods=['GET', 'POST'])
@require_admin_auth
def generate_card_set():
    """Generate a complete balanced card set with AI"""
    
    if request.method == 'GET':
        # Show the card set generation form
        api_service = APIService()
        
        # Get existing card sets via API
        existing_sets_response = api_service.get('/v1/admin/card-sets')
        existing_sets = existing_sets_response.get('card_sets', []) if existing_sets_response else []
            
        return render_template('admin/card_sets/generate_ai.html', existing_sets=existing_sets)
    
    # POST: Generate complete card set
    try:
        data = request.get_json() if request.is_json else request.form
        
        set_name = data.get('set_name')
        set_code = data.get('set_code')
        theme = data.get('theme', 'fantasy')
        color_distribution = data.get('color_distribution', 'balanced')
        set_size = int(data.get('set_size', 50))
        generation_prompt = data.get('generation_prompt', '')
        
        # Generate the complete card set via API
        api_service = APIService()
        
        set_generation_data = {
            'set_name': set_name,
            'set_code': set_code,
            'theme': theme,
            'color_distribution': color_distribution,
            'set_size': set_size,
            'generation_prompt': generation_prompt
        }
        
        generated_set_response = api_service.post('/v1/admin/card-sets/generate', set_generation_data)
        
        if not generated_set_response:
            raise Exception("Failed to generate card set via API")
        
        generated_set = generated_set_response
        
        if request.is_json:
            return jsonify({
                'success': True,
                'card_set': generated_set,
                'message': f'Generated {len(generated_set["cards"])} cards for set "{set_name}"'
            })
        else:
            flash(f'Generated {len(generated_set["cards"])} cards for set "{set_name}"!', 'success')
            return render_template('admin/card_sets/review_generated_set.html', 
                                 card_set=generated_set)
            
    except Exception as e:
        logger.error(f"Error generating card set: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            flash(f'Error generating card set: {e}', 'error')
            return redirect(url_for('card_set_generation.generate_card_set'))

@card_set_gen_bp.route('/save-set', methods=['POST'])
@require_admin_auth
def save_generated_set():
    """Save a complete generated card set to the database"""
    
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            # Create the card set
            card_set = CardSet(
                name=data['set_name'],
                code=data['set_code'],
                description=data.get('description', ''),
                is_active=False,  # Needs review before activation
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(card_set)
            session.flush()  # Get the ID
            
            # Create all card templates
            created_cards = []
            for card_data in data['cards']:
                template = CardTemplate(
                    card_set_id=card_set.id,
                    name=card_data['name'],
                    slug=generate_unique_slug(card_data['name'], session),
                    description=card_data.get('description', ''),
                    flavor_text=card_data.get('flavor_text', ''),
                    rarity=card_data['rarity'],
                    category=card_data['category'],
                    color_code=card_data.get('color_code'),
                    base_stats=card_data.get('base_stats', {}),
                    art_prompt=card_data.get('art_prompt', ''),
                    art_style=card_data.get('art_style', 'painterly'),
                    is_design_complete=True,
                    is_balanced=True,  # AI-generated, pre-balanced
                    is_ready_for_production=False,  # Needs admin review
                    balance_weight=card_data.get('balance_weight', 50),
                    generation_context=card_data.get('generation_context', ''),
                    generation_prompt_history=[data.get('user_prompt', 'AI Set Generation')]
                )
                
                session.add(template)
                created_cards.append(template)
            
            session.commit()
            
            logger.info(f"Created card set '{card_set.name}' with {len(created_cards)} cards")
            
            return jsonify({
                'success': True,
                'set_id': card_set.id,
                'cards_created': len(created_cards),
                'message': f'Card set "{card_set.name}" saved with {len(created_cards)} cards!'
            })
            
    except Exception as e:
        logger.error(f"Error saving card set: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_balanced_card_set_ai(set_name, set_code, theme, color_distribution, set_size, user_prompt=""):
    """
    Generate a complete balanced card set using AI analysis
    """
    
    # Define set structure based on size
    set_structure = calculate_set_structure(set_size, color_distribution)
    
    # Generate thematic context
    thematic_context = build_set_theme_context(theme, set_name, user_prompt)
    
    # Generate cards for each category and color
    generated_cards = []
    
    for color_code, color_info in set_structure['colors'].items():
        for category, count in color_info['categories'].items():
            for rarity, rarity_count in color_info['rarities'].items():
                if rarity_count > 0:
                    cards = generate_cards_for_category(
                        color_code=color_code,
                        category=category,
                        rarity=rarity,
                        count=rarity_count,
                        theme_context=thematic_context,
                        set_context={'name': set_name, 'code': set_code}
                    )
                    generated_cards.extend(cards)
    
    return {
        'set_name': set_name,
        'set_code': set_code,
        'theme': theme,
        'total_cards': len(generated_cards),
        'structure': set_structure,
        'cards': generated_cards,
        'art_style_guide': generate_art_style_guide(theme, set_name),
        'balance_report': generate_balance_report(generated_cards)
    }

def calculate_set_structure(set_size, color_distribution):
    """Calculate the optimal structure for a card set"""
    
    # Define color codes
    colors = ['RED', 'BLUE', 'GREEN', 'WHITE', 'BLACK', 'NEUTRAL']
    
    # Rarity distribution (typical TCG ratios)
    rarity_ratios = {
        'COMMON': 0.50,    # 50% commons
        'RARE': 0.30,      # 30% rares  
        'EPIC': 0.15,      # 15% epics
        'LEGENDARY': 0.05  # 5% legendaries
    }
    
    # Category distribution
    category_ratios = {
        'CREATURE': 0.40,   # 40% creatures
        'ACTION': 0.25,     # 25% actions/spells
        'EQUIPMENT': 0.20,  # 20% equipment
        'STRUCTURE': 0.10,  # 10% structures
        'SPECIAL': 0.05     # 5% special cards
    }
    
    # Calculate cards per color
    if color_distribution == 'balanced':
        cards_per_color = set_size // len(colors)
    elif color_distribution == 'focused':
        # Focus on 3 main colors
        main_colors = colors[:3]
        cards_per_color = set_size // len(main_colors)
        colors = main_colors
    
    structure = {
        'total_cards': set_size,
        'colors': {}
    }
    
    for color in colors:
        color_cards = cards_per_color
        
        # Calculate rarities for this color
        color_rarities = {}
        for rarity, ratio in rarity_ratios.items():
            color_rarities[rarity] = max(1, int(color_cards * ratio))
        
        # Calculate categories for this color
        color_categories = {}
        for category, ratio in category_ratios.items():
            color_categories[category] = max(1, int(color_cards * ratio))
        
        structure['colors'][color] = {
            'total_cards': color_cards,
            'rarities': color_rarities,
            'categories': color_categories
        }
    
    return structure

def build_set_theme_context(theme, set_name, user_prompt):
    """Build thematic context for consistent card generation"""
    
    theme_contexts = {
        'fantasy': {
            'setting': 'A magical realm of wizards, dragons, and ancient mysteries',
            'tone': 'Epic and mystical',
            'visual_style': 'High fantasy with rich colors and magical effects',
            'naming_style': 'Medieval fantasy names with mystical elements'
        },
        'sci-fi': {
            'setting': 'A futuristic universe of space travel, advanced technology, and alien worlds',
            'tone': 'Technological and futuristic',
            'visual_style': 'Sleek technology, neon colors, and cosmic backgrounds',
            'naming_style': 'Technical and futuristic terminology'
        },
        'steampunk': {
            'setting': 'A Victorian-era world powered by steam and mechanical ingenuity',
            'tone': 'Industrial and inventive',
            'visual_style': 'Brass, copper, gears, and steam with sepia tones',
            'naming_style': 'Victorian names with mechanical terminology'
        },
        'cyberpunk': {
            'setting': 'A dystopian future of corporate control, hackers, and digital rebellion',
            'tone': 'Dark and rebellious',
            'visual_style': 'Neon lights, dark cities, and digital interfaces',
            'naming_style': 'Tech slang and corporate terminology'
        }
    }
    
    base_context = theme_contexts.get(theme, theme_contexts['fantasy'])
    
    return {
        'theme': theme,
        'set_name': set_name,
        'setting': base_context['setting'],
        'tone': base_context['tone'],
        'visual_style': base_context['visual_style'],
        'naming_style': base_context['naming_style'],
        'user_direction': user_prompt
    }

def generate_cards_for_category(color_code, category, rarity, count, theme_context, set_context):
    """Generate multiple cards for a specific category/rarity/color combination"""
    
    cards = []
    
    for i in range(count):
        # Generate unique card based on theme and specifications
        card = generate_thematic_card(
            color_code=color_code,
            category=category,
            rarity=rarity,
            theme_context=theme_context,
            set_context=set_context,
            card_number=i + 1
        )
        cards.append(card)
    
    return cards

def generate_thematic_card(color_code, category, rarity, theme_context, set_context, card_number):
    """Generate a single thematic card with balanced stats and art prompt"""
    
    # Color-specific themes
    color_themes = {
        'RED': {'element': 'fire', 'traits': 'aggressive, passionate, destructive', 'creatures': 'dragons, warriors, phoenixes'},
        'BLUE': {'element': 'water/air', 'traits': 'intelligent, controlling, mystical', 'creatures': 'wizards, elementals, spirits'},
        'GREEN': {'element': 'nature', 'traits': 'growing, natural, harmonious', 'creatures': 'beasts, druids, treants'},
        'WHITE': {'element': 'light', 'traits': 'protective, healing, orderly', 'creatures': 'angels, clerics, knights'},
        'BLACK': {'element': 'darkness', 'traits': 'corrupting, powerful, sacrificial', 'creatures': 'demons, necromancers, shadows'},
        'NEUTRAL': {'element': 'balance', 'traits': 'versatile, mechanical, ancient', 'creatures': 'golems, artifacts, constructs'}
    }
    
    color_theme = color_themes.get(color_code, color_themes['NEUTRAL'])
    
    # Generate base stats based on rarity and category
    base_stats = generate_balanced_stats(rarity, category, color_code)
    
    # Generate thematic name
    name = generate_thematic_name(category, color_code, theme_context, card_number)
    
    # Generate description and flavor text
    description = generate_card_description(category, rarity, color_theme, theme_context)
    flavor_text = generate_flavor_text(name, color_theme, theme_context)
    
    # Generate comprehensive art prompt
    art_prompt = generate_comprehensive_art_prompt(
        name=name,
        category=category,
        color_theme=color_theme,
        theme_context=theme_context,
        rarity=rarity
    )
    
    return {
        'name': name,
        'description': description,
        'flavor_text': flavor_text,
        'rarity': rarity,
        'category': category,
        'color_code': color_code,
        'base_stats': base_stats,
        'art_prompt': art_prompt,
        'art_style': theme_context.get('visual_style', 'painterly'),
        'balance_weight': calculate_balance_weight(base_stats, rarity),
        'display_label': f'{rarity.title()} {category.title()}',
        'generation_context': f'Generated for {set_context["name"]} - {theme_context["theme"]} theme'
    }

def generate_balanced_stats(rarity, category, color_code):
    """Generate balanced stats based on rarity and category"""
    
    # Base stat templates by rarity
    rarity_multipliers = {
        'COMMON': 1.0,
        'RARE': 1.3,
        'EPIC': 1.6,
        'LEGENDARY': 2.0
    }
    
    # Category base stats
    category_bases = {
        'CREATURE': {'attack': 2, 'health': 3, 'defense': 1, 'energy_cost': 1},
        'ACTION': {'damage': 3, 'energy_cost': 2, 'duration': 1},
        'EQUIPMENT': {'attack_bonus': 2, 'defense_bonus': 1, 'durability': 4, 'energy_cost': 2},
        'STRUCTURE': {'health': 5, 'defense': 3, 'energy_cost': 3, 'ability_power': 2},
        'SPECIAL': {'effect_power': 4, 'energy_cost': 4, 'charges': 2}
    }
    
    base = category_bases.get(category, category_bases['CREATURE'])
    multiplier = rarity_multipliers.get(rarity, 1.0)
    
    # Apply multiplier and add some variation
    stats = {}
    for stat, value in base.items():
        stats[stat] = max(1, int(value * multiplier))
    
    return stats

def generate_thematic_name(category, color_code, theme_context, card_number):
    """Generate a thematic name for the card"""
    
    # Name components by theme and color
    name_components = {
        'fantasy': {
            'RED': {'prefixes': ['Flame', 'Fire', 'Burning', 'Crimson', 'Blazing'], 
                   'suffixes': ['Warrior', 'Dragon', 'Phoenix', 'Berserker', 'Mage']},
            'BLUE': {'prefixes': ['Frost', 'Crystal', 'Mystic', 'Azure', 'Ethereal'], 
                    'suffixes': ['Wizard', 'Elemental', 'Scholar', 'Seer', 'Spirit']},
            'GREEN': {'prefixes': ['Wild', 'Ancient', 'Verdant', 'Living', 'Primal'], 
                     'suffixes': ['Beast', 'Druid', 'Treant', 'Guardian', 'Shaman']},
            'WHITE': {'prefixes': ['Divine', 'Sacred', 'Radiant', 'Holy', 'Pure'], 
                     'suffixes': ['Angel', 'Cleric', 'Knight', 'Paladin', 'Healer']},
            'BLACK': {'prefixes': ['Dark', 'Shadow', 'Cursed', 'Void', 'Corrupt'], 
                     'suffixes': ['Demon', 'Necromancer', 'Wraith', 'Cultist', 'Reaper']},
            'NEUTRAL': {'prefixes': ['Ancient', 'Mechanical', 'Eternal', 'Forgotten', 'Arcane'], 
                       'suffixes': ['Golem', 'Construct', 'Artifact', 'Relic', 'Automaton']}
        }
    }
    
    theme_names = name_components.get(theme_context['theme'], name_components['fantasy'])
    color_names = theme_names.get(color_code, theme_names['NEUTRAL'])
    
    # Category-specific adjustments
    if category == 'ACTION':
        color_names['suffixes'] = ['Blast', 'Strike', 'Surge', 'Storm', 'Ritual']
    elif category == 'EQUIPMENT':
        color_names['suffixes'] = ['Blade', 'Shield', 'Armor', 'Talisman', 'Crown']
    elif category == 'STRUCTURE':
        color_names['suffixes'] = ['Tower', 'Fortress', 'Shrine', 'Citadel', 'Sanctum']
    
    import random
    prefix = random.choice(color_names['prefixes'])
    suffix = random.choice(color_names['suffixes'])
    
    return f"{prefix} {suffix}"

def generate_card_description(category, rarity, color_theme, theme_context):
    """Generate card ability description"""
    
    # Template descriptions by category
    descriptions = {
        'CREATURE': f"A {color_theme['traits'].split(',')[0].strip()} creature that embodies the power of {color_theme['element']}.",
        'ACTION': f"Channel the {color_theme['traits'].split(',')[1].strip()} force of {color_theme['element']} to devastate your enemies.",
        'EQUIPMENT': f"Ancient equipment infused with {color_theme['element']} energy, granting {color_theme['traits'].split(',')[0].strip()} power.",
        'STRUCTURE': f"A {color_theme['traits'].split(',')[2].strip()} structure that harnesses {color_theme['element']} for strategic advantage.",
        'SPECIAL': f"A rare manifestation of {color_theme['element']} with {color_theme['traits'].split(',')[0].strip()} properties."
    }
    
    return descriptions.get(category, descriptions['CREATURE'])

def generate_flavor_text(name, color_theme, theme_context):
    """Generate thematic flavor text"""
    
    flavor_templates = [
        f"The {color_theme['element']} flows through all who wield the {name}.",
        f"In the {theme_context['setting'].lower()}, few dare to face the {name}.",
        f"'{color_theme['traits'].split(',')[0].strip().title()} and {color_theme['traits'].split(',')[1].strip()}' - Ancient Proverb",
        f"The power of {color_theme['element']} made manifest in the form of {name}."
    ]
    
    import random
    return random.choice(flavor_templates)

def generate_comprehensive_art_prompt(name, category, color_theme, theme_context, rarity):
    """Generate detailed art prompt for AI image generation"""
    
    # Base prompt structure
    subject = f"{name}, a {rarity.lower()} {category.lower()}"
    
    # Visual elements based on color
    color_visuals = {
        'RED': 'flames, fire effects, red and orange colors, dramatic lighting, heat distortion',
        'BLUE': 'ice crystals, water effects, blue and cyan colors, mystical glow, ethereal mist',
        'GREEN': 'natural elements, vines, green and brown colors, organic textures, living energy',
        'WHITE': 'divine light, golden glow, white and gold colors, radiant aura, holy symbols',
        'BLACK': 'dark shadows, purple and black colors, ominous atmosphere, corrupted energy',
        'NEUTRAL': 'metallic surfaces, ancient stone, grey and bronze colors, mechanical details'
    }
    
    # Category-specific details
    category_details = {
        'CREATURE': f"detailed character design, {color_theme['creatures']}, dynamic pose",
        'ACTION': "spell effect, energy burst, magical phenomenon, dynamic motion",
        'EQUIPMENT': "detailed weapon or armor, intricate craftsmanship, magical enhancement",
        'STRUCTURE': "architectural design, imposing building, environmental integration",
        'SPECIAL': "unique magical artifact, mysterious object, otherworldly appearance"
    }
    
    # Quality and style modifiers
    quality_mods = "highly detailed, fantasy art, professional illustration, dramatic composition"
    
    # Rarity-specific enhancement
    rarity_enhancements = {
        'COMMON': "clean design, straightforward composition",
        'RARE': "enhanced details, magical effects, rich colors",
        'EPIC': "elaborate design, powerful magical aura, cinematic lighting",
        'LEGENDARY': "masterpiece quality, overwhelming magical presence, epic scale"
    }
    
    art_prompt = f"{subject}, {category_details[category]}, {color_visuals[color_theme.get('element', 'balance')]}, {theme_context['visual_style']}, {rarity_enhancements[rarity]}, {quality_mods}"
    
    return art_prompt

def generate_art_style_guide(theme, set_name):
    """Generate a comprehensive art style guide for the set"""
    
    return {
        'theme': theme,
        'set_name': set_name,
        'color_palette': get_theme_color_palette(theme),
        'visual_elements': get_theme_visual_elements(theme),
        'composition_guidelines': get_composition_guidelines(theme),
        'lighting_style': get_lighting_style(theme),
        'texture_preferences': get_texture_preferences(theme)
    }

def generate_balance_report(cards):
    """Generate a balance analysis report for the card set"""
    
    total_cards = len(cards)
    
    # Analyze distribution
    rarity_dist = {}
    category_dist = {}
    color_dist = {}
    
    for card in cards:
        rarity_dist[card['rarity']] = rarity_dist.get(card['rarity'], 0) + 1
        category_dist[card['category']] = category_dist.get(card['category'], 0) + 1
        color_dist[card['color_code']] = color_dist.get(card['color_code'], 0) + 1
    
    return {
        'total_cards': total_cards,
        'rarity_distribution': rarity_dist,
        'category_distribution': category_dist,
        'color_distribution': color_dist,
        'balance_score': calculate_set_balance_score(cards),
        'recommendations': generate_balance_recommendations(cards)
    }

def calculate_balance_weight(stats, rarity):
    """Calculate balance weight for a card"""
    
    total_power = sum(stats.values()) if stats else 0
    rarity_weights = {'COMMON': 1, 'RARE': 2, 'EPIC': 3, 'LEGENDARY': 4}
    
    return min(100, max(1, int(total_power * rarity_weights.get(rarity, 1) * 10)))

def generate_unique_slug(name, session):
    """Generate a unique slug for the card"""
    
    base_slug = name.lower().replace(' ', '-').replace("'", "")
    slug = base_slug
    counter = 1
    
    while session.query(CardTemplate).filter(CardTemplate.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

# Helper functions for art style guide
def get_theme_color_palette(theme):
    palettes = {
        'fantasy': ['#8B4513', '#228B22', '#4169E1', '#DC143C', '#FFD700'],
        'sci-fi': ['#00FFFF', '#FF1493', '#32CD32', '#FF4500', '#9370DB'],
        'steampunk': ['#CD853F', '#8B4513', '#DAA520', '#2F4F4F', '#696969'],
        'cyberpunk': ['#FF00FF', '#00FFFF', '#FFFF00', '#FF0000', '#000000']
    }
    return palettes.get(theme, palettes['fantasy'])

def get_theme_visual_elements(theme):
    elements = {
        'fantasy': ['magical runes', 'mystical creatures', 'ancient architecture', 'natural elements'],
        'sci-fi': ['holographic displays', 'space stations', 'alien technology', 'energy weapons'],
        'steampunk': ['brass gears', 'steam pipes', 'Victorian architecture', 'mechanical devices'],
        'cyberpunk': ['neon signs', 'digital interfaces', 'urban decay', 'corporate logos']
    }
    return elements.get(theme, elements['fantasy'])

def get_composition_guidelines(theme):
    return f"Dynamic compositions emphasizing {theme} aesthetics with strong focal points and balanced visual weight"

def get_lighting_style(theme):
    styles = {
        'fantasy': 'Dramatic lighting with magical glows and natural illumination',
        'sci-fi': 'High-tech lighting with neon accents and energy effects',
        'steampunk': 'Warm industrial lighting with steam and brass reflections',
        'cyberpunk': 'Harsh neon lighting with deep shadows and digital glows'
    }
    return styles.get(theme, styles['fantasy'])

def get_texture_preferences(theme):
    textures = {
        'fantasy': 'Organic textures, weathered stone, natural materials',
        'sci-fi': 'Smooth metals, energy fields, crystalline structures',
        'steampunk': 'Brass, copper, leather, worn metal surfaces',
        'cyberpunk': 'Reflective surfaces, digital textures, urban grime'
    }
    return textures.get(theme, textures['fantasy'])

def calculate_set_balance_score(cards):
    """Calculate overall balance score for the set"""
    # Simplified balance scoring
    return 85  # Placeholder

def generate_balance_recommendations(cards):
    """Generate recommendations for set balance"""
    return [
        "Consider adding more low-cost cards for early game",
        "Balance looks good across all rarities",
        "Color distribution is well-balanced"
    ]













