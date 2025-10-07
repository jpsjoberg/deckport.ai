extends Node
# class_name CardAbilitiesCatalog  # Commented out to avoid autoload conflict

# All possible card abilities in the system
# This will be used to validate cards and implement effects dynamically

var ability_definitions = {
	# === DAMAGE ABILITIES ===
	"deal_damage": {
		"name": "Deal Damage",
		"description": "Deal X damage to target",
		"parameters": ["amount", "target_type"],
		"animation": "damage_burst",
		"video_clip": "abilities/deal_damage.mp4"
	},
	"fire_damage": {
		"name": "Fire Damage", 
		"description": "Deal X fire damage to target",
		"parameters": ["amount", "target_type"],
		"animation": "fire_burst",
		"video_clip": "abilities/fire_damage.mp4"
	},
	"water_damage": {
		"name": "Water Damage",
		"description": "Deal X water damage to target", 
		"parameters": ["amount", "target_type"],
		"animation": "water_burst",
		"video_clip": "abilities/water_damage.mp4"
	},
	"piercing_damage": {
		"name": "Piercing Damage",
		"description": "Deal X damage that ignores armor",
		"parameters": ["amount", "target_type"],
		"animation": "pierce_strike",
		"video_clip": "abilities/piercing_damage.mp4"
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
	
	# === BUFF/DEBUFF ABILITIES ===
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
	
	# === CARD DRAW/MANIPULATION ===
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
	
	# === AREA EFFECTS ===
	"area_damage": {
		"name": "Area Damage",
		"description": "Deal X damage to all enemies",
		"parameters": ["amount"],
		"animation": "explosion",
		"video_clip": "abilities/area_damage.mp4"
	},
	"area_heal": {
		"name": "Area Heal",
		"description": "Heal X to all allies",
		"parameters": ["amount"],
		"animation": "healing_wave",
		"video_clip": "abilities/area_heal.mp4"
	},
	
	# === ULTIMATE ABILITIES ===
	"ultimate_fire_storm": {
		"name": "Fire Storm",
		"description": "Deal massive fire damage to all enemies",
		"parameters": ["base_damage"],
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

# Target types for abilities
var target_types = {
	"self": "Self",
	"ally": "Allied target",
	"enemy": "Enemy target", 
	"any": "Any target",
	"all_allies": "All allies",
	"all_enemies": "All enemies",
	"all": "All targets",
	"random_enemy": "Random enemy",
	"random_ally": "Random ally"
}

# Animation types
var animation_types = {
	"damage_burst": "Quick damage flash",
	"fire_burst": "Fire explosion effect",
	"water_burst": "Water splash effect",
	"healing_light": "Golden healing glow",
	"power_up": "Red strength aura",
	"shield_up": "Blue defensive barrier",
	"burning_effect": "Continuous fire damage",
	"ice_prison": "Freezing ice effect",
	"energy_surge": "Lightning energy boost",
	"mana_crystal": "Colored mana crystal",
	"explosion": "Large area explosion",
	"teleport_flash": "Instant movement flash"
}

func _ready():
	print("🎴 Card Abilities Catalog initialized with ", ability_definitions.size(), " abilities")

func get_ability_definition(ability_name: String) -> Dictionary:
	"""Get the definition for a specific ability"""
	return ability_definitions.get(ability_name, {})

func is_valid_ability(ability_name: String) -> bool:
	"""Check if an ability exists in the catalog"""
	return ability_definitions.has(ability_name)

func get_ability_video_clip(ability_name: String) -> String:
	"""Get the video clip path for an ability"""
	var definition = get_ability_definition(ability_name)
	return definition.get("video_clip", "abilities/default.mp4")

func get_ability_animation(ability_name: String) -> String:
	"""Get the animation type for an ability"""
	var definition = get_ability_definition(ability_name)
	return definition.get("animation", "default")

func validate_card_abilities(card_abilities: Array) -> Dictionary:
	"""Validate that all abilities on a card are defined"""
	var result = {
		"valid": true,
		"invalid_abilities": [],
		"missing_parameters": []
	}
	
	for ability in card_abilities:
		var ability_name = ""
		var ability_params = {}
		
		if ability is String:
			ability_name = ability
		elif ability is Dictionary:
			ability_name = ability.get("name", "")
			ability_params = ability.get("parameters", {})
		
		if not is_valid_ability(ability_name):
			result.valid = false
			result.invalid_abilities.append(ability_name)
			continue
		
		# Check required parameters
		var definition = get_ability_definition(ability_name)
		var required_params = definition.get("parameters", [])
		
		for param in required_params:
			if not ability_params.has(param):
				result.valid = false
				result.missing_parameters.append({
					"ability": ability_name,
					"missing_param": param
				})
	
	return result

func get_all_abilities() -> Array:
	"""Get list of all available abilities"""
	return ability_definitions.keys()

func get_abilities_by_category() -> Dictionary:
	"""Get abilities organized by category"""
	var categories = {
		"damage": [],
		"healing": [],
		"buffs": [],
		"debuffs": [],
		"status": [],
		"resource": [],
		"special": [],
		"area": [],
		"ultimate": []
	}
	
	for ability_name in ability_definitions:
		var definition = ability_definitions[ability_name]
		var name = definition.get("name", ability_name)
		
		# Categorize based on ability name patterns
		if ability_name.contains("damage"):
			categories.damage.append({"name": ability_name, "display": name})
		elif ability_name.contains("heal"):
			categories.healing.append({"name": ability_name, "display": name})
		elif ability_name.contains("buff"):
			categories.buffs.append({"name": ability_name, "display": name})
		elif ability_name.contains("debuff"):
			categories.debuffs.append({"name": ability_name, "display": name})
		elif ability_name.contains("burn") or ability_name.contains("freeze") or ability_name.contains("poison") or ability_name.contains("stun"):
			categories.status.append({"name": ability_name, "display": name})
		elif ability_name.contains("mana") or ability_name.contains("energy"):
			categories.resource.append({"name": ability_name, "display": name})
		elif ability_name.contains("area"):
			categories.area.append({"name": ability_name, "display": name})
		elif ability_name.contains("ultimate"):
			categories.ultimate.append({"name": ability_name, "display": name})
		else:
			categories.special.append({"name": ability_name, "display": name})
	
	return categories

func create_ability_effect_data(ability_name: String, parameters: Dictionary) -> Dictionary:
	"""Create standardized effect data for an ability"""
	var definition = get_ability_definition(ability_name)
	if definition.is_empty():
		return {}
	
	return {
		"ability": ability_name,
		"name": definition.get("name", ability_name),
		"description": definition.get("description", ""),
		"parameters": parameters,
		"animation": definition.get("animation", "default"),
		"video_clip": definition.get("video_clip", "abilities/default.mp4"),
		"timestamp": Time.get_unix_time_from_system()
	}

func execute_ability_animation(ability_name: String, target_position: Vector2 = Vector2.ZERO) -> void:
	"""Execute the visual animation for an ability"""
	var definition = get_ability_definition(ability_name)
	if definition.is_empty():
		print("❌ Cannot animate unknown ability: ", ability_name)
		return
	
	var animation_type = definition.get("animation", "default")
	var video_clip = definition.get("video_clip", "")
	
	print("🎬 Playing animation: ", animation_type, " for ability: ", ability_name)
	
	# Emit signal for animation system to handle
	# This will be caught by the card display manager or battle scene
	var animation_data = {
		"ability_name": ability_name,
		"animation_type": animation_type,
		"video_clip": video_clip,
		"target_position": target_position,
		"duration": 2.0  # Standard 2-second duration
	}
	
	# In a full implementation, this would trigger the actual animation
	# For now, we log the animation request
	print("🎯 Animation data: ", animation_data)

func validate_ability_execution(card_data: Dictionary, ability_name: String, game_state: Dictionary) -> Dictionary:
	"""Validate if an ability can be executed given current game state"""
	var result = {
		"can_execute": false,
		"error_message": "",
		"required_resources": {},
		"valid_targets": []
	}
	
	# Check if ability exists
	if not is_valid_ability(ability_name):
		result.error_message = "Unknown ability: " + ability_name
		return result
	
	var definition = get_ability_definition(ability_name)
	var required_params = definition.get("parameters", [])
	
	# Check energy requirements (from card cost)
	var energy_cost = card_data.get("energy_cost", 0)
	var current_energy = game_state.get("player_energy", 0)
	
	if current_energy < energy_cost:
		result.error_message = "Insufficient energy: need " + str(energy_cost) + ", have " + str(current_energy)
		result.required_resources["energy"] = energy_cost
		return result
	
	# Check mana requirements
	var mana_costs = card_data.get("mana_costs", {})
	var current_mana = game_state.get("player_mana", {})
	
	for color in mana_costs:
		var required = mana_costs[color]
		var available = current_mana.get(color, 0)
		
		if available < required:
			result.error_message = "Insufficient " + color + " mana: need " + str(required) + ", have " + str(available)
			result.required_resources[color] = required
			return result
	
	# Check target requirements
	if "target_type" in required_params:
		var valid_targets = _get_valid_targets_for_ability(ability_name, game_state)
		result.valid_targets = valid_targets
		
		if valid_targets.is_empty() and definition.get("requires_target", false):
			result.error_message = "No valid targets available"
			return result
	
	result.can_execute = true
	return result

func _get_valid_targets_for_ability(ability_name: String, game_state: Dictionary) -> Array:
	"""Get list of valid targets for an ability based on current game state"""
	var definition = get_ability_definition(ability_name)
	var valid_targets = []
	
	# This would need to be implemented based on the actual game state structure
	# For now, return placeholder targets
	var battlefield_creatures = game_state.get("battlefield_creatures", [])
	var opponent_creatures = game_state.get("opponent_creatures", [])
	
	# Damage abilities typically target enemies
	if ability_name.contains("damage") or ability_name.contains("debuff"):
		valid_targets = opponent_creatures
	
	# Healing and buff abilities typically target allies
	elif ability_name.contains("heal") or ability_name.contains("buff"):
		valid_targets = battlefield_creatures
	
	# Area abilities don't need specific targets
	elif ability_name.contains("area"):
		valid_targets = ["area_effect"]
	
	return valid_targets

func get_ability_cost_info(ability_name: String) -> Dictionary:
	"""Get cost information for an ability (for UI display)"""
	var definition = get_ability_definition(ability_name)
	if definition.is_empty():
		return {}
	
	return {
		"name": definition.get("name", ability_name),
		"description": definition.get("description", ""),
		"parameters": definition.get("parameters", []),
		"estimated_cost": _estimate_ability_cost(ability_name),
		"target_required": "target_type" in definition.get("parameters", [])
	}

func _estimate_ability_cost(ability_name: String) -> Dictionary:
	"""Estimate the typical cost for an ability (for balance reference)"""
	var cost_estimates = {
		"energy": 1,
		"mana": {}
	}
	
	# Ultimate abilities are expensive
	if ability_name.begins_with("ultimate_"):
		cost_estimates.energy = 5
		cost_estimates.mana = {"any": 3}
	
	# Area effects are more expensive
	elif ability_name.contains("area"):
		cost_estimates.energy = 3
		cost_estimates.mana = {"any": 2}
	
	# Damage abilities vary by amount
	elif ability_name.contains("damage"):
		cost_estimates.energy = 2
		if ability_name.contains("fire"):
			cost_estimates.mana = {"CRIMSON": 1}
		elif ability_name.contains("water"):
			cost_estimates.mana = {"AZURE": 1}
	
	# Healing abilities
	elif ability_name.contains("heal"):
		cost_estimates.energy = 2
		cost_estimates.mana = {"VERDANT": 1}
	
	# Utility abilities are cheaper
	else:
		cost_estimates.energy = 1
	
	return cost_estimates



