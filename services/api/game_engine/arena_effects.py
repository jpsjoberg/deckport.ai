"""
Arena Effects System
Implements arena-based mana generation, hero bonuses, and special rules
Production-ready with full integration to game state
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.utils.logging import setup_logging

logger = setup_logging("arena_effects", "INFO")

class ManaColor(str, Enum):
    CRIMSON = "CRIMSON"
    AZURE = "AZURE"
    VERDANT = "VERDANT"
    GOLDEN = "GOLDEN"
    SHADOW = "SHADOW"
    AETHER = "AETHER"

class ArenaEffectsEngine:
    """Production-ready arena effects system"""
    
    def __init__(self):
        self.arena_catalog = self._load_arena_catalog()
        self.color_oppositions = {
            ManaColor.CRIMSON: ManaColor.AZURE,
            ManaColor.AZURE: ManaColor.CRIMSON,
            ManaColor.VERDANT: ManaColor.SHADOW,
            ManaColor.SHADOW: ManaColor.VERDANT,
            ManaColor.GOLDEN: ManaColor.SHADOW,
            ManaColor.AETHER: None
        }
    
    def _load_arena_catalog(self) -> Dict:
        """Load all arena definitions"""
        return {
            "crimson_forge": {
                "id": 1,
                "name": "Crimson Forge",
                "mana_color": ManaColor.CRIMSON,
                "mana_generation": 2,
                "background_video": "crimson_forge_ambient.mp4",
                "passive_effects": {
                    "fire_damage_bonus": 1,
                    "water_spell_penalty": 1
                },
                "hero_bonuses": {
                    ManaColor.CRIMSON: {
                        "attack": 2,
                        "defense": 0,
                        "abilities": ["fire_immunity"],
                        "special_rules": ["forge_hammer"]
                    },
                    ManaColor.AZURE: {
                        "attack": -1,
                        "defense": -1,
                        "penalties": ["water_spells_cost_extra"]
                    }
                },
                "special_rules": {
                    "forge_hammer": {
                        "name": "Forge Hammer",
                        "description": "Once per turn, CRIMSON heroes can deal 1 damage to any target",
                        "trigger": "once_per_turn",
                        "effect": "deal_damage",
                        "amount": 1,
                        "restriction": "crimson_heroes_only"
                    }
                },
                "objectives": [
                    {
                        "id": "forge_master",
                        "name": "Forge Master",
                        "type": "fire_damage_dealt",
                        "target": 15,
                        "description": "Deal 15 fire damage to win instantly",
                        "reward": "instant_victory"
                    }
                ],
                "story_text": "Ancient forges burn eternal, empowering fire magic while suppressing water.",
                "clips": {
                    "intro": "crimson_forge_intro.mp4",
                    "advantage": "crimson_forge_advantage.mp4",
                    "hazard": "crimson_forge_hazard.mp4"
                }
            },
            "azure_depths": {
                "id": 2,
                "name": "Azure Depths",
                "mana_color": ManaColor.AZURE,
                "mana_generation": 2,
                "background_video": "azure_depths_ambient.mp4",
                "passive_effects": {
                    "water_mastery": -1,
                    "fire_suppression": -1
                },
                "hero_bonuses": {
                    ManaColor.AZURE: {
                        "attack": 0,
                        "defense": 2,
                        "abilities": ["spell_cost_reduction"],
                        "special_rules": ["tidal_mastery"]
                    },
                    ManaColor.CRIMSON: {
                        "attack": -1,
                        "defense": -1,
                        "penalties": ["fire_spells_cost_extra"]
                    }
                },
                "special_rules": {
                    "tidal_wave": {
                        "name": "Tidal Wave",
                        "description": "Every 3rd turn, all creatures take 1 water damage",
                        "trigger": "every_3_turns",
                        "effect": "area_water_damage",
                        "amount": 1,
                        "target": "all_creatures"
                    }
                },
                "objectives": [
                    {
                        "id": "tide_master",
                        "name": "Tide Master",
                        "type": "creatures_frozen",
                        "target": 5,
                        "description": "Freeze 5 creatures to gain control of the tides",
                        "reward": "extra_mana_generation"
                    }
                ],
                "story_text": "Deep ocean currents enhance water magic while extinguishing flames.",
                "clips": {
                    "intro": "azure_depths_intro.mp4",
                    "advantage": "azure_depths_advantage.mp4",
                    "hazard": "azure_depths_tidal_wave.mp4"
                }
            },
            "verdant_grove": {
                "id": 3,
                "name": "Verdant Grove",
                "mana_color": ManaColor.VERDANT,
                "mana_generation": 2,
                "background_video": "verdant_grove_ambient.mp4",
                "passive_effects": {
                    "nature_growth": 1,
                    "shadow_weakness": 1
                },
                "hero_bonuses": {
                    ManaColor.VERDANT: {
                        "attack": 1,
                        "defense": 1,
                        "abilities": ["regeneration"],
                        "special_rules": ["life_bloom"]
                    },
                    ManaColor.SHADOW: {
                        "attack": -1,
                        "defense": -1,
                        "penalties": ["dark_spells_weakened"]
                    }
                },
                "special_rules": {
                    "life_bloom": {
                        "name": "Life Bloom",
                        "description": "At turn start, all VERDANT creatures heal 1 HP",
                        "trigger": "turn_start",
                        "effect": "heal_verdant_creatures",
                        "amount": 1,
                        "target": "verdant_creatures"
                    }
                },
                "objectives": [
                    {
                        "id": "nature_guardian",
                        "name": "Nature Guardian",
                        "type": "healing_done",
                        "target": 20,
                        "description": "Heal 20 total damage to unlock nature's blessing",
                        "reward": "all_creatures_regeneration"
                    }
                ],
                "story_text": "Living trees pulse with natural energy, nurturing growth while banishing darkness.",
                "clips": {
                    "intro": "verdant_grove_intro.mp4",
                    "advantage": "verdant_grove_bloom.mp4",
                    "hazard": "verdant_grove_thorns.mp4"
                }
            },
            "golden_sanctum": {
                "id": 4,
                "name": "Golden Sanctum",
                "mana_color": ManaColor.GOLDEN,
                "mana_generation": 2,
                "background_video": "golden_sanctum_ambient.mp4",
                "passive_effects": {
                    "divine_blessing": 1,
                    "shadow_banishment": 1
                },
                "hero_bonuses": {
                    ManaColor.GOLDEN: {
                        "attack": 1,
                        "defense": 1,
                        "abilities": ["divine_protection"],
                        "special_rules": ["sanctified_ground"]
                    },
                    ManaColor.SHADOW: {
                        "attack": -2,
                        "defense": -1,
                        "penalties": ["shadow_spells_weakened"]
                    }
                },
                "special_rules": {
                    "divine_intervention": {
                        "name": "Divine Intervention",
                        "description": "When a GOLDEN hero would die, heal to 1 HP instead (once per match)",
                        "trigger": "on_death",
                        "effect": "prevent_death",
                        "amount": 1,
                        "restriction": "once_per_match"
                    }
                },
                "story_text": "Sacred light empowers the righteous while banishing shadow.",
                "clips": {
                    "intro": "golden_sanctum_intro.mp4",
                    "advantage": "golden_sanctum_blessing.mp4"
                }
            },
            "shadow_nexus": {
                "id": 5,
                "name": "Shadow Nexus",
                "mana_color": ManaColor.SHADOW,
                "mana_generation": 2,
                "background_video": "shadow_nexus_ambient.mp4",
                "passive_effects": {
                    "dark_empowerment": 1,
                    "light_suppression": 1
                },
                "hero_bonuses": {
                    ManaColor.SHADOW: {
                        "attack": 2,
                        "defense": 0,
                        "abilities": ["shadow_step"],
                        "special_rules": ["void_drain"]
                    },
                    ManaColor.GOLDEN: {
                        "attack": -1,
                        "defense": -2,
                        "penalties": ["light_spells_cost_extra"]
                    }
                },
                "special_rules": {
                    "void_drain": {
                        "name": "Void Drain",
                        "description": "When an enemy creature dies, SHADOW heroes gain 1 energy",
                        "trigger": "on_enemy_death",
                        "effect": "gain_energy",
                        "amount": 1,
                        "target": "shadow_heroes"
                    }
                },
                "story_text": "Darkness consumes light, empowering shadow magic while weakening divine power.",
                "clips": {
                    "intro": "shadow_nexus_intro.mp4",
                    "advantage": "shadow_nexus_drain.mp4"
                }
            },
            "aether_void": {
                "id": 6,
                "name": "Aether Void",
                "mana_color": ManaColor.AETHER,
                "mana_generation": 3,  # More mana but colorless
                "background_video": "aether_void_ambient.mp4",
                "passive_effects": {
                    "neutral_ground": 0,
                    "mana_instability": 1
                },
                "hero_bonuses": {
                    # No color-specific bonuses - neutral arena
                },
                "special_rules": {
                    "mana_storm": {
                        "name": "Mana Storm",
                        "description": "Every 4 turns, all players gain 2 random colored mana",
                        "trigger": "every_4_turns",
                        "effect": "gain_random_mana",
                        "amount": 2,
                        "target": "all_players"
                    }
                },
                "story_text": "The void between realms offers neutral ground but unpredictable magic.",
                "clips": {
                    "intro": "aether_void_intro.mp4",
                    "advantage": "aether_void_storm.mp4"
                }
            }
        }
    
    def initialize_arena(self, arena_name: str, game_state: Any) -> Dict[str, Any]:
        """Initialize arena effects for a match"""
        if arena_name not in self.arena_catalog:
            logger.warning(f"Unknown arena: {arena_name}, using default")
            arena_name = "aether_void"
        
        arena_data = self.arena_catalog[arena_name]
        
        # Set arena in game state
        game_state.arena.name = arena_data["name"]
        game_state.arena.color = arena_data["mana_color"].value
        game_state.arena.passive_effect = arena_data.get("passive_effects", {})
        
        # Initialize arena-specific tracking
        arena_state = {
            "arena_name": arena_name,
            "turn_counter": 0,
            "special_rules_used": {},
            "objectives_progress": {},
            "mana_generation": arena_data["mana_generation"],
            "background_video": arena_data["background_video"]
        }
        
        # Apply initial hero bonuses
        self._apply_hero_bonuses(arena_data, game_state)
        
        logger.info(f"Initialized arena: {arena_data['name']} with {arena_data['mana_generation']} {arena_data['mana_color'].value} mana per turn")
        
        return arena_state
    
    def generate_turn_mana(self, arena_name: str, game_state: Any, player_team: int) -> Dict[str, int]:
        """Generate mana for a player's turn based on arena"""
        if arena_name not in self.arena_catalog:
            return {}
        
        arena_data = self.arena_catalog[arena_name]
        mana_color = arena_data["mana_color"]
        mana_amount = arena_data["mana_generation"]
        
        player_state = game_state.players.get(str(player_team))
        if not player_state:
            return {}
        
        # Apply hero bonuses to mana generation
        hero = player_state.hero
        if hero and hero.get("mana_affinity") == mana_color:
            # Matching hero gets bonus mana
            mana_amount += 1
        elif hero and self._is_opposing_color(hero.get("mana_affinity"), mana_color):
            # Opposing hero gets penalty
            mana_amount = max(1, mana_amount - 1)
        
        # Generate mana
        generated_mana = {mana_color.value: mana_amount}
        
        # Add to player's mana pool
        if mana_color.value not in player_state.mana:
            player_state.mana[mana_color.value] = 0
        player_state.mana[mana_color.value] += mana_amount
        
        logger.info(f"Generated {mana_amount} {mana_color.value} mana for player {player_team}")
        
        return generated_mana
    
    def apply_turn_start_effects(self, arena_name: str, game_state: Any, turn_number: int) -> List[Dict]:
        """Apply arena effects at the start of each turn"""
        if arena_name not in self.arena_catalog:
            return []
        
        arena_data = self.arena_catalog[arena_name]
        special_rules = arena_data.get("special_rules", {})
        effects_triggered = []
        
        for rule_name, rule_data in special_rules.items():
            trigger = rule_data.get("trigger")
            
            if trigger == "turn_start":
                effect = self._execute_special_rule(rule_name, rule_data, game_state)
                if effect:
                    effects_triggered.append(effect)
            
            elif trigger == "every_3_turns" and turn_number % 3 == 0:
                effect = self._execute_special_rule(rule_name, rule_data, game_state)
                if effect:
                    effects_triggered.append(effect)
            
            elif trigger == "every_4_turns" and turn_number % 4 == 0:
                effect = self._execute_special_rule(rule_name, rule_data, game_state)
                if effect:
                    effects_triggered.append(effect)
        
        return effects_triggered
    
    def calculate_hero_bonuses(self, arena_name: str, hero_mana_affinity: str) -> Dict[str, Any]:
        """Calculate bonuses/penalties for a hero based on arena"""
        if arena_name not in self.arena_catalog:
            return {}
        
        arena_data = self.arena_catalog[arena_name]
        hero_bonuses = arena_data.get("hero_bonuses", {})
        
        # Convert string to enum for comparison
        try:
            hero_color = ManaColor(hero_mana_affinity)
        except ValueError:
            return {}
        
        if hero_color in hero_bonuses:
            return hero_bonuses[hero_color]
        
        # Check for opposing color penalties
        arena_color = arena_data["mana_color"]
        if self._is_opposing_color(hero_color, arena_color):
            return {
                "attack": -1,
                "defense": -1,
                "penalties": ["opposing_arena_penalty"]
            }
        
        return {}
    
    def apply_damage_bonuses(self, arena_name: str, damage_amount: int, damage_type: str) -> int:
        """Apply arena-specific damage bonuses"""
        if arena_name not in self.arena_catalog:
            return damage_amount
        
        arena_data = self.arena_catalog[arena_name]
        passive_effects = arena_data.get("passive_effects", {})
        
        # Apply damage type bonuses
        if damage_type == "fire" and "fire_damage_bonus" in passive_effects:
            return damage_amount + passive_effects["fire_damage_bonus"]
        elif damage_type == "water" and "water_mastery" in passive_effects:
            return damage_amount + abs(passive_effects["water_mastery"])
        elif damage_type == "nature" and "nature_growth" in passive_effects:
            return damage_amount + passive_effects["nature_growth"]
        
        return damage_amount
    
    def apply_healing_bonuses(self, arena_name: str, healing_amount: int) -> int:
        """Apply arena-specific healing bonuses"""
        if arena_name not in self.arena_catalog:
            return healing_amount
        
        arena_data = self.arena_catalog[arena_name]
        
        # Verdant Grove enhances healing
        if arena_data["mana_color"] == ManaColor.VERDANT:
            return healing_amount + 1
        
        return healing_amount
    
    def check_arena_objectives(self, arena_name: str, game_state: Any, action_data: Dict) -> Optional[Dict]:
        """Check if any arena objectives are completed"""
        if arena_name not in self.arena_catalog:
            return None
        
        arena_data = self.arena_catalog[arena_name]
        objectives = arena_data.get("objectives", [])
        
        for objective in objectives:
            if self._check_objective_completion(objective, game_state, action_data):
                return {
                    "objective_id": objective["id"],
                    "name": objective["name"],
                    "description": objective["description"],
                    "reward": objective["reward"],
                    "completed_by": action_data.get("player_id")
                }
        
        return None
    
    def get_arena_background_video(self, arena_name: str) -> str:
        """Get the background video for an arena"""
        if arena_name not in self.arena_catalog:
            return "default_arena.mp4"
        
        return self.arena_catalog[arena_name].get("background_video", "default_arena.mp4")
    
    def get_arena_clip(self, arena_name: str, clip_type: str) -> str:
        """Get specific arena clip (intro, advantage, hazard, etc.)"""
        if arena_name not in self.arena_catalog:
            return ""
        
        clips = self.arena_catalog[arena_name].get("clips", {})
        return clips.get(clip_type, "")
    
    def get_available_arenas(self) -> List[Dict]:
        """Get list of all available arenas"""
        arenas = []
        for arena_name, arena_data in self.arena_catalog.items():
            arenas.append({
                "id": arena_data["id"],
                "name": arena_data["name"],
                "mana_color": arena_data["mana_color"].value,
                "story_text": arena_data.get("story_text", ""),
                "background_video": arena_data.get("background_video", "")
            })
        
        return arenas
    
    def select_balanced_arena(self, player1_hero: Dict, player2_hero: Dict) -> str:
        """Select a balanced arena based on hero affinities"""
        p1_affinity = player1_hero.get("mana_affinity", ManaColor.AETHER)
        p2_affinity = player2_hero.get("mana_affinity", ManaColor.AETHER)
        
        # If heroes have same affinity, use that arena
        if p1_affinity == p2_affinity:
            for arena_name, arena_data in self.arena_catalog.items():
                if arena_data["mana_color"].value == p1_affinity:
                    return arena_name
        
        # If heroes are opposing colors, use neutral arena
        if self._is_opposing_color(ManaColor(p1_affinity), ManaColor(p2_affinity)):
            return "aether_void"
        
        # Otherwise, select random arena that doesn't heavily favor either player
        neutral_arenas = ["aether_void"]
        return neutral_arenas[0]  # For now, always use neutral
    
    # === PRIVATE HELPER METHODS ===
    
    def _apply_hero_bonuses(self, arena_data: Dict, game_state: Any):
        """Apply initial hero bonuses based on arena"""
        hero_bonuses = arena_data.get("hero_bonuses", {})
        
        for player_state in game_state.players.values():
            hero = player_state.hero
            if not hero:
                continue
            
            hero_affinity = hero.get("mana_affinity")
            if not hero_affinity:
                continue
            
            try:
                hero_color = ManaColor(hero_affinity)
                if hero_color in hero_bonuses:
                    bonuses = hero_bonuses[hero_color]
                    
                    # Apply stat bonuses
                    hero["attack"] = hero.get("attack", 0) + bonuses.get("attack", 0)
                    hero["defense"] = hero.get("defense", 0) + bonuses.get("defense", 0)
                    
                    # Add special abilities
                    abilities = bonuses.get("abilities", [])
                    if "abilities" not in hero:
                        hero["abilities"] = []
                    hero["abilities"].extend(abilities)
                    
                    # Add special rules
                    special_rules = bonuses.get("special_rules", [])
                    if "special_rules" not in hero:
                        hero["special_rules"] = []
                    hero["special_rules"].extend(special_rules)
                    
                    logger.info(f"Applied arena bonuses to {hero_affinity} hero: +{bonuses.get('attack', 0)} attack, +{bonuses.get('defense', 0)} defense")
            
            except ValueError:
                continue
    
    def _execute_special_rule(self, rule_name: str, rule_data: Dict, game_state: Any) -> Optional[Dict]:
        """Execute a special arena rule"""
        effect_type = rule_data.get("effect")
        amount = rule_data.get("amount", 0)
        target = rule_data.get("target", "all")
        
        effect_result = {
            "rule_name": rule_name,
            "description": rule_data.get("description", ""),
            "effect_type": effect_type,
            "targets_affected": []
        }
        
        if effect_type == "area_water_damage":
            # Tidal Wave effect
            for player_state in game_state.players.values():
                for creature in player_state.battlefield:
                    creature["health"] = max(0, creature["health"] - amount)
                    effect_result["targets_affected"].append(creature.get("id", "unknown"))
        
        elif effect_type == "heal_verdant_creatures":
            # Life Bloom effect
            for player_state in game_state.players.values():
                for creature in player_state.battlefield:
                    if creature.get("mana_affinity") == ManaColor.VERDANT.value:
                        max_health = creature.get("max_health", 20)
                        creature["health"] = min(max_health, creature["health"] + amount)
                        effect_result["targets_affected"].append(creature.get("id", "unknown"))
        
        elif effect_type == "gain_random_mana":
            # Mana Storm effect
            import random
            colors = [color.value for color in ManaColor if color != ManaColor.AETHER]
            
            for player_state in game_state.players.values():
                for _ in range(amount):
                    random_color = random.choice(colors)
                    player_state.mana[random_color] = player_state.mana.get(random_color, 0) + 1
                    effect_result["targets_affected"].append(f"player_{player_state.team}")
        
        return effect_result if effect_result["targets_affected"] else None
    
    def _check_objective_completion(self, objective: Dict, game_state: Any, action_data: Dict) -> bool:
        """Check if an arena objective is completed"""
        objective_type = objective["type"]
        target_value = objective["target"]
        
        if objective_type == "fire_damage_dealt":
            # Track fire damage dealt this match
            total_fire_damage = action_data.get("fire_damage_total", 0)
            return total_fire_damage >= target_value
        
        elif objective_type == "creatures_frozen":
            # Track creatures frozen this match
            frozen_count = action_data.get("creatures_frozen_count", 0)
            return frozen_count >= target_value
        
        elif objective_type == "healing_done":
            # Track total healing done this match
            total_healing = action_data.get("healing_total", 0)
            return total_healing >= target_value
        
        return False
    
    def _is_opposing_color(self, color1: ManaColor, color2: ManaColor) -> bool:
        """Check if two mana colors are opposing"""
        return self.color_oppositions.get(color1) == color2
    
    def get_arena_info(self, arena_name: str) -> Optional[Dict]:
        """Get complete information about an arena"""
        return self.arena_catalog.get(arena_name)
    
    def validate_arena(self, arena_name: str) -> bool:
        """Validate that an arena exists"""
        return arena_name in self.arena_catalog
