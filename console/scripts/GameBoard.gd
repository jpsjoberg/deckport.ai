extends Control
class_name GameBoard

# Game Board Scene
# Main gameplay interface with real-time match state and card interactions

signal match_completed(result: Dictionary)
signal card_action_performed(card_id: String, action: String)

# UI References
@onready var player_health_label: Label = $UI/PlayerStats/HealthLabel
@onready var player_energy_label: Label = $UI/PlayerStats/EnergyLabel
@onready var player_mana_container: HBoxContainer = $UI/PlayerStats/ManaContainer
@onready var opponent_health_label: Label = $UI/OpponentStats/HealthLabel
@onready var opponent_energy_label: Label = $UI/OpponentStats/EnergyLabel

@onready var turn_label: Label = $UI/TurnInfo/TurnLabel
@onready var phase_label: Label = $UI/TurnInfo/PhaseLabel
@onready var timer_label: Label = $UI/TurnInfo/TimerLabel
@onready var current_player_label: Label = $UI/TurnInfo/CurrentPlayerLabel

@onready var hand_container: HBoxContainer = $UI/Hand/CardContainer
@onready var battlefield_container: GridContainer = $UI/Battlefield/CardContainer
@onready var equipment_container: HBoxContainer = $UI/Equipment/CardContainer

@onready var play_window_indicator: Panel = $UI/PlayWindow/Indicator
@onready var play_window_label: Label = $UI/PlayWindow/Label

@onready var action_log: RichTextLabel = $UI/ActionLog/LogText
@onready var nfc_scan_prompt: Panel = $UI/NFCScanPrompt

# Game state
var current_match_id: String = ""
var player_team: int = 0
var game_state: Dictionary = {}
var is_your_turn: bool = false
var play_window_active: bool = false
var playable_card_types: Array = []

# Card UI management
var hand_cards: Array = []
var battlefield_cards: Array = []
var equipment_cards: Array = []

# Network and managers
var network_client: NetworkClient
var nfc_manager: NFCManager
var turn_manager: TurnManager

func _ready():
	Logger.log_info("GameBoard", "Game board initialized")
	
	# Get manager references
	network_client = get_node("/root/NetworkClient")
	nfc_manager = get_node("/root/NFCManager") 
	turn_manager = get_node("/root/TurnManager")
	
	# Connect signals
	_connect_signals()
	
	# Initialize UI
	_initialize_ui()

func _connect_signals():
	"""Connect all necessary signals"""
	# Network client signals
	network_client.match_started.connect(_on_match_started)
	network_client.match_ended.connect(_on_match_ended)
	network_client.game_state_updated.connect(_on_game_state_updated)
	network_client.card_played.connect(_on_card_played)
	network_client.phase_changed.connect(_on_phase_changed)
	network_client.timer_updated.connect(_on_timer_updated)
	network_client.error_occurred.connect(_on_network_error)
	
	# NFC Manager signals
	nfc_manager.card_scanned.connect(_on_card_scanned)
	nfc_manager.scan_failed.connect(_on_scan_failed)
	
	# Turn Manager signals (if using local turn management)
	if turn_manager:
		turn_manager.phase_changed.connect(_on_local_phase_changed)
		turn_manager.turn_changed.connect(_on_local_turn_changed)
		turn_manager.play_window_opened.connect(_on_play_window_opened)
		turn_manager.play_window_closed.connect(_on_play_window_closed)

func _initialize_ui():
	"""Initialize UI elements"""
	# Hide play window indicator initially
	play_window_indicator.visible = false
	nfc_scan_prompt.visible = false
	
	# Clear containers
	_clear_card_containers()
	
	# Initialize action log
	action_log.clear()
	_add_log_entry("Game board ready - waiting for match...")

func start_match(match_id: String, team: int, initial_state: Dictionary = {}):
	"""Start a new match"""
	Logger.log_info("GameBoard", "Starting match", {
		"match_id": match_id,
		"team": team
	})
	
	current_match_id = match_id
	player_team = team
	
	# Initialize game state
	if initial_state.size() > 0:
		_update_game_state(initial_state)
	else:
		# Request current state
		network_client.get_match_state(int(match_id), team)
	
	# Start turn manager if available
	if turn_manager:
		turn_manager.start_match(initial_state)
	
	_add_log_entry("Match started! You are Team " + str(team))

func _update_game_state(state: Dictionary):
	"""Update the complete game state"""
	game_state = state
	
	# Extract key information
	var turn = state.get("turn", 1)
	var phase = state.get("phase", "start")
	var current_player = state.get("current_player", 0)
	var your_turn = state.get("your_turn", false)
	
	is_your_turn = your_turn
	
	# Update UI
	_update_turn_info(turn, phase, current_player)
	_update_player_stats(state)
	_update_play_window(state.get("play_window", {}))
	_update_cards(state)
	
	Logger.log_debug("GameBoard", "Game state updated", {
		"turn": turn,
		"phase": phase,
		"your_turn": your_turn
	})

func _update_turn_info(turn: int, phase: String, current_player: int):
	"""Update turn information display"""
	turn_label.text = "Turn: " + str(turn)
	phase_label.text = "Phase: " + phase.capitalize()
	
	if current_player == player_team:
		current_player_label.text = "YOUR TURN"
		current_player_label.modulate = Color.GREEN
	else:
		current_player_label.text = "Opponent's Turn"
		current_player_label.modulate = Color.RED

func _update_player_stats(state: Dictionary):
	"""Update player and opponent stats"""
	var you = state.get("you", {})
	var opponent = state.get("opponent", {})
	
	# Player stats
	player_health_label.text = "Health: " + str(you.get("health", 20))
	player_energy_label.text = "Energy: " + str(you.get("energy", 0))
	
	# Update mana display
	_update_mana_display(you.get("mana", {}))
	
	# Opponent stats
	opponent_health_label.text = "Opponent Health: " + str(opponent.get("health", 20))
	opponent_energy_label.text = "Opponent Energy: " + str(opponent.get("energy", 0))

func _update_mana_display(mana: Dictionary):
	"""Update mana display"""
	# Clear existing mana labels
	for child in player_mana_container.get_children():
		child.queue_free()
	
	# Add mana labels for each color
	for color in mana.keys():
		var mana_label = Label.new()
		mana_label.text = color + ": " + str(mana[color])
		mana_label.add_theme_color_override("font_color", _get_mana_color(color))
		player_mana_container.add_child(mana_label)

func _get_mana_color(color_name: String) -> Color:
	"""Get color for mana display"""
	match color_name.to_upper():
		"RADIANT":
			return Color.YELLOW
		"AZURE":
			return Color.BLUE
		"VERDANT":
			return Color.GREEN
		"CRIMSON":
			return Color.RED
		"OBSIDIAN":
			return Color.PURPLE
		_:
			return Color.WHITE

func _update_play_window(play_window: Dictionary):
	"""Update play window indicator"""
	var active = play_window.get("active", false)
	var card_types = play_window.get("card_types", [])
	var remaining_ms = play_window.get("remaining_ms", 0)
	
	play_window_active = active
	playable_card_types = card_types
	
	if active and is_your_turn:
		play_window_indicator.visible = true
		play_window_label.text = "Play Window: " + str(remaining_ms / 1000) + "s"
		play_window_indicator.modulate = Color.GREEN
		
		# Show NFC scan prompt
		nfc_scan_prompt.visible = true
		
		_add_log_entry("Play window opened - scan cards to play!")
	else:
		play_window_indicator.visible = false
		nfc_scan_prompt.visible = false

func _update_cards(state: Dictionary):
	"""Update card displays"""
	var you = state.get("you", {})
	
	# Update hand
	var hand = you.get("hand", [])
	_update_card_container(hand_container, hand, "hand")
	
	# Update battlefield
	var battlefield = you.get("battlefield", [])
	_update_card_container(battlefield_container, battlefield, "battlefield")
	
	# Update equipment
	var equipment = you.get("equipment", [])
	_update_card_container(equipment_container, equipment, "equipment")

func _update_card_container(container: Node, cards: Array, location: String):
	"""Update a specific card container"""
	# Clear existing cards
	for child in container.get_children():
		child.queue_free()
	
	# Add new cards
	for card in cards:
		var card_ui = _create_card_ui(card, location)
		container.add_child(card_ui)

func _create_card_ui(card: Dictionary, location: String) -> Control:
	"""Create UI element for a card"""
	var card_panel = Panel.new()
	card_panel.custom_minimum_size = Vector2(100, 140)
	
	var vbox = VBoxContainer.new()
	card_panel.add_child(vbox)
	
	# Card name
	var name_label = Label.new()
	name_label.text = card.get("name", "Unknown")
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(name_label)
	
	# Card cost
	var cost_label = Label.new()
	var energy_cost = card.get("energy_cost", 0)
	var mana_costs = card.get("mana_costs", {})
	cost_label.text = "Cost: " + str(energy_cost)
	if mana_costs.size() > 0:
		cost_label.text += " + Mana"
	vbox.add_child(cost_label)
	
	# Card category/type
	var type_label = Label.new()
	type_label.text = card.get("category", "Unknown")
	type_label.add_theme_color_override("font_color", Color.GRAY)
	vbox.add_child(type_label)
	
	# Make clickable if in hand and playable
	if location == "hand" and _is_card_playable(card):
		card_panel.modulate = Color.GREEN
		var button = Button.new()
		button.text = "Play"
		button.pressed.connect(_on_card_play_button_pressed.bind(card))
		vbox.add_child(button)
	
	return card_panel

func _is_card_playable(card: Dictionary) -> bool:
	"""Check if a card can be played right now"""
	if not play_window_active or not is_your_turn:
		return false
	
	var card_category = card.get("category", "")
	return card_category in playable_card_types

func _clear_card_containers():
	"""Clear all card containers"""
	for child in hand_container.get_children():
		child.queue_free()
	for child in battlefield_container.get_children():
		child.queue_free()
	for child in equipment_container.get_children():
		child.queue_free()

func _add_log_entry(message: String):
	"""Add entry to action log"""
	var timestamp = Time.get_datetime_string_from_system()
	action_log.append_text("[" + timestamp + "] " + message + "\n")
	
	# Auto-scroll to bottom
	action_log.scroll_to_line(action_log.get_line_count() - 1)

# === SIGNAL HANDLERS ===

func _on_match_started(match_data: Dictionary):
	"""Handle match start"""
	var match_id = str(match_data.get("match_id", ""))
	var initial_state = match_data
	
	if match_id == current_match_id:
		_update_game_state(initial_state)
		_add_log_entry("Match officially started!")

func _on_match_ended(result: Dictionary):
	"""Handle match end"""
	var winner = result.get("winner")
	var condition = result.get("condition", "unknown")
	var description = result.get("description", "Match ended")
	
	_add_log_entry("MATCH ENDED: " + description)
	
	if winner == player_team:
		_add_log_entry("🎉 YOU WIN! 🎉")
	elif winner == null:
		_add_log_entry("⚖️ DRAW ⚖️")
	else:
		_add_log_entry("💀 YOU LOSE 💀")
	
	# Emit completion signal
	match_completed.emit(result)

func _on_game_state_updated(update: Dictionary):
	"""Handle game state update"""
	var update_type = update.get("type", "")
	
	if update_type == "full_sync":
		var state = update.get("state", {})
		_update_game_state(state)
		_add_log_entry("Game state synchronized")
	elif update_type == "state_response":
		var state = update.get("state", {})
		_update_game_state(state)
	else:
		# Partial update
		var patch = update.get("patch", {})
		_apply_state_patch(patch)

func _apply_state_patch(patch: Dictionary):
	"""Apply partial state update"""
	# Update relevant parts of game state
	for key in patch.keys():
		game_state[key] = patch[key]
	
	# Refresh UI with updated state
	_update_game_state(game_state)

func _on_card_played(card_data: Dictionary):
	"""Handle card played by any player"""
	var player_team_id = card_data.get("player_team", -1)
	var card_id = card_data.get("card_id", "")
	var action = card_data.get("action", "play")
	
	var player_name = "Player " + str(player_team_id)
	if player_team_id == player_team:
		player_name = "You"
	
	_add_log_entry(player_name + " played card: " + card_id + " (" + action + ")")
	
	# Emit signal for other systems
	card_action_performed.emit(card_id, action)

func _on_phase_changed(phase_data: Dictionary):
	"""Handle phase change"""
	var new_phase = phase_data.get("phase", "unknown")
	var turn = phase_data.get("turn", 1)
	var current_player = phase_data.get("current_player", 0)
	
	_add_log_entry("Phase changed to: " + new_phase.capitalize())
	_update_turn_info(turn, new_phase, current_player)

func _on_timer_updated(timer_data: Dictionary):
	"""Handle timer update"""
	var remaining_ms = timer_data.get("remaining_ms", 0)
	var phase = timer_data.get("phase", "")
	
	timer_label.text = "Time: " + str(remaining_ms / 1000) + "s"
	
	# Update play window timer if active
	var play_window = timer_data.get("play_window", {})
	if play_window.get("active", false):
		_update_play_window(play_window)

func _on_network_error(error_message: String):
	"""Handle network error"""
	_add_log_entry("❌ Network Error: " + error_message)
	Logger.log_error("GameBoard", "Network error", {"message": error_message})

func _on_card_scanned(card_data: Dictionary):
	"""Handle NFC card scan"""
	if not play_window_active or not is_your_turn:
		_add_log_entry("Cannot play cards right now")
		return
	
	var card_id = card_data.get("id", "")
	var card_name = card_data.get("name", "Unknown")
	var card_category = card_data.get("category", "")
	
	Logger.log_info("GameBoard", "Card scanned", {
		"id": card_id,
		"name": card_name,
		"category": card_category
	})
	
	# Check if card is playable
	if card_category in playable_card_types:
		_play_card(card_id, "play")
		_add_log_entry("✨ Played: " + card_name)
	else:
		_add_log_entry("❌ Cannot play " + card_name + " in " + game_state.get("phase", "") + " phase")

func _on_scan_failed(error: String):
	"""Handle NFC scan failure"""
	_add_log_entry("❌ Card scan failed: " + error)

func _on_card_play_button_pressed(card: Dictionary):
	"""Handle card play button press"""
	var card_id = card.get("id", "")
	_play_card(card_id, "play")

func _play_card(card_id: String, action: String):
	"""Play a card"""
	if current_match_id == "":
		Logger.log_error("GameBoard", "No active match")
		return
	
	Logger.log_info("GameBoard", "Playing card", {
		"card_id": card_id,
		"action": action
	})
	
	# Send via both HTTP and WebSocket for reliability
	network_client.play_card(int(current_match_id), player_team, card_id, action)
	network_client.send_card_play_websocket(current_match_id, card_id, action)

# === LOCAL TURN MANAGER HANDLERS ===

func _on_local_phase_changed(new_phase: String):
	"""Handle local phase change from turn manager"""
	_add_log_entry("Local phase: " + new_phase.capitalize())

func _on_local_turn_changed(new_turn: int, new_player: int):
	"""Handle local turn change from turn manager"""
	_add_log_entry("Local turn " + str(new_turn) + " - Player " + str(new_player))

func _on_play_window_opened(card_types: Array):
	"""Handle local play window opening"""
	playable_card_types = card_types
	_add_log_entry("Local play window opened for: " + str(card_types))

func _on_play_window_closed():
	"""Handle local play window closing"""
	playable_card_types = []
	_add_log_entry("Local play window closed")

# === DEBUG/ADMIN FUNCTIONS ===

func force_advance_phase():
	"""Force advance to next phase (debug)"""
	if current_match_id != "":
		network_client.force_advance_phase(int(current_match_id))
		_add_log_entry("🔧 Force advancing phase...")

func request_state_sync():
	"""Request full state synchronization"""
	if current_match_id != "":
		network_client.request_state_sync(current_match_id)
		_add_log_entry("🔄 Requesting state sync...")

func simulate_card_scan(card_sku: String):
	"""Simulate card scan for testing"""
	network_client.simulate_card_scan(card_sku)
	_add_log_entry("🧪 Simulating scan: " + card_sku)

# === INPUT HANDLING ===

func _input(event):
	"""Handle input events"""
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_Q:
				# Simulate scanning first card in hand
				if game_state.has("you") and game_state.you.has("hand"):
					var hand = game_state.you.hand
					if hand.size() > 0:
						simulate_card_scan(hand[0].get("product_sku", "RADIANT-001"))
			KEY_W:
				# Simulate scanning second card
				simulate_card_scan("AZURE-014")
			KEY_E:
				# Simulate scanning third card
				simulate_card_scan("VERDANT-007")
			KEY_F:
				# Force advance phase (debug)
				force_advance_phase()
			KEY_R:
				# Request state sync
				request_state_sync()

func cleanup():
	"""Clean up when leaving scene"""
	Logger.log_info("GameBoard", "Cleaning up game board")
	
	current_match_id = ""
	game_state = {}
	is_your_turn = false
	play_window_active = false
	
	_clear_card_containers()
	action_log.clear()
