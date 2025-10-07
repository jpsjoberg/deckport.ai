"""
Game Abilities API Routes
Provides endpoints for card abilities and arena effects
"""

from flask import Blueprint, request, jsonify, g
from typing import Optional, Dict, Any
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Match, MatchParticipant, Player
from shared.auth.decorators import admin_required
from shared.utils.logging import setup_logging
from game_engine.card_abilities import CardAbilitiesEngine
from game_engine.arena_effects import ArenaEffectsEngine
from game_engine.match_manager import MatchManager

logger = setup_logging("game_abilities_api", "INFO")

abilities_bp = Blueprint('game_abilities', __name__, url_prefix='/v1/abilities')

# Initialize engines
abilities_engine = CardAbilitiesEngine()
arena_engine = ArenaEffectsEngine()

@abilities_bp.route('/catalog', methods=['GET'])
def get_abilities_catalog():
    """Get complete catalog of all available abilities"""
    try:
        abilities = abilities_engine.get_all_abilities()
        catalog = {}
        
        for ability_name in abilities:
            ability_info = abilities_engine.get_ability_info(ability_name)
            if ability_info:
                catalog[ability_name] = ability_info
        
        return jsonify({
            "success": True,
            "abilities": catalog,
            "total_count": len(abilities)
        })
        
    except Exception as e:
        logger.error(f"Error getting abilities catalog: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve abilities catalog"
        }), 500

@abilities_bp.route('/validate', methods=['POST'])
def validate_ability():
    """Validate ability parameters"""
    try:
        data = request.get_json()
        ability_name = data.get('ability_name')
        parameters = data.get('parameters', {})
        
        if not ability_name:
            return jsonify({
                "success": False,
                "error": "Ability name required"
            }), 400
        
        is_valid, error_message = abilities_engine.validate_ability_parameters(ability_name, parameters)
        
        return jsonify({
            "success": True,
            "valid": is_valid,
            "error_message": error_message if not is_valid else None,
            "ability_info": abilities_engine.get_ability_info(ability_name)
        })
        
    except Exception as e:
        logger.error(f"Error validating ability: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to validate ability"
        }), 500

@abilities_bp.route('/execute', methods=['POST'])
@admin_required
def execute_ability():
    """Execute an ability (admin/testing only)"""
    try:
        data = request.get_json()
        ability_name = data.get('ability_name')
        parameters = data.get('parameters', {})
        caster = data.get('caster', {})
        target_id = data.get('target_id')
        
        if not ability_name:
            return jsonify({
                "success": False,
                "error": "Ability name required"
            }), 400
        
        # This would need a mock game state for testing
        # In production, abilities are executed through match manager
        mock_game_state = type('MockGameState', (), {
            'players': {'0': type('Player', (), {'health': 20, 'mana': {}, 'battlefield': []})()},
            'arena': type('Arena', (), {'color': 'AETHER'})()
        })()
        
        result = abilities_engine.execute_ability(
            ability_name, parameters, caster, mock_game_state, target_id
        )
        
        return jsonify({
            "success": True,
            "result": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error executing ability: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@abilities_bp.route('/arenas', methods=['GET'])
def get_arenas():
    """Get all available arenas"""
    try:
        arenas = arena_engine.get_available_arenas()
        
        return jsonify({
            "success": True,
            "arenas": arenas,
            "total_count": len(arenas)
        })
        
    except Exception as e:
        logger.error(f"Error getting arenas: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve arenas"
        }), 500

@abilities_bp.route('/arenas/<arena_name>', methods=['GET'])
def get_arena_info(arena_name: str):
    """Get detailed information about a specific arena"""
    try:
        arena_info = arena_engine.get_arena_info(arena_name)
        
        if not arena_info:
            return jsonify({
                "success": False,
                "error": "Arena not found"
            }), 404
        
        return jsonify({
            "success": True,
            "arena": arena_info
        })
        
    except Exception as e:
        logger.error(f"Error getting arena info: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve arena information"
        }), 500

@abilities_bp.route('/arenas/<arena_name>/bonuses', methods=['POST'])
def calculate_hero_bonuses(arena_name: str):
    """Calculate hero bonuses for a specific arena"""
    try:
        data = request.get_json()
        hero_mana_affinity = data.get('hero_mana_affinity', 'AETHER')
        
        if not arena_engine.validate_arena(arena_name):
            return jsonify({
                "success": False,
                "error": "Invalid arena name"
            }), 400
        
        bonuses = arena_engine.calculate_hero_bonuses(arena_name, hero_mana_affinity)
        
        return jsonify({
            "success": True,
            "arena_name": arena_name,
            "hero_affinity": hero_mana_affinity,
            "bonuses": bonuses
        })
        
    except Exception as e:
        logger.error(f"Error calculating hero bonuses: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to calculate hero bonuses"
        }), 500

@abilities_bp.route('/arenas/select-balanced', methods=['POST'])
def select_balanced_arena():
    """Select a balanced arena for two heroes"""
    try:
        data = request.get_json()
        player1_hero = data.get('player1_hero', {})
        player2_hero = data.get('player2_hero', {})
        
        if not player1_hero or not player2_hero:
            return jsonify({
                "success": False,
                "error": "Both player heroes required"
            }), 400
        
        selected_arena = arena_engine.select_balanced_arena(player1_hero, player2_hero)
        arena_info = arena_engine.get_arena_info(selected_arena)
        
        return jsonify({
            "success": True,
            "selected_arena": selected_arena,
            "arena_info": arena_info,
            "player1_bonuses": arena_engine.calculate_hero_bonuses(
                selected_arena, player1_hero.get('mana_affinity', 'AETHER')
            ),
            "player2_bonuses": arena_engine.calculate_hero_bonuses(
                selected_arena, player2_hero.get('mana_affinity', 'AETHER')
            )
        })
        
    except Exception as e:
        logger.error(f"Error selecting balanced arena: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to select balanced arena"
        }), 500

@abilities_bp.route('/match/<int:match_id>/abilities', methods=['GET'])
def get_match_abilities_status(match_id: int):
    """Get status of abilities and effects in an active match"""
    try:
        # This would integrate with the match manager to get real match state
        # For now, return placeholder data
        
        with SessionLocal() as session:
            match = session.query(Match).filter(Match.id == match_id).first()
            if not match:
                return jsonify({
                    "success": False,
                    "error": "Match not found"
                }), 404
            
            # In a full implementation, this would get the actual game state
            # from the match manager and return active effects, cooldowns, etc.
            
            return jsonify({
                "success": True,
                "match_id": match_id,
                "active_effects": [],  # Would be populated from game state
                "available_abilities": [],  # Would be based on cards in play
                "arena_effects": {},  # Current arena bonuses/penalties
                "turn_number": 1,  # From game state
                "current_phase": "main"  # From game state
            })
            
    except Exception as e:
        logger.error(f"Error getting match abilities status: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve match abilities status"
        }), 500

@abilities_bp.route('/effects/status', methods=['GET'])
def get_status_effects_info():
    """Get information about all status effects"""
    try:
        # Return information about status effects that can be applied
        status_effects = {
            "burn": {
                "name": "Burn",
                "description": "Deal fire damage at start of each turn",
                "type": "damage_over_time",
                "damage_type": "fire"
            },
            "freeze": {
                "name": "Freeze",
                "description": "Cannot act for specified turns",
                "type": "disable",
                "prevents_actions": True
            },
            "poison": {
                "name": "Poison",
                "description": "Deal damage at start of each turn",
                "type": "damage_over_time",
                "damage_type": "physical"
            },
            "stun": {
                "name": "Stun",
                "description": "Skip next turn",
                "type": "disable",
                "prevents_actions": True
            },
            "regeneration": {
                "name": "Regeneration",
                "description": "Heal at start of each turn",
                "type": "healing_over_time"
            },
            "attack_buff": {
                "name": "Attack Buff",
                "description": "Increased attack power",
                "type": "stat_modifier",
                "stat": "attack"
            },
            "defense_buff": {
                "name": "Defense Buff",
                "description": "Increased defense",
                "type": "stat_modifier",
                "stat": "defense"
            },
            "attack_debuff": {
                "name": "Attack Debuff",
                "description": "Decreased attack power",
                "type": "stat_modifier",
                "stat": "attack"
            },
            "defense_debuff": {
                "name": "Defense Debuff",
                "description": "Decreased defense",
                "type": "stat_modifier",
                "stat": "defense"
            },
            "reflect_damage": {
                "name": "Reflect Damage",
                "description": "Return percentage of damage to attacker",
                "type": "reactive"
            },
            "immunity": {
                "name": "Immunity",
                "description": "Immune to specific damage type",
                "type": "protection"
            }
        }
        
        return jsonify({
            "success": True,
            "status_effects": status_effects,
            "total_count": len(status_effects)
        })
        
    except Exception as e:
        logger.error(f"Error getting status effects info: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve status effects information"
        }), 500

# Health check endpoint
@abilities_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for abilities system"""
    try:
        # Test that engines are working
        abilities_count = len(abilities_engine.get_all_abilities())
        arenas_count = len(arena_engine.get_available_arenas())
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "abilities_loaded": abilities_count,
            "arenas_loaded": arenas_count,
            "engines_initialized": True
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500
