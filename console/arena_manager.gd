extends Node
class_name ArenaManager

signal arena_selected(arena_data: Dictionary)
signal arena_effect_triggered(effect_name: String, effect_data: Dictionary)
signal mana_generated(color: String, amount: int)

# Arena data
var current_arena: Dictionary = {}
var available_arenas: Array[Dictionary] = []

# Mana colors enum
enum ManaColor {
	CRIMSON,
	AZURE, 
	VERDANT,
	GOLDEN,
	SHADOW,
	AETHER
}

# Color opposition mapping
var color_oppositions = {
	"CRIMSON": "AZURE",
	"AZURE": "CRIMSON", 
	"VERDANT": "SHADOW",
	"SHADOW": "VERDANT",
	"GOLDEN": "SHADOW",
	"AETHER": ""
}

func _ready():
	print("🏟️ Arena Manager initialized")
	load_available_arenas()

func load_available_arenas():
	"""Load arena data from API or local config"""
	# For now, define some basic arenas - will be loaded from API later
	available_arenas = [
		{
			"id": 1,
			"name": "Crimson Forge",
			"mana_color": "CRIMSON",
			"mana_generation": 2,
			"background_video": "crimson_forge_ambient.mp4",
			"passive_effects": {
				"fire_damage_bonus": 1,
				"water_spell_penalty": 1
			},
			"hero_bonuses": {
				"CRIMSON": {"attack": 2, "defense": 0, "abilities": ["fire_immunity"]},
				"AZURE": {"attack": -1, "defense": -1, "penalties": ["water_spells_cost_extra"]}
			},
			"special_rules": {
				"forge_hammer": "Once per turn, CRIMSON heroes can deal 1 damage to any target"
			},
			"objectives": [
				{
					"id": "forge_master",
					"name": "Forge Master",
					"type": "fire_damage_dealt",
					"target": 15,
					"description": "Deal 15 fire damage to win instantly",
					"reward": "instant_victory"
				},
				{
					"id": "flame_keeper",
					"name": "Flame Keeper", 
					"type": "fire_creatures_summoned",
					"target": 3,
					"description": "Summon 3 fire creatures for +2 attack to all",
					"reward": "all_creatures_attack_bonus"
				}
			],
			"story_text": "Ancient forges burn eternal, empowering fire magic while suppressing water.",
			"clips": {
				"intro": "crimson_forge_intro.mp4",
				"advantage": "crimson_forge_advantage.mp4", 
				"hazard": "crimson_forge_hazard.mp4",
				"objective_complete": "crimson_forge_objective.mp4"
			}
		},
		{
			"id": 2,
			"name": "Azure Depths",
			"mana_color": "AZURE",
			"mana_generation": 2,
			"background_video": "azure_depths_ambient.mp4",
			"passive_effects": {
				"water_mastery": -1,
				"fire_suppression": -1
			},
			"hero_bonuses": {
				"AZURE": {"attack": 0, "defense": 2, "abilities": ["spell_cost_reduction"]},
				"CRIMSON": {"attack": -1, "defense": -1, "penalties": ["fire_spells_cost_extra"]}
			},
			"special_rules": {
				"tidal_wave": "Every 3rd turn, all creatures take 1 water damage"
			},
			"objectives": [
				{
					"id": "tide_master",
					"name": "Tide Master",
					"type": "creatures_frozen",
					"target": 5,
					"description": "Freeze 5 creatures to gain control of the tides",
					"reward": "extra_mana_generation"
				},
				{
					"id": "depth_walker",
					"name": "Depth Walker",
					"type": "water_spells_cast",
					"target": 8,
					"description": "Cast 8 water spells to unlock the depths",
					"reward": "spell_cost_reduction"
				}
			],
			"story_text": "Deep ocean currents enhance water magic while extinguishing flames.",
			"clips": {
				"intro": "azure_depths_intro.mp4",
				"advantage": "azure_depths_advantage.mp4",
				"hazard": "azure_depths_tidal_wave.mp4",
				"objective_complete": "azure_depths_objective.mp4"
			}
		},
		{
			"id": 3,
			"name": "Verdant Grove", 
			"mana_color": "VERDANT",
			"mana_generation": 2,
			"background_video": "verdant_grove_ambient.mp4",
			"passive_effects": {
				"nature_growth": 1,
				"shadow_weakness": 1
			},
			"hero_bonuses": {
				"VERDANT": {"attack": 1, "defense": 1, "abilities": ["regeneration"]},
				"SHADOW": {"attack": -1, "defense": -1, "penalties": ["dark_spells_weakened"]}
			},
			"special_rules": {
				"life_bloom": "At turn start, all VERDANT creatures heal 1 HP"
			},
			"story_text": "Living trees pulse with natural energy, nurturing growth while banishing darkness.",
			"clips": {
				"intro": "verdant_grove_intro.mp4",
				"advantage": "verdant_grove_bloom.mp4",
				"hazard": "verdant_grove_thorns.mp4"
			}
		}
	]
	print("🏟️ Loaded ", available_arenas.size(), " arenas")

func select_arena(arena_id: int) -> bool:
	"""Select arena for the match"""
	for arena in available_arenas:
		if arena.get("id") == arena_id:
			current_arena = arena
			arena_selected.emit(arena)
			print("🏟️ Arena selected: ", arena.get("name"))
			return true
	
	print("❌ Arena not found: ", arena_id)
	return false

func get_random_arena() -> Dictionary:
	"""Get a random arena for matchmaking"""
	if available_arenas.is_empty():
		return {}
	return available_arenas[randi() % available_arenas.size()]

func get_arena_mana_color() -> String:
	"""Get the mana color provided by current arena"""
	return current_arena.get("mana_color", "AETHER")

func get_mana_generation_amount() -> int:
	"""Get how much mana the arena generates per turn"""
	return current_arena.get("mana_generation", 1)

func calculate_hero_arena_effects(hero_mana_affinity: String) -> Dictionary:
	"""Calculate bonuses/penalties for hero based on arena"""
	if current_arena.is_empty():
		return {}
	
	var arena_color = get_arena_mana_color()
	var hero_bonuses = current_arena.get("hero_bonuses", {})
	
	if hero_bonuses.has(hero_mana_affinity):
		return hero_bonuses[hero_mana_affinity]
	
	# Check if opposing colors
	if is_opposing_color(hero_mana_affinity, arena_color):
		return {
			"attack": -1,
			"defense": -1,
			"penalties": ["opposing_arena_penalty"]
		}
	
	return {}

func is_opposing_color(color1: String, color2: String) -> bool:
	"""Check if two mana colors are opposing"""
	return color_oppositions.get(color1, "") == color2

func get_arena_background_video() -> String:
	"""Get the background video file for current arena"""
	return current_arena.get("background_video", "default_arena.mp4")

func get_arena_clip(clip_type: String) -> String:
	"""Get specific arena clip (intro, advantage, hazard, etc.)"""
	var clips = current_arena.get("clips", {})
	return clips.get(clip_type, "")

func trigger_arena_effect(effect_name: String, context: Dictionary = {}):
	"""Trigger arena-specific effects"""
	var special_rules = current_arena.get("special_rules", {})
	
	if special_rules.has(effect_name):
		var effect_data = {
			"name": effect_name,
			"description": special_rules[effect_name],
			"context": context
		}
		arena_effect_triggered.emit(effect_name, effect_data)
		print("🏟️ Arena effect triggered: ", effect_name)

func generate_turn_mana(player_hero_affinity: String = "") -> Dictionary:
	"""Generate mana for the turn based on arena and hero affinity"""
	var mana_color = get_arena_mana_color()
	var base_amount = get_mana_generation_amount()
	var final_amount = base_amount
	
	# Apply hero affinity bonuses/penalties
	if player_hero_affinity != "":
		if player_hero_affinity == mana_color:
			final_amount += 1  # Matching hero gets bonus
			print("🌟 Hero affinity bonus: +1 ", mana_color, " mana")
		elif is_opposing_color(player_hero_affinity, mana_color):
			final_amount = max(1, final_amount - 1)  # Opposing hero gets penalty
			print("⚡ Hero affinity penalty: -1 ", mana_color, " mana")
	
	var generated_mana = {}
	generated_mana[mana_color] = final_amount
	
	mana_generated.emit(mana_color, final_amount)
	print("🔮 Generated ", final_amount, " ", mana_color, " mana")
	
	return generated_mana

func apply_arena_damage_bonus(base_damage: int, damage_type: String) -> int:
	"""Apply arena-specific damage bonuses"""
	if current_arena.is_empty():
		return base_damage
	
	var passive_effects = current_arena.get("passive_effects", {})
	var arena_color = get_arena_mana_color()
	
	# Fire damage bonus in CRIMSON arenas
	if damage_type == "fire" and arena_color == "CRIMSON":
		if "fire_damage_bonus" in passive_effects:
			var bonus = passive_effects["fire_damage_bonus"]
			print("🔥 Arena fire damage bonus: +", bonus)
			return base_damage + bonus
	
	# Water damage bonus in AZURE arenas  
	elif damage_type == "water" and arena_color == "AZURE":
		if "water_mastery" in passive_effects:
			var bonus = abs(passive_effects["water_mastery"])
			print("🌊 Arena water damage bonus: +", bonus)
			return base_damage + bonus
	
	# Nature damage bonus in VERDANT arenas
	elif damage_type == "nature" and arena_color == "VERDANT":
		if "nature_growth" in passive_effects:
			var bonus = passive_effects["nature_growth"]
			print("🌿 Arena nature damage bonus: +", bonus)
			return base_damage + bonus
	
	return base_damage

func apply_arena_healing_bonus(base_healing: int) -> int:
	"""Apply arena-specific healing bonuses"""
	if current_arena.is_empty():
		return base_healing
	
	var arena_color = get_arena_mana_color()
	
	# Healing bonus in VERDANT arenas
	if arena_color == "VERDANT":
		print("💚 Arena healing bonus: +1")
		return base_healing + 1
	
	return base_healing

func check_special_rule_trigger(rule_name: String, turn_number: int, context: Dictionary = {}) -> bool:
	"""Check if a special arena rule should trigger"""
	if current_arena.is_empty():
		return false
	
	var special_rules = current_arena.get("special_rules", {})
	if not special_rules.has(rule_name):
		return false
	
	var rule_data = special_rules[rule_name]
	var trigger_condition = rule_data.get("trigger", "")
	
	match trigger_condition:
		"once_per_turn":
			return true  # Can be used once per turn
		"every_3_turns":
			return turn_number % 3 == 0
		"every_4_turns":
			return turn_number % 4 == 0
		"turn_start":
			return context.get("phase", "") == "start"
		"on_enemy_death":
			return context.get("event", "") == "enemy_death"
		"on_death":
			return context.get("event", "") == "death"
	
	return false

func execute_special_rule(rule_name: String, _context: Dictionary = {}) -> Dictionary:
	"""Execute a special arena rule and return the result"""
	if current_arena.is_empty():
		return {}
	
	var special_rules = current_arena.get("special_rules", {})
	if not special_rules.has(rule_name):
		return {}
	
	var rule_data = special_rules[rule_name]
	var effect_type = rule_data.get("effect", "")
	var amount = rule_data.get("amount", 0)
	
	var result = {
		"rule_name": rule_name,
		"description": rule_data.get("description", ""),
		"effect_type": effect_type,
		"amount": amount,
		"success": true
	}
	
	print("🏟️ Executing arena rule: ", rule_name)
	
	# Emit signal for game systems to handle the effect
	arena_effect_triggered.emit(rule_name, result)
	
	return result

func get_arena_objective_progress(objective_id: String, current_stats: Dictionary) -> Dictionary:
	"""Check progress on arena objectives"""
	if current_arena.is_empty():
		return {}
	
	var objectives = current_arena.get("objectives", [])
	
	for objective in objectives:
		if objective.get("id", "") == objective_id:
			var objective_type = objective.get("type", "")
			var target_value = objective.get("target", 0)
			var current_value = 0
			
			match objective_type:
				"fire_damage_dealt":
					current_value = current_stats.get("fire_damage_total", 0)
				"creatures_frozen":
					current_value = current_stats.get("creatures_frozen_count", 0)
				"healing_done":
					current_value = current_stats.get("healing_total", 0)
				"fire_creatures_summoned":
					current_value = current_stats.get("fire_creatures_summoned", 0)
				"water_spells_cast":
					current_value = current_stats.get("water_spells_cast", 0)
			
			var progress_percent = float(current_value) / float(target_value) * 100.0
			var is_completed = current_value >= target_value
			
			return {
				"objective_id": objective_id,
				"name": objective.get("name", ""),
				"description": objective.get("description", ""),
				"current_value": current_value,
				"target_value": target_value,
				"progress_percent": progress_percent,
				"completed": is_completed,
				"reward": objective.get("reward", "")
			}
	
	return {}

func get_hero_arena_synergy_info(hero_mana_affinity: String) -> Dictionary:
	"""Get detailed information about hero-arena synergy"""
	var synergy_info = {
		"affinity_match": false,
		"opposing_colors": false,
		"bonuses": {},
		"penalties": {},
		"synergy_level": "neutral"
	}
	
	if current_arena.is_empty():
		return synergy_info
	
	var arena_color = get_arena_mana_color()
	var hero_bonuses = calculate_hero_arena_effects(hero_mana_affinity)
	
	# Check affinity match
	if hero_mana_affinity == arena_color:
		synergy_info.affinity_match = true
		synergy_info.synergy_level = "excellent"
		synergy_info.bonuses = hero_bonuses
	
	# Check opposing colors
	elif is_opposing_color(hero_mana_affinity, arena_color):
		synergy_info.opposing_colors = true
		synergy_info.synergy_level = "poor"
		synergy_info.penalties = hero_bonuses
	
	# Neutral case
	else:
		synergy_info.synergy_level = "neutral"
	
	return synergy_info

func simulate_arena_selection(player1_hero: Dictionary, player2_hero: Dictionary) -> Dictionary:
	"""Simulate arena selection for balanced matchmaking"""
	var p1_affinity = player1_hero.get("mana_affinity", "AETHER")
	var p2_affinity = player2_hero.get("mana_affinity", "AETHER")
	
	var selection_result = {
		"recommended_arena": "",
		"reason": "",
		"balance_score": 0.0,
		"p1_advantage": 0,
		"p2_advantage": 0
	}
	
	# Same affinity - use that arena
	if p1_affinity == p2_affinity:
		for arena in available_arenas:
			if arena.get("mana_color", "") == p1_affinity:
				selection_result.recommended_arena = arena.get("name", "")
				selection_result.reason = "Both heroes share " + p1_affinity + " affinity"
				selection_result.balance_score = 1.0
				break
	
	# Opposing colors - use neutral arena
	elif is_opposing_color(p1_affinity, p2_affinity):
		selection_result.recommended_arena = "Aether Void"
		selection_result.reason = "Heroes have opposing affinities - neutral ground"
		selection_result.balance_score = 1.0
	
	# Different but not opposing - calculate best balance
	else:
		var best_balance = 0.0
		var best_arena = ""
		
		for arena in available_arenas:
			var arena_color = arena.get("mana_color", "")
			var p1_bonus = 1 if p1_affinity == arena_color else 0
			var p2_bonus = 1 if p2_affinity == arena_color else 0
			var balance = 1.0 - abs(p1_bonus - p2_bonus)
			
			if balance > best_balance:
				best_balance = balance
				best_arena = arena.get("name", "")
				selection_result.p1_advantage = p1_bonus
				selection_result.p2_advantage = p2_bonus
		
		selection_result.recommended_arena = best_arena
		selection_result.balance_score = best_balance
		selection_result.reason = "Best balance for different affinities"
	
	return selection_result

func get_current_arena() -> Dictionary:
	"""Get current arena data"""
	return current_arena

func get_available_arenas() -> Array[Dictionary]:
	"""Get all available arenas"""
	return available_arenas
