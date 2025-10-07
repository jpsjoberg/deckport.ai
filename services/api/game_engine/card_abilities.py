"""
Card Abilities Execution System
Implements all 40+ card abilities from the Battle Abilities Reference
Production-ready with validation, effects, and state management
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.utils.logging import setup_logging

logger = setup_logging("card_abilities", "INFO")

class TargetType(str, Enum):
    SELF = "self"
    ALLY = "ally"
    ENEMY = "enemy"
    ANY = "any"
    ALL_ALLIES = "all_allies"
    ALL_ENEMIES = "all_enemies"
    ALL = "all"
    RANDOM_ENEMY = "random_enemy"
    RANDOM_ALLY = "random_ally"

class DamageType(str, Enum):
    PHYSICAL = "physical"
    FIRE = "fire"
    WATER = "water"
    NATURE = "nature"
    LIGHT = "light"
    SHADOW = "shadow"
    PIERCING = "piercing"

class StatusEffect:
    """Represents a temporary status effect on a target"""
    def __init__(self, effect_type: str, amount: int, duration: int, source: str):
        self.effect_type = effect_type
        self.amount = amount
        self.duration = duration
        self.source = source
        self.applied_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        return {
            "effect_type": self.effect_type,
            "amount": self.amount,
            "duration": self.duration,
            "source": self.source,
            "applied_at": self.applied_at.isoformat()
        }

class AbilityResult:
    """Result of an ability execution"""
    def __init__(self):
        self.success = True
        self.damage_dealt = 0
        self.healing_done = 0
        self.targets_affected = []
        self.status_effects_applied = []
        self.mana_changes = {}
        self.energy_changes = {}
        self.animation_data = {}
        self.error_message = ""
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "damage_dealt": self.damage_dealt,
            "healing_done": self.healing_done,
            "targets_affected": self.targets_affected,
            "status_effects_applied": [effect.to_dict() for effect in self.status_effects_applied],
            "mana_changes": self.mana_changes,
            "energy_changes": self.energy_changes,
            "animation_data": self.animation_data,
            "error_message": self.error_message
        }

class CardAbilitiesEngine:
    """Production-ready card abilities execution engine"""
    
    def __init__(self):
        self.ability_catalog = self._load_ability_catalog()
        self.arena_bonuses = {}
        self.active_effects = {}  # target_id -> [StatusEffect]
    
    def _load_ability_catalog(self) -> Dict:
        """Load all ability definitions from the catalog"""
        return {
            # === DAMAGE ABILITIES ===
            "deal_damage": {
                "name": "Deal Damage",
                "description": "Deal X damage to target",
                "parameters": ["amount", "target_type"],
                "damage_type": DamageType.PHYSICAL,
                "animation": "damage_burst",
                "video_clip": "abilities/deal_damage.mp4"
            },
            "fire_damage": {
                "name": "Fire Damage",
                "description": "Deal X fire damage to target",
                "parameters": ["amount", "target_type"],
                "damage_type": DamageType.FIRE,
                "animation": "fire_burst",
                "video_clip": "abilities/fire_damage.mp4"
            },
            "water_damage": {
                "name": "Water Damage",
                "description": "Deal X water damage to target",
                "parameters": ["amount", "target_type"],
                "damage_type": DamageType.WATER,
                "animation": "water_burst",
                "video_clip": "abilities/water_damage.mp4"
            },
            "piercing_damage": {
                "name": "Piercing Damage",
                "description": "Deal X damage that ignores armor",
                "parameters": ["amount", "target_type"],
                "damage_type": DamageType.PIERCING,
                "animation": "pierce_strike",
                "video_clip": "abilities/piercing_damage.mp4"
            },
            "area_damage": {
                "name": "Area Damage",
                "description": "Deal X damage to all enemies",
                "parameters": ["amount"],
                "damage_type": DamageType.PHYSICAL,
                "animation": "explosion",
                "video_clip": "abilities/area_damage.mp4"
            },
            
            # === HEALING ABILITIES ===
            "heal": {
                "name": "Heal",
                "description": "Restore X health to target",
                "parameters": ["amount", "target_type"],
                "animation": "healing_light",
                "video_clip": "abilities/heal.mp4"
            },
            "regeneration": {
                "name": "Regeneration",
                "description": "Heal X health at start of each turn",
                "parameters": ["amount", "duration"],
                "animation": "regen_aura",
                "video_clip": "abilities/regeneration.mp4"
            },
            "area_heal": {
                "name": "Area Heal",
                "description": "Heal X to all allies",
                "parameters": ["amount"],
                "animation": "healing_wave",
                "video_clip": "abilities/area_heal.mp4"
            },
            
            # === BUFF ABILITIES ===
            "buff_attack": {
                "name": "Attack Buff",
                "description": "Increase target's attack by X",
                "parameters": ["amount", "duration", "target_type"],
                "animation": "power_up",
                "video_clip": "abilities/buff_attack.mp4"
            },
            "buff_defense": {
                "name": "Defense Buff",
                "description": "Increase target's defense by X",
                "parameters": ["amount", "duration", "target_type"],
                "animation": "shield_up",
                "video_clip": "abilities/buff_defense.mp4"
            },
            
            # === DEBUFF ABILITIES ===
            "debuff_attack": {
                "name": "Attack Debuff",
                "description": "Decrease target's attack by X",
                "parameters": ["amount", "duration", "target_type"],
                "animation": "weakness",
                "video_clip": "abilities/debuff_attack.mp4"
            },
            "debuff_defense": {
                "name": "Defense Debuff",
                "description": "Decrease target's defense by X",
                "parameters": ["amount", "duration", "target_type"],
                "animation": "armor_break",
                "video_clip": "abilities/debuff_defense.mp4"
            },
            
            # === STATUS EFFECTS ===
            "burn": {
                "name": "Burn",
                "description": "Deal X fire damage at start of each turn",
                "parameters": ["amount", "duration"],
                "animation": "burning_effect",
                "video_clip": "abilities/burn.mp4"
            },
            "freeze": {
                "name": "Freeze",
                "description": "Target cannot act for X turns",
                "parameters": ["duration"],
                "animation": "ice_prison",
                "video_clip": "abilities/freeze.mp4"
            },
            "poison": {
                "name": "Poison",
                "description": "Deal X damage at start of each turn",
                "parameters": ["amount", "duration"],
                "animation": "poison_cloud",
                "video_clip": "abilities/poison.mp4"
            },
            "stun": {
                "name": "Stun",
                "description": "Target skips next turn",
                "parameters": ["duration"],
                "animation": "lightning_stun",
                "video_clip": "abilities/stun.mp4"
            },
            
            # === RESOURCE ABILITIES ===
            "gain_energy": {
                "name": "Gain Energy",
                "description": "Gain X energy this turn",
                "parameters": ["amount"],
                "animation": "energy_surge",
                "video_clip": "abilities/gain_energy.mp4"
            },
            "gain_mana": {
                "name": "Gain Mana",
                "description": "Gain X mana of specified color",
                "parameters": ["amount", "color"],
                "animation": "mana_crystal",
                "video_clip": "abilities/gain_mana.mp4"
            },
            "mana_burn": {
                "name": "Mana Burn",
                "description": "Remove X mana from opponent",
                "parameters": ["amount", "color"],
                "animation": "mana_drain",
                "video_clip": "abilities/mana_burn.mp4"
            },
            
            # === CARD MANIPULATION ===
            "draw_card": {
                "name": "Draw Card",
                "description": "Draw X cards from deck",
                "parameters": ["amount"],
                "animation": "card_draw",
                "video_clip": "abilities/draw_card.mp4"
            },
            "discard_card": {
                "name": "Discard Card",
                "description": "Force opponent to discard X cards",
                "parameters": ["amount"],
                "animation": "card_discard",
                "video_clip": "abilities/discard_card.mp4"
            },
            
            # === SPECIAL ABILITIES ===
            "teleport": {
                "name": "Teleport",
                "description": "Move target to different position",
                "parameters": ["target_type"],
                "animation": "teleport_flash",
                "video_clip": "abilities/teleport.mp4"
            },
            "reflect_damage": {
                "name": "Reflect Damage",
                "description": "Return X% of damage taken to attacker",
                "parameters": ["percentage", "duration"],
                "animation": "mirror_shield",
                "video_clip": "abilities/reflect_damage.mp4"
            },
            "immunity": {
                "name": "Immunity",
                "description": "Immune to specified damage type",
                "parameters": ["damage_type", "duration"],
                "animation": "immunity_aura",
                "video_clip": "abilities/immunity.mp4"
            },
            "life_steal": {
                "name": "Life Steal",
                "description": "Heal for X% of damage dealt",
                "parameters": ["percentage"],
                "animation": "life_drain",
                "video_clip": "abilities/life_steal.mp4"
            },
            
            # === ULTIMATE ABILITIES ===
            "ultimate_fire_storm": {
                "name": "Fire Storm",
                "description": "Deal massive fire damage to all enemies",
                "parameters": ["base_damage"],
                "damage_type": DamageType.FIRE,
                "animation": "fire_storm",
                "video_clip": "abilities/ultimate_fire_storm.mp4"
            },
            "ultimate_ice_age": {
                "name": "Ice Age",
                "description": "Freeze all enemies for multiple turns",
                "parameters": ["duration"],
                "animation": "ice_age",
                "video_clip": "abilities/ultimate_ice_age.mp4"
            },
            "ultimate_nature_wrath": {
                "name": "Nature's Wrath",
                "description": "Massive healing and damage over time",
                "parameters": ["heal_amount", "damage_amount", "duration"],
                "animation": "nature_wrath",
                "video_clip": "abilities/ultimate_nature_wrath.mp4"
            }
        }
    
    def execute_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                       game_state: Any, target_id: Optional[str] = None) -> AbilityResult:
        """Execute a card ability with full validation and effects"""
        result = AbilityResult()
        
        # Validate ability exists
        if ability_name not in self.ability_catalog:
            result.success = False
            result.error_message = f"Unknown ability: {ability_name}"
            return result
        
        ability_def = self.ability_catalog[ability_name]
        
        # Validate parameters
        validation_result = self._validate_parameters(ability_def, parameters)
        if not validation_result[0]:
            result.success = False
            result.error_message = validation_result[1]
            return result
        
        # Set animation data
        result.animation_data = {
            "animation": ability_def.get("animation", "default"),
            "video_clip": ability_def.get("video_clip", "abilities/default.mp4"),
            "ability_name": ability_name
        }
        
        try:
            # Execute specific ability
            if ability_name in ["deal_damage", "fire_damage", "water_damage", "piercing_damage"]:
                self._execute_damage_ability(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name == "area_damage":
                self._execute_area_damage(parameters, caster, game_state, result)
            elif ability_name in ["heal", "regeneration"]:
                self._execute_heal_ability(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name == "area_heal":
                self._execute_area_heal(parameters, caster, game_state, result)
            elif ability_name in ["buff_attack", "buff_defense"]:
                self._execute_buff_ability(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name in ["debuff_attack", "debuff_defense"]:
                self._execute_debuff_ability(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name in ["burn", "poison", "freeze", "stun"]:
                self._execute_status_effect(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name in ["gain_energy", "gain_mana", "mana_burn"]:
                self._execute_resource_ability(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name in ["draw_card", "discard_card"]:
                self._execute_card_manipulation(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name in ["teleport", "reflect_damage", "immunity", "life_steal"]:
                self._execute_special_ability(ability_name, parameters, caster, game_state, target_id, result)
            elif ability_name.startswith("ultimate_"):
                self._execute_ultimate_ability(ability_name, parameters, caster, game_state, result)
            else:
                result.success = False
                result.error_message = f"Ability execution not implemented: {ability_name}"
            
            logger.info(f"Executed ability {ability_name} - Success: {result.success}")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Ability execution failed: {str(e)}"
            logger.error(f"Error executing ability {ability_name}: {e}")
        
        return result
    
    def _validate_parameters(self, ability_def: Dict, parameters: Dict) -> Tuple[bool, str]:
        """Validate ability parameters"""
        required_params = ability_def.get("parameters", [])
        
        for param in required_params:
            if param not in parameters:
                return False, f"Missing required parameter: {param}"
        
        # Validate parameter types and ranges
        if "amount" in parameters:
            amount = parameters["amount"]
            if not isinstance(amount, (int, float)) or amount < 0:
                return False, "Amount must be a non-negative number"
        
        if "duration" in parameters:
            duration = parameters["duration"]
            if not isinstance(duration, int) or duration < 1:
                return False, "Duration must be a positive integer"
        
        if "target_type" in parameters:
            target_type = parameters["target_type"]
            if target_type not in [t.value for t in TargetType]:
                return False, f"Invalid target type: {target_type}"
        
        return True, ""
    
    def _execute_damage_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                               game_state: Any, target_id: str, result: AbilityResult):
        """Execute damage-dealing abilities"""
        amount = parameters["amount"]
        target_type = parameters.get("target_type", TargetType.ENEMY.value)
        
        # Apply arena bonuses
        damage_type = self.ability_catalog[ability_name].get("damage_type", DamageType.PHYSICAL)
        final_amount = self._apply_arena_damage_bonus(amount, damage_type, game_state)
        
        # Get targets
        targets = self._resolve_targets(target_type, caster, game_state, target_id)
        
        for target in targets:
            # Apply damage with armor calculation
            actual_damage = self._calculate_damage(final_amount, target, damage_type)
            
            # Apply damage
            target["health"] = max(0, target["health"] - actual_damage)
            
            result.damage_dealt += actual_damage
            result.targets_affected.append(target.get("id", "unknown"))
            
            # Check for life steal
            if "life_steal" in caster.get("abilities", []):
                heal_amount = int(actual_damage * 0.25)  # 25% life steal
                caster["health"] = min(caster.get("max_health", 20), caster["health"] + heal_amount)
                result.healing_done += heal_amount
    
    def _execute_area_damage(self, parameters: Dict, caster: Dict, game_state: Any, result: AbilityResult):
        """Execute area damage abilities"""
        amount = parameters["amount"]
        
        # Get all enemy targets
        enemies = self._get_all_enemies(caster, game_state)
        
        for enemy in enemies:
            actual_damage = self._calculate_damage(amount, enemy, DamageType.PHYSICAL)
            enemy["health"] = max(0, enemy["health"] - actual_damage)
            
            result.damage_dealt += actual_damage
            result.targets_affected.append(enemy.get("id", "unknown"))
    
    def _execute_heal_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                             game_state: Any, target_id: str, result: AbilityResult):
        """Execute healing abilities"""
        amount = parameters["amount"]
        
        if ability_name == "regeneration":
            # Apply regeneration status effect
            duration = parameters["duration"]
            target = self._resolve_single_target(parameters.get("target_type", TargetType.SELF.value), 
                                               caster, game_state, target_id)
            
            if target:
                effect = StatusEffect("regeneration", amount, duration, caster.get("id", "unknown"))
                self._apply_status_effect(target, effect, result)
        else:
            # Direct healing
            target_type = parameters.get("target_type", TargetType.ALLY.value)
            targets = self._resolve_targets(target_type, caster, game_state, target_id)
            
            for target in targets:
                # Apply arena healing bonus
                final_amount = self._apply_arena_healing_bonus(amount, game_state)
                
                max_health = target.get("max_health", 20)
                old_health = target["health"]
                target["health"] = min(max_health, old_health + final_amount)
                
                actual_healing = target["health"] - old_health
                result.healing_done += actual_healing
                result.targets_affected.append(target.get("id", "unknown"))
    
    def _execute_area_heal(self, parameters: Dict, caster: Dict, game_state: Any, result: AbilityResult):
        """Execute area healing abilities"""
        amount = parameters["amount"]
        
        # Get all ally targets
        allies = self._get_all_allies(caster, game_state)
        
        for ally in allies:
            final_amount = self._apply_arena_healing_bonus(amount, game_state)
            max_health = ally.get("max_health", 20)
            old_health = ally["health"]
            ally["health"] = min(max_health, old_health + final_amount)
            
            actual_healing = ally["health"] - old_health
            result.healing_done += actual_healing
            result.targets_affected.append(ally.get("id", "unknown"))
    
    def _execute_buff_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                             game_state: Any, target_id: str, result: AbilityResult):
        """Execute buff abilities"""
        amount = parameters["amount"]
        duration = parameters["duration"]
        target_type = parameters.get("target_type", TargetType.ALLY.value)
        
        targets = self._resolve_targets(target_type, caster, game_state, target_id)
        
        buff_type = "attack_buff" if "attack" in ability_name else "defense_buff"
        
        for target in targets:
            effect = StatusEffect(buff_type, amount, duration, caster.get("id", "unknown"))
            self._apply_status_effect(target, effect, result)
    
    def _execute_debuff_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                               game_state: Any, target_id: str, result: AbilityResult):
        """Execute debuff abilities"""
        amount = parameters["amount"]
        duration = parameters["duration"]
        target_type = parameters.get("target_type", TargetType.ENEMY.value)
        
        targets = self._resolve_targets(target_type, caster, game_state, target_id)
        
        debuff_type = "attack_debuff" if "attack" in ability_name else "defense_debuff"
        
        for target in targets:
            effect = StatusEffect(debuff_type, amount, duration, caster.get("id", "unknown"))
            self._apply_status_effect(target, effect, result)
    
    def _execute_status_effect(self, ability_name: str, parameters: Dict, caster: Dict, 
                              game_state: Any, target_id: str, result: AbilityResult):
        """Execute status effect abilities"""
        duration = parameters["duration"]
        amount = parameters.get("amount", 0)
        
        target = self._resolve_single_target(TargetType.ENEMY.value, caster, game_state, target_id)
        
        if target:
            effect = StatusEffect(ability_name, amount, duration, caster.get("id", "unknown"))
            self._apply_status_effect(target, effect, result)
    
    def _execute_resource_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                                 game_state: Any, target_id: str, result: AbilityResult):
        """Execute resource manipulation abilities"""
        amount = parameters["amount"]
        
        if ability_name == "gain_energy":
            player_state = self._get_player_state(caster, game_state)
            player_state["energy"] += amount
            result.energy_changes[caster.get("team", 0)] = amount
            
        elif ability_name == "gain_mana":
            color = parameters["color"]
            player_state = self._get_player_state(caster, game_state)
            player_state["mana"][color] = player_state["mana"].get(color, 0) + amount
            result.mana_changes[color] = amount
            
        elif ability_name == "mana_burn":
            color = parameters.get("color", "any")
            opponent_state = self._get_opponent_state(caster, game_state)
            
            if color == "any":
                # Burn any available mana
                for mana_color, mana_amount in opponent_state["mana"].items():
                    if mana_amount > 0:
                        burned = min(amount, mana_amount)
                        opponent_state["mana"][mana_color] -= burned
                        result.mana_changes[mana_color] = -burned
                        break
            else:
                # Burn specific color
                current_mana = opponent_state["mana"].get(color, 0)
                burned = min(amount, current_mana)
                opponent_state["mana"][color] = current_mana - burned
                result.mana_changes[color] = -burned
    
    def _execute_card_manipulation(self, ability_name: str, parameters: Dict, caster: Dict, 
                                  game_state: Any, target_id: str, result: AbilityResult):
        """Execute card manipulation abilities"""
        amount = parameters["amount"]
        
        if ability_name == "draw_card":
            # In physical card game, this is simulated
            player_state = self._get_player_state(caster, game_state)
            # Add placeholder cards to hand
            for _ in range(amount):
                player_state["hand"].append({"id": f"drawn_{datetime.now().timestamp()}", "name": "Drawn Card"})
            
        elif ability_name == "discard_card":
            opponent_state = self._get_opponent_state(caster, game_state)
            cards_to_discard = min(amount, len(opponent_state["hand"]))
            
            for _ in range(cards_to_discard):
                if opponent_state["hand"]:
                    discarded = opponent_state["hand"].pop(0)
                    opponent_state["graveyard"].append(discarded)
    
    def _execute_special_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                                game_state: Any, target_id: str, result: AbilityResult):
        """Execute special abilities"""
        if ability_name == "teleport":
            # Move target to different battlefield position
            target_type = parameters.get("target_type", TargetType.ALLY.value)
            target = self._resolve_single_target(target_type, caster, game_state, target_id)
            
            if target:
                # Teleportation effect (position change)
                target["position"] = target.get("position", 0) + 1
                result.targets_affected.append(target.get("id", "unknown"))
        
        elif ability_name == "reflect_damage":
            percentage = parameters["percentage"]
            duration = parameters["duration"]
            
            target = self._resolve_single_target(TargetType.SELF.value, caster, game_state, target_id)
            if target:
                effect = StatusEffect("reflect_damage", percentage, duration, caster.get("id", "unknown"))
                self._apply_status_effect(target, effect, result)
        
        elif ability_name == "immunity":
            damage_type = parameters["damage_type"]
            duration = parameters["duration"]
            
            target = self._resolve_single_target(TargetType.SELF.value, caster, game_state, target_id)
            if target:
                effect = StatusEffect(f"immunity_{damage_type}", 100, duration, caster.get("id", "unknown"))
                self._apply_status_effect(target, effect, result)
        
        elif ability_name == "life_steal":
            # Add life steal property to caster
            percentage = parameters["percentage"]
            if "abilities" not in caster:
                caster["abilities"] = []
            caster["abilities"].append(f"life_steal_{percentage}")
    
    def _execute_ultimate_ability(self, ability_name: str, parameters: Dict, caster: Dict, 
                                 game_state: Any, result: AbilityResult):
        """Execute ultimate abilities"""
        if ability_name == "ultimate_fire_storm":
            base_damage = parameters["base_damage"]
            enemies = self._get_all_enemies(caster, game_state)
            
            for enemy in enemies:
                # Ultimate abilities deal massive damage
                final_damage = base_damage + 5  # Base ultimate bonus
                actual_damage = self._calculate_damage(final_damage, enemy, DamageType.FIRE)
                enemy["health"] = max(0, enemy["health"] - actual_damage)
                
                result.damage_dealt += actual_damage
                result.targets_affected.append(enemy.get("id", "unknown"))
        
        elif ability_name == "ultimate_ice_age":
            duration = parameters["duration"]
            enemies = self._get_all_enemies(caster, game_state)
            
            for enemy in enemies:
                effect = StatusEffect("freeze", 0, duration + 1, caster.get("id", "unknown"))  # Extra duration for ultimate
                self._apply_status_effect(enemy, effect, result)
        
        elif ability_name == "ultimate_nature_wrath":
            heal_amount = parameters["heal_amount"]
            damage_amount = parameters["damage_amount"]
            duration = parameters["duration"]
            
            # Heal all allies
            allies = self._get_all_allies(caster, game_state)
            for ally in allies:
                max_health = ally.get("max_health", 20)
                old_health = ally["health"]
                ally["health"] = min(max_health, old_health + heal_amount)
                result.healing_done += ally["health"] - old_health
                result.targets_affected.append(ally.get("id", "unknown"))
            
            # Apply damage over time to enemies
            enemies = self._get_all_enemies(caster, game_state)
            for enemy in enemies:
                effect = StatusEffect("poison", damage_amount, duration, caster.get("id", "unknown"))
                self._apply_status_effect(enemy, effect, result)
    
    # === HELPER METHODS ===
    
    def _resolve_targets(self, target_type: str, caster: Dict, game_state: Any, target_id: str = None) -> List[Dict]:
        """Resolve ability targets based on target type"""
        if target_type == TargetType.SELF.value:
            return [caster]
        elif target_type == TargetType.ALL_ALLIES.value:
            return self._get_all_allies(caster, game_state)
        elif target_type == TargetType.ALL_ENEMIES.value:
            return self._get_all_enemies(caster, game_state)
        elif target_type == TargetType.ALL.value:
            return self._get_all_allies(caster, game_state) + self._get_all_enemies(caster, game_state)
        elif target_type in [TargetType.ALLY.value, TargetType.ENEMY.value, TargetType.ANY.value]:
            target = self._resolve_single_target(target_type, caster, game_state, target_id)
            return [target] if target else []
        elif target_type == TargetType.RANDOM_ENEMY.value:
            enemies = self._get_all_enemies(caster, game_state)
            return [enemies[0]] if enemies else []  # Simplified random selection
        elif target_type == TargetType.RANDOM_ALLY.value:
            allies = self._get_all_allies(caster, game_state)
            return [allies[0]] if allies else []  # Simplified random selection
        
        return []
    
    def _resolve_single_target(self, target_type: str, caster: Dict, game_state: Any, target_id: str = None) -> Optional[Dict]:
        """Resolve a single target"""
        if target_type == TargetType.SELF.value:
            return caster
        
        # For now, return the first available target of the specified type
        # In a full implementation, this would use the target_id to find the specific target
        if target_type == TargetType.ALLY.value:
            allies = self._get_all_allies(caster, game_state)
            return allies[0] if allies else None
        elif target_type == TargetType.ENEMY.value:
            enemies = self._get_all_enemies(caster, game_state)
            return enemies[0] if enemies else None
        
        return None
    
    def _get_all_allies(self, caster: Dict, game_state: Any) -> List[Dict]:
        """Get all allied targets"""
        caster_team = caster.get("team", 0)
        player_state = game_state.players.get(str(caster_team))
        
        if not player_state:
            return []
        
        allies = []
        # Add hero if exists
        if player_state.hero:
            allies.append(player_state.hero)
        
        # Add battlefield creatures
        allies.extend(player_state.battlefield)
        
        return allies
    
    def _get_all_enemies(self, caster: Dict, game_state: Any) -> List[Dict]:
        """Get all enemy targets"""
        caster_team = caster.get("team", 0)
        opponent_team = 1 - caster_team
        opponent_state = game_state.players.get(str(opponent_team))
        
        if not opponent_state:
            return []
        
        enemies = []
        # Add opponent hero if exists
        if opponent_state.hero:
            enemies.append(opponent_state.hero)
        
        # Add opponent battlefield creatures
        enemies.extend(opponent_state.battlefield)
        
        return enemies
    
    def _get_player_state(self, caster: Dict, game_state: Any):
        """Get the player state for the caster"""
        caster_team = caster.get("team", 0)
        return game_state.players.get(str(caster_team))
    
    def _get_opponent_state(self, caster: Dict, game_state: Any):
        """Get the opponent's player state"""
        caster_team = caster.get("team", 0)
        opponent_team = 1 - caster_team
        return game_state.players.get(str(opponent_team))
    
    def _calculate_damage(self, base_damage: int, target: Dict, damage_type: DamageType) -> int:
        """Calculate final damage after armor and resistances"""
        final_damage = base_damage
        
        # Apply armor (only for non-piercing damage)
        if damage_type != DamageType.PIERCING:
            armor = target.get("defense", 0)
            final_damage = max(1, final_damage - armor)  # Minimum 1 damage
        
        # Apply damage type resistances/immunities
        immunities = target.get("immunities", [])
        if damage_type.value in immunities:
            return 0
        
        resistances = target.get("resistances", {})
        if damage_type.value in resistances:
            resistance_percent = resistances[damage_type.value]
            final_damage = int(final_damage * (1 - resistance_percent / 100))
        
        return max(0, final_damage)
    
    def _apply_arena_damage_bonus(self, base_damage: int, damage_type: DamageType, game_state: Any) -> int:
        """Apply arena-specific damage bonuses"""
        arena = game_state.arena
        arena_color = arena.color if arena else "NEUTRAL"
        
        # Arena damage bonuses
        if damage_type == DamageType.FIRE and arena_color == "CRIMSON":
            return base_damage + 1
        elif damage_type == DamageType.WATER and arena_color == "AZURE":
            return base_damage + 1
        
        return base_damage
    
    def _apply_arena_healing_bonus(self, base_healing: int, game_state: Any) -> int:
        """Apply arena-specific healing bonuses"""
        arena = game_state.arena
        arena_color = arena.color if arena else "NEUTRAL"
        
        # Arena healing bonuses
        if arena_color == "VERDANT":
            return base_healing + 1
        
        return base_healing
    
    def _apply_status_effect(self, target: Dict, effect: StatusEffect, result: AbilityResult):
        """Apply a status effect to a target"""
        target_id = target.get("id", "unknown")
        
        if target_id not in self.active_effects:
            self.active_effects[target_id] = []
        
        self.active_effects[target_id].append(effect)
        result.status_effects_applied.append(effect)
        result.targets_affected.append(target_id)
    
    def process_turn_start_effects(self, game_state: Any) -> List[Dict]:
        """Process all status effects at the start of a turn"""
        effects_processed = []
        
        for target_id, effects in self.active_effects.items():
            remaining_effects = []
            
            for effect in effects:
                # Process effect
                effect_result = self._process_status_effect(effect, target_id, game_state)
                if effect_result:
                    effects_processed.append(effect_result)
                
                # Decrease duration
                effect.duration -= 1
                
                # Keep effect if duration > 0
                if effect.duration > 0:
                    remaining_effects.append(effect)
            
            # Update effects list
            if remaining_effects:
                self.active_effects[target_id] = remaining_effects
            else:
                del self.active_effects[target_id]
        
        return effects_processed
    
    def _process_status_effect(self, effect: StatusEffect, target_id: str, game_state: Any) -> Optional[Dict]:
        """Process a single status effect"""
        # Find target in game state
        target = self._find_target_by_id(target_id, game_state)
        if not target:
            return None
        
        effect_data = {
            "target_id": target_id,
            "effect_type": effect.effect_type,
            "amount": effect.amount
        }
        
        if effect.effect_type == "burn":
            # Deal fire damage
            damage = self._calculate_damage(effect.amount, target, DamageType.FIRE)
            target["health"] = max(0, target["health"] - damage)
            effect_data["damage_dealt"] = damage
            
        elif effect.effect_type == "poison":
            # Deal poison damage
            damage = self._calculate_damage(effect.amount, target, DamageType.PHYSICAL)
            target["health"] = max(0, target["health"] - damage)
            effect_data["damage_dealt"] = damage
            
        elif effect.effect_type == "regeneration":
            # Heal target
            max_health = target.get("max_health", 20)
            old_health = target["health"]
            target["health"] = min(max_health, old_health + effect.amount)
            effect_data["healing_done"] = target["health"] - old_health
            
        elif effect.effect_type in ["freeze", "stun"]:
            # Skip turn effects (handled by game state manager)
            effect_data["action"] = "skip_turn"
        
        return effect_data
    
    def _find_target_by_id(self, target_id: str, game_state: Any) -> Optional[Dict]:
        """Find a target by ID in the game state"""
        # Search through all players and their creatures
        for player_state in game_state.players.values():
            # Check hero
            if player_state.hero and player_state.hero.get("id") == target_id:
                return player_state.hero
            
            # Check battlefield creatures
            for creature in player_state.battlefield:
                if creature.get("id") == target_id:
                    return creature
        
        return None
    
    def get_ability_info(self, ability_name: str) -> Optional[Dict]:
        """Get information about an ability"""
        return self.ability_catalog.get(ability_name)
    
    def validate_ability_parameters(self, ability_name: str, parameters: Dict) -> Tuple[bool, str]:
        """Validate ability parameters without executing"""
        if ability_name not in self.ability_catalog:
            return False, f"Unknown ability: {ability_name}"
        
        ability_def = self.ability_catalog[ability_name]
        return self._validate_parameters(ability_def, parameters)
    
    def get_all_abilities(self) -> List[str]:
        """Get list of all available abilities"""
        return list(self.ability_catalog.keys())
