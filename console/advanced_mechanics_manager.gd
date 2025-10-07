extends Node
class_name AdvancedMechanicsManager

signal card_played_once_per_game(card_sku: String)
signal arena_objective_completed(objective_name: String, player_id: int)
signal legendary_rule_triggered(creature_name: String, rule_type: String)
signal combo_chain_started(combo_name: String, chain_length: int)
signal combo_chain_completed(combo_name: String, total_effects: Array)
signal sacrifice_performed(sacrificed_card: Dictionary, beneficiary_card: Dictionary)
signal card_transformed(original_card: Dictionary, new_card: Dictionary)
signal card_sent_to_graveyard(card: Dictionary, source: String)
signal card_exiled(card: Dictionary, source: String)
signal graveyard_interaction(interaction_type: String, cards: Array)

# Once per game tracking
var played_cards_this_game: Dictionary = {}  # card_sku -> turn_played
var current_match_id: String = ""

# Arena objectives
var current_arena_objectives: Array[Dictionary] = []
var objective_progress: Dictionary = {}  # objective_id -> progress_data

# Legendary creatures on battlefield
var legendary_creatures: Dictionary = {}  # player_id -> [legendary_names]

# Combo system
var active_combos: Array[Dictionary] = []
var combo_definitions: Dictionary = {}
var combo_timer_duration: float = 15.0  # 15 seconds to continue combo

# Game zones
var graveyard: Dictionary = {"player": [], "opponent": []}
var exile_zone: Dictionary = {"player": [], "opponent": []}
var battlefield: Dictionary = {"player": [], "opponent": []}

# Sacrifice tracking
var sacrifice_pool: Array[Dictionary] = []  # Cards available for sacrifice

func _ready():
	print("🎯 Advanced Mechanics Manager initialized")
	setup_combo_definitions()

func initialize_match(match_id: String, arena_data: Dictionary, player_id: int):
	"""Initialize advanced mechanics for a new match"""
	current_match_id = match_id
	played_cards_this_game.clear()
	legendary_creatures.clear()
	active_combos.clear()
	
	# Clear all zones
	for zone in [graveyard, exile_zone, battlefield]:
		zone.player.clear()
		zone.opponent.clear()
	
	sacrifice_pool.clear()
	
	# Setup arena objectives
	setup_arena_objectives(arena_data)
	
	print("🎮 Advanced mechanics initialized for match: ", match_id)

# === ONCE PER GAME MECHANICS ===

func can_play_card_once_per_game(card_sku: String) -> bool:
	"""Check if a card can be played (once per game rule)"""
	return not played_cards_this_game.has(card_sku)

func mark_card_played_once_per_game(card_sku: String, turn_number: int):
	"""Mark a card as played for once per game tracking"""
	if played_cards_this_game.has(card_sku):
		print("⚠️ Card already played this game: ", card_sku)
		return false
	
	played_cards_this_game[card_sku] = turn_number
	card_played_once_per_game.emit(card_sku)
	print("🎴 Card marked as played once per game: ", card_sku)
	return true

func get_played_cards_this_game() -> Dictionary:
	"""Get all cards played this game"""
	return played_cards_this_game.duplicate()

# === ARENA OBJECTIVES ===

func setup_arena_objectives(arena_data: Dictionary):
	"""Setup objectives for the current arena"""
	current_arena_objectives.clear()
	objective_progress.clear()
	
	var objectives = arena_data.get("objectives", [])
	for objective in objectives:
		current_arena_objectives.append(objective)
		objective_progress[objective.get("id", "")] = {
			"progress": 0,
			"target": objective.get("target", 1),
			"completed": false,
			"player_progress": {"player": 0, "opponent": 0}
		}
	
	print("🏟️ Arena objectives setup: ", current_arena_objectives.size())

func update_arena_objective_progress(objective_type: String, player_id: int, amount: int = 1):
	"""Update progress on arena objectives"""
	for objective in current_arena_objectives:
		if objective.get("type") == objective_type:
			var obj_id = objective.get("id", "")
			var progress_data = objective_progress.get(obj_id, {})
			
			if progress_data.has("player_progress"):
				var player_key = "player" if player_id == get_current_player_id() else "opponent"
				progress_data.player_progress[player_key] += amount
				
				var target = progress_data.get("target", 1)
				if progress_data.player_progress[player_key] >= target and not progress_data.completed:
					progress_data.completed = true
					arena_objective_completed.emit(objective.get("name", ""), player_id)
					print("🏆 Arena objective completed: ", objective.get("name", ""))

func get_arena_objectives() -> Array[Dictionary]:
	"""Get current arena objectives with progress"""
	var objectives_with_progress = []
	for objective in current_arena_objectives:
		var obj_copy = objective.duplicate()
		var obj_id = objective.get("id", "")
		obj_copy["progress"] = objective_progress.get(obj_id, {})
		objectives_with_progress.append(obj_copy)
	return objectives_with_progress

# === LEGENDARY CREATURES ===

func can_play_legendary_creature(creature_name: String, player_id: int) -> bool:
	"""Check if a legendary creature can be played (legendary rule)"""
	var player_key = str(player_id)
	var player_legendaries = legendary_creatures.get(player_key, [])
	return not creature_name in player_legendaries

func add_legendary_creature(creature_name: String, player_id: int, card_data: Dictionary):
	"""Add a legendary creature to the battlefield"""
	var player_key = str(player_id)
	if not legendary_creatures.has(player_key):
		legendary_creatures[player_key] = []
	
	if creature_name in legendary_creatures[player_key]:
		print("❌ Legendary rule violation: ", creature_name, " already on battlefield")
		return false
	
	legendary_creatures[player_key].append(creature_name)
	
	# Add to battlefield
	var battlefield_key = "player" if player_id == get_current_player_id() else "opponent"
	battlefield[battlefield_key].append(card_data)
	
	# Trigger legendary rule effects
	trigger_legendary_rule_effects(creature_name, card_data)
	
	print("👑 Legendary creature summoned: ", creature_name)
	return true

func remove_legendary_creature(creature_name: String, player_id: int):
	"""Remove a legendary creature from battlefield"""
	var player_key = str(player_id)
	if legendary_creatures.has(player_key):
		legendary_creatures[player_key].erase(creature_name)
		print("👑 Legendary creature removed: ", creature_name)

func trigger_legendary_rule_effects(creature_name: String, card_data: Dictionary):
	"""Trigger special effects for legendary creatures"""
	var legendary_effects = card_data.get("legendary_effects", [])
	for effect in legendary_effects:
		legendary_rule_triggered.emit(creature_name, effect)
		print("👑 Legendary effect triggered: ", creature_name, " -> ", effect)

# === COMBO ABILITIES ===

func setup_combo_definitions():
	"""Define available combo chains"""
	combo_definitions = {
		"fire_combo": {
			"name": "Inferno Chain",
			"cards": ["fire_damage", "burn", "area_damage"],
			"bonus_effects": {
				"damage_multiplier": 1.5,
				"energy_refund": 1
			},
			"description": "Fire spells deal 50% more damage and refund 1 energy"
		},
		"water_combo": {
			"name": "Tidal Mastery",
			"cards": ["water_damage", "freeze", "area_heal"],
			"bonus_effects": {
				"freeze_duration": 1,
				"heal_bonus": 2
			},
			"description": "Freeze lasts 1 extra turn, healing +2"
		},
		"nature_combo": {
			"name": "Life Cycle",
			"cards": ["heal", "regeneration", "buff_defense"],
			"bonus_effects": {
				"regeneration_bonus": 1,
				"defense_bonus": 1
			},
			"description": "Regeneration +1, defense buffs +1"
		},
		"shadow_combo": {
			"name": "Death Chain",
			"cards": ["sacrifice", "graveyard_summon", "life_steal"],
			"bonus_effects": {
				"sacrifice_bonus": "draw_card",
				"life_steal_bonus": 0.5
			},
			"description": "Sacrifices draw cards, life steal +50%"
		}
	}

func start_combo_chain(ability_name: String, card_data: Dictionary):
	"""Start or continue a combo chain"""
	# Check if this ability can start/continue any combo
	for combo_id in combo_definitions:
		var combo = combo_definitions[combo_id]
		var combo_cards = combo.get("cards", [])
		
		if ability_name in combo_cards:
			# Find existing active combo or start new one
			var active_combo = find_active_combo(combo_id)
			if active_combo == null:
				# Start new combo
				active_combo = {
					"combo_id": combo_id,
					"name": combo.get("name", ""),
					"cards_played": [ability_name],
					"start_time": Time.get_unix_time_from_system(),
					"timer_remaining": combo_timer_duration,
					"bonus_effects": combo.get("bonus_effects", {}),
					"completed": false
				}
				active_combos.append(active_combo)
				combo_chain_started.emit(combo.get("name", ""), 1)
				print("🔗 Combo started: ", combo.get("name", ""))
			else:
				# Continue existing combo
				if not ability_name in active_combo.cards_played:
					active_combo.cards_played.append(ability_name)
					active_combo.timer_remaining = combo_timer_duration  # Reset timer
					print("🔗 Combo continued: ", active_combo.name, " (", active_combo.cards_played.size(), "/", combo_cards.size(), ")")
					
					# Check if combo is complete
					if active_combo.cards_played.size() >= combo_cards.size():
						complete_combo_chain(active_combo)

func find_active_combo(combo_id: String) -> Dictionary:
	"""Find an active combo by ID"""
	for combo in active_combos:
		if combo.get("combo_id") == combo_id and not combo.get("completed", false):
			return combo
	return {}

func complete_combo_chain(combo: Dictionary):
	"""Complete a combo chain and apply bonus effects"""
	combo.completed = true
	var bonus_effects = combo.get("bonus_effects", {})
	
	combo_chain_completed.emit(combo.get("name", ""), bonus_effects.keys())
	print("✨ Combo completed: ", combo.get("name", ""), " - Bonus effects: ", bonus_effects)
	
	# Apply bonus effects (implementation depends on specific effects)
	apply_combo_bonus_effects(bonus_effects)

func apply_combo_bonus_effects(effects: Dictionary):
	"""Apply bonus effects from completed combos"""
	for effect_type in effects:
		var effect_value = effects[effect_type]
		print("✨ Applying combo bonus: ", effect_type, " = ", effect_value)
		# Implementation would depend on specific effect types

func update_combo_timers(delta: float):
	"""Update combo timers (call from _process)"""
	for combo in active_combos:
		if not combo.get("completed", false):
			combo.timer_remaining -= delta
			if combo.timer_remaining <= 0:
				print("⏰ Combo expired: ", combo.get("name", ""))
				combo.completed = true

# === SACRIFICE MECHANICS ===

func add_to_sacrifice_pool(card_data: Dictionary):
	"""Add a card to the sacrifice pool"""
	sacrifice_pool.append(card_data)
	print("⚰️ Card added to sacrifice pool: ", card_data.get("name", "Unknown"))

func can_sacrifice_card(card_data: Dictionary) -> bool:
	"""Check if a card can be sacrificed"""
	# Check if card is in sacrifice pool or on battlefield
	return card_data in sacrifice_pool or is_card_on_battlefield(card_data)

func sacrifice_card(sacrificed_card: Dictionary, beneficiary_card: Dictionary = {}) -> bool:
	"""Sacrifice a card for benefits"""
	if not can_sacrifice_card(sacrificed_card):
		return false
	
	# Remove from battlefield/sacrifice pool
	remove_card_from_battlefield(sacrificed_card)
	sacrifice_pool.erase(sacrificed_card)
	
	# Send to graveyard
	send_card_to_graveyard(sacrificed_card, "sacrifice")
	
	# Apply sacrifice benefits
	apply_sacrifice_benefits(sacrificed_card, beneficiary_card)
	
	sacrifice_performed.emit(sacrificed_card, beneficiary_card)
	print("⚰️ Card sacrificed: ", sacrificed_card.get("name", "Unknown"))
	return true

func apply_sacrifice_benefits(sacrificed_card: Dictionary, beneficiary_card: Dictionary):
	"""Apply benefits from sacrificing a card"""
	var sacrifice_effects = sacrificed_card.get("sacrifice_effects", [])
	for effect in sacrifice_effects:
		print("⚰️ Sacrifice effect: ", effect)
		# Implementation depends on specific sacrifice effects

# === TRANSFORM ABILITIES ===

func transform_card(original_card: Dictionary, transform_target: String) -> Dictionary:
	"""Transform a card into another card"""
	var new_card = get_transform_target_data(transform_target)
	if new_card.is_empty():
		print("❌ Transform target not found: ", transform_target)
		return {}
	
	# Replace card on battlefield
	replace_card_on_battlefield(original_card, new_card)
	
	card_transformed.emit(original_card, new_card)
	print("🔄 Card transformed: ", original_card.get("name", ""), " -> ", new_card.get("name", ""))
	
	return new_card

func get_transform_target_data(target_name: String) -> Dictionary:
	"""Get card data for transform target"""
	# This would typically load from card database
	# For now, return basic structure
	return {
		"name": target_name,
		"type": "creature",
		"energy_cost": 0,  # Transforms usually don't cost energy
		"abilities": [],
		"transformed": true
	}

# === GRAVEYARD INTERACTIONS ===

func send_card_to_graveyard(card: Dictionary, source: String = "destroyed"):
	"""Send a card to the graveyard"""
	var player_key = "player"  # Determine based on card owner
	graveyard[player_key].append(card)
	
	card_sent_to_graveyard.emit(card, source)
	print("⚰️ Card sent to graveyard: ", card.get("name", "Unknown"), " (", source, ")")
	
	# Trigger graveyard entry effects
	trigger_graveyard_entry_effects(card)

func summon_from_graveyard(card_index: int, player_key: String = "player") -> Dictionary:
	"""Summon a card from graveyard back to battlefield"""
	if card_index < 0 or card_index >= graveyard[player_key].size():
		return {}
	
	var card = graveyard[player_key][card_index]
	graveyard[player_key].remove_at(card_index)
	
	# Add back to battlefield
	battlefield[player_key].append(card)
	
	graveyard_interaction.emit("summon", [card])
	print("⚰️ Card summoned from graveyard: ", card.get("name", "Unknown"))
	
	return card

func get_graveyard_contents(player_key: String = "player") -> Array:
	"""Get contents of graveyard"""
	return graveyard[player_key].duplicate()

func trigger_graveyard_entry_effects(card: Dictionary):
	"""Trigger effects when cards enter graveyard"""
	var graveyard_effects = card.get("graveyard_effects", [])
	for effect in graveyard_effects:
		print("⚰️ Graveyard effect triggered: ", effect)

# === EXILE EFFECTS ===

func exile_card(card: Dictionary, source: String = "exiled"):
	"""Exile a card (remove from game)"""
	var player_key = "player"  # Determine based on card owner
	
	# Remove from other zones
	remove_card_from_all_zones(card)
	
	# Add to exile zone
	exile_zone[player_key].append(card)
	
	card_exiled.emit(card, source)
	print("🚫 Card exiled: ", card.get("name", "Unknown"), " (", source, ")")

func get_exile_zone_contents(player_key: String = "player") -> Array:
	"""Get contents of exile zone"""
	return exile_zone[player_key].duplicate()

func can_return_from_exile(card: Dictionary) -> bool:
	"""Check if a card can return from exile"""
	return card.get("can_return_from_exile", false)

# === UTILITY FUNCTIONS ===

func is_card_on_battlefield(card: Dictionary) -> bool:
	"""Check if a card is on the battlefield"""
	return card in battlefield.player or card in battlefield.opponent

func remove_card_from_battlefield(card: Dictionary):
	"""Remove a card from battlefield"""
	battlefield.player.erase(card)
	battlefield.opponent.erase(card)

func replace_card_on_battlefield(old_card: Dictionary, new_card: Dictionary):
	"""Replace a card on battlefield with another"""
	for player_key in battlefield:
		var index = battlefield[player_key].find(old_card)
		if index >= 0:
			battlefield[player_key][index] = new_card
			break

func remove_card_from_all_zones(card: Dictionary):
	"""Remove a card from all game zones"""
	remove_card_from_battlefield(card)
	graveyard.player.erase(card)
	graveyard.opponent.erase(card)
	sacrifice_pool.erase(card)

func get_current_player_id() -> int:
	"""Get current player ID (would be set by battle system)"""
	# This would be provided by the battle system
	return 1

func get_battlefield_contents() -> Dictionary:
	"""Get all cards on battlefield"""
	return battlefield.duplicate()

func _process(delta):
	"""Update timers and ongoing effects"""
	update_combo_timers(delta)











