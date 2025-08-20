extends Control

# Main Game Board Scene
# Handles real-time gameplay with NFC card scanning and turn management

@onready var opponent_zone = $OpponentZone
@onready var opponent_hero = $OpponentZone/OpponentHero
@onready var opponent_health = $OpponentZone/HealthBar
@onready var opponent_energy = $OpponentZone/EnergyDisplay
@onready var opponent_mana = $OpponentZone/ManaDisplay

@onready var arena_zone = $ArenaZone
@onready var arena_name = $ArenaZone/ArenaName
@onready var arena_objective = $ArenaZone/ObjectivePanel
@onready var arena_background = $ArenaZone/ArenaBackground

@onready var player_zone = $PlayerZone
@onready var player_hero = $PlayerZone/PlayerHero
@onready var player_health = $PlayerZone/HealthBar
@onready var player_energy = $PlayerZone/EnergyDisplay
@onready var player_mana = $PlayerZone/ManaDisplay

@onready var turn_info_panel = $TurnInfoPanel
@onready var current_turn_label = $TurnInfoPanel/CurrentTurn
@onready var current_phase_label = $TurnInfoPanel/CurrentPhase
@onready var turn_timer = $TurnInfoPanel/TurnTimer
@onready var phase_timer = $TurnInfoPanel/PhaseTimer

@onready var action_panel = $ActionPanel
@onready var action_instruction = $ActionPanel/ActionInstruction
@onready var nfc_scan_area = $ActionPanel/NFCScanArea
@onready var available_actions = $ActionPanel/AvailableActions

@onready var match_stats_panel = $MatchStatsPanel
@onready var cards_played_label = $MatchStatsPanel/CardsPlayed
@onready var damage_dealt_label = $MatchStatsPanel/DamageDealt
@onready var energy_used_label = $MatchStatsPanel/EnergyUsed

@onready var video_overlay = $VideoOverlay
@onready var action_video_player = $VideoOverlay/ActionVideoPlayer

var nfc_manager
var network_client
var turn_manager

# Game state
var current_game_state: Dictionary = {}
var my_team: int = 0
var is_my_turn: bool = false
var current_phase: String = ""
var nfc_scan_enabled: bool = false
var waiting_for_action: String = ""

# Match statistics
var cards_played_count: int = 0
var total_damage_dealt: int = 0
var total_energy_used: int = 0

func _ready():
	Logger.log_info("GameBoard", "Game board scene loaded")
	Global.current_scene = "GameBoard"
	
	setup_ui()
	setup_nfc()
	setup_networking()
	setup_turn_management()
	
	# Wait for match start
	wait_for_match_start()

func setup_ui():
	"""Initialize game board UI"""
	# Set arena information
	var arena = Global.current_arena
	arena_name.text = arena.get("name", "Unknown Arena")
	
	# Set player hero
	var hero = Global.selected_hero
	player_hero.get_node("HeroName").text = hero.get("name", "Unknown Hero")
	
	# Initialize stats
	update_match_stats()

func setup_nfc():
	"""Setup NFC scanning for gameplay"""
	nfc_manager = Global.get_nfc_manager()
	if nfc_manager:
		# Connect NFC signals
		if nfc_manager.has_signal("card_scanned"):
			nfc_manager.card_scanned.connect(_on_card_scanned)
		if nfc_manager.has_signal("scan_error"):
			nfc_manager.scan_error.connect(_on_nfc_error)
		
		# Start NFC monitoring
		nfc_manager.start_monitoring()

func setup_networking():
	"""Setup network client for real-time game communication"""
	network_client = Global.get_network_client()
	if network_client:
		# Connect network signals
		if network_client.has_signal("message_received"):
			network_client.message_received.connect(_on_network_message)
		if network_client.has_signal("connection_error"):
			network_client.connection_error.connect(_on_connection_error)
	
		# Ensure connected
		if network_client.has_method("connect_to_server") and not Global.server_connected:
			network_client.connect_to_server()

func setup_turn_management():
	"""Setup turn management system"""
	if not has_node("TurnManager"):
		turn_manager = preload("res://scripts/TurnManager.gd").new()
		turn_manager.name = "TurnManager"
		add_child(turn_manager)
	
	# Connect turn signals
	turn_manager.phase_changed.connect(_on_phase_changed)
	turn_manager.turn_changed.connect(_on_turn_changed)
	turn_manager.timer_updated.connect(_on_timer_updated)

func wait_for_match_start():
	"""Wait for match start message from server"""
	action_instruction.text = "Waiting for match to start..."
	nfc_scan_enabled = false

func _on_network_message(message: Dictionary):
	"""Handle real-time network messages"""
	var msg_type = message.get("type", "")
	
	match msg_type:
		"match.start":
			_on_match_start(message)
		"state.apply":
			_on_state_update(message)
		"timer.tick":
			_on_timer_tick(message)
		"card.played":
			_on_opponent_card_played(message)
		"match.end":
			_on_match_end(message)

func _on_match_start(message: Dictionary):
	"""Handle match start"""
	Logger.log_info("GameBoard", "Match started")
	
	current_game_state = message.get("full_state", {})
	my_team = message.get("your_team", 0)
	
	# Initialize game state
	update_game_display()
	
	# Start turn management
	turn_manager.start_match(current_game_state)
	
	# Enable NFC scanning
	nfc_scan_enabled = true
	action_instruction.text = "Match started! Scan cards to play."

func _on_state_update(message: Dictionary):
	"""Handle game state updates"""
	var patch = message.get("patch", {})
	Logger.log_info("GameBoard", "Applying state update", {"patch_keys": patch.keys()})
	
	# Apply patch to current state
	_apply_state_patch(patch)
	
	# Update display
	update_game_display()

func _on_timer_tick(message: Dictionary):
	"""Handle timer updates"""
	var remaining_ms = message.get("remaining_ms", 0)
	var phase = message.get("phase", "")
	
	# Update timer displays
	phase_timer.text = _format_time(remaining_ms)
	current_phase_label.text = "Phase: " + phase.capitalize()
	
	# Update timer color based on remaining time
	if remaining_ms < 10000:  # Less than 10 seconds
		phase_timer.modulate = Color.RED
	elif remaining_ms < 30000:  # Less than 30 seconds
		phase_timer.modulate = Color.YELLOW
	else:
		phase_timer.modulate = Color.WHITE

func _on_card_scanned(card_data: Dictionary):
	"""Handle NFC card scan during gameplay"""
	if not nfc_scan_enabled:
		Logger.log_warning("GameBoard", "NFC scanning disabled")
		return
	
	if not is_my_turn:
		Logger.log_warning("GameBoard", "Not your turn")
		_show_not_your_turn_feedback()
		return
	
	Logger.log_info("GameBoard", "Card scanned during gameplay", {"card": card_data.get("name")})
	
	# Validate card for current phase
	if _is_card_valid_for_phase(card_data):
		await _play_card(card_data)
	else:
		_show_invalid_card_feedback(card_data)

func _is_card_valid_for_phase(card_data: Dictionary) -> bool:
	"""Check if card can be played in current phase"""
	var category = card_data.get("category", "")
	var current_phase = current_game_state.get("phase", "")
	
	match current_phase:
		"start":
			return false  # No cards played in start phase
		"main":
			return category in ["CREATURE", "STRUCTURE", "ACTION_SLOW", "EQUIPMENT", "ENCHANTMENT", "ARTIFACT", "RITUAL"]
		"attack":
			return category in ["ACTION_FAST", "TRAP"]  # Reactions only
		"end":
			return false  # No cards played in end phase
		_:
			return false

func _play_card(card_data: Dictionary):
	"""Play a scanned card"""
	Logger.log_info("GameBoard", "Playing card", {"card": card_data.get("name")})
	
	# Determine action based on card category
	var action = _get_card_action(card_data)
	
	# Play card action video
	await _play_card_action_video(card_data, action)
	
	# Send to server
	network_client.send_card_play(card_data.get("id", ""), action)
	
	# Update local stats
	cards_played_count += 1
	update_match_stats()
	
	# Provide feedback
	_show_card_played_feedback(card_data)

func _get_card_action(card_data: Dictionary) -> String:
	"""Determine action type for card category"""
	var category = card_data.get("category", "")
	
	match category:
		"CREATURE", "STRUCTURE":
			return "summon"
		"ACTION_FAST", "ACTION_SLOW":
			return "cast"
		"EQUIPMENT":
			return "equip"
		"ENCHANTMENT":
			return "enchant"
		"ARTIFACT":
			return "deploy"
		"RITUAL":
			return "perform"
		"TRAP":
			return "set"
		_:
			return "play"

func _play_card_action_video(card_data: Dictionary, action: String):
	"""Play video for card action"""
	var video_path = "res://assets/videos/cards/actions/" + action + "_" + card_data.get("category", "").to_lower() + ".mp4"
	
	# Check for specific card video first
	var specific_video = "res://assets/videos/cards/actions/" + card_data.get("product_sku", "") + "_" + action + ".mp4"
	
	if ResourceLoader.exists(specific_video):
		video_overlay.visible = true
		action_video_player.stream = load(specific_video)
		action_video_player.play()
		Logger.log_info("GameBoard", "Playing specific card action video: " + specific_video)
	elif ResourceLoader.exists(video_path):
		video_overlay.visible = true
		action_video_player.stream = load(video_path)
		action_video_player.play()
		Logger.log_info("GameBoard", "Playing generic card action video: " + video_path)
	else:
		Logger.log_warning("GameBoard", "No action video found for: " + action)
		return
	
	# Wait for video to finish
	action_video_player.finished.connect(_on_action_video_finished, CONNECT_ONE_SHOT)
	await action_video_player.finished

func _on_action_video_finished():
	"""Handle action video completion"""
	video_overlay.visible = false
	Logger.log_info("GameBoard", "Action video finished")

func _apply_state_patch(patch: Dictionary):
	"""Apply state patch to current game state"""
	for key in patch:
		current_game_state[key] = patch[key]

func update_game_display():
	"""Update all game display elements"""
	# Update player info
	var player_data = current_game_state.get("players", {}).get(str(my_team), {})
	player_health.value = player_data.get("health", 20)
	player_energy.text = "Energy: " + str(player_data.get("energy", 0))
	
	# Update mana display
	var mana = player_data.get("mana", {})
	var mana_text = ""
	for color in mana:
		mana_text += color + ": " + str(mana[color]) + " "
	player_mana.text = mana_text
	
	# Update opponent info
	var opponent_team = 1 - my_team
	var opponent_data = current_game_state.get("players", {}).get(str(opponent_team), {})
	opponent_health.value = opponent_data.get("health", 20)
	opponent_energy.text = "Energy: " + str(opponent_data.get("energy", 0))
	
	# Update turn info
	var current_turn = current_game_state.get("turn", 1)
	var current_player = current_game_state.get("current_player", 0)
	current_phase = current_game_state.get("phase", "start")
	
	current_turn_label.text = "Turn: " + str(current_turn)
	current_phase_label.text = "Phase: " + current_phase.capitalize()
	
	# Update turn indicator
	is_my_turn = (current_player == my_team)
	_update_turn_indicator()

func _update_turn_indicator():
	"""Update UI to show whose turn it is"""
	if is_my_turn:
		action_instruction.text = "Your turn - " + _get_phase_instruction()
		action_instruction.modulate = Color.GREEN
		nfc_scan_enabled = true
	else:
		action_instruction.text = "Opponent's turn - " + current_phase.capitalize() + " phase"
		action_instruction.modulate = Color.GRAY
		nfc_scan_enabled = false

func _get_phase_instruction() -> String:
	"""Get instruction text for current phase"""
	match current_phase:
		"start":
			return "Start phase - gaining resources"
		"main":
			return "Scan cards to play (Heroes, Actions, Equipment)"
		"attack":
			return "Attack phase - declare attacks or play reactions"
		"end":
			return "End phase - resolving effects"
		_:
			return "Unknown phase"

func _show_card_played_feedback(card_data: Dictionary):
	"""Show visual feedback when card is played"""
	# Flash the action panel
	var tween = create_tween()
	action_panel.modulate = Color.CYAN
	tween.tween_property(action_panel, "modulate", Color.WHITE, 0.5)
	
	# Play success sound
	var success_audio = AudioStreamPlayer.new()
	success_audio.stream = load("res://assets/sounds/cards/card_play_success.ogg")
	add_child(success_audio)
	success_audio.play()
	success_audio.finished.connect(func(): success_audio.queue_free())
	
	# Show card name briefly
	var card_name_popup = Label.new()
	card_name_popup.text = card_data.get("name", "Card") + " played!"
	card_name_popup.position = Vector2(960, 200)  # Center top
	card_name_popup.modulate = Color.GOLD
	add_child(card_name_popup)
	
	# Animate and remove popup
	var popup_tween = create_tween()
	popup_tween.tween_property(card_name_popup, "position:y", 100, 1.0)
	popup_tween.parallel().tween_property(card_name_popup, "modulate:a", 0.0, 1.0)
	await popup_tween.finished
	card_name_popup.queue_free()

func _show_not_your_turn_feedback():
	"""Show feedback when player tries to act on opponent's turn"""
	var feedback_audio = AudioStreamPlayer.new()
	feedback_audio.stream = load("res://assets/sounds/ui/not_your_turn.ogg")
	add_child(feedback_audio)
	feedback_audio.play()
	feedback_audio.finished.connect(func(): feedback_audio.queue_free())
	
	# Flash turn indicator
	var tween = create_tween()
	turn_info_panel.modulate = Color.RED
	tween.tween_property(turn_info_panel, "modulate", Color.WHITE, 0.5)

func _show_invalid_card_feedback(card_data: Dictionary):
	"""Show feedback for invalid card plays"""
	var error_audio = AudioStreamPlayer.new()
	error_audio.stream = load("res://assets/sounds/nfc/invalid_card.ogg")
	add_child(error_audio)
	error_audio.play()
	error_audio.finished.connect(func(): error_audio.queue_free())
	
	# Show error message
	var error_popup = Label.new()
	error_popup.text = "Cannot play " + card_data.get("name", "card") + " in " + current_phase + " phase"
	error_popup.position = Vector2(960, 300)
	error_popup.modulate = Color.RED
	add_child(error_popup)
	
	# Animate and remove
	var popup_tween = create_tween()
	popup_tween.tween_property(error_popup, "modulate:a", 0.0, 2.0)
	await popup_tween.finished
	error_popup.queue_free()

func _on_opponent_card_played(message: Dictionary):
	"""Handle opponent card play"""
	var card_name = message.get("card_name", "Unknown Card")
	var action = message.get("action", "played")
	
	Logger.log_info("GameBoard", "Opponent played card", {"card": card_name, "action": action})
	
	# Show opponent action
	var opponent_action_label = Label.new()
	opponent_action_label.text = "Opponent " + action + ": " + card_name
	opponent_action_label.position = Vector2(960, 200)
	opponent_action_label.modulate = Color.ORANGE
	add_child(opponent_action_label)
	
	# Animate
	var tween = create_tween()
	tween.tween_property(opponent_action_label, "position:y", 100, 1.5)
	tween.parallel().tween_property(opponent_action_label, "modulate:a", 0.0, 1.5)
	await tween.finished
	opponent_action_label.queue_free()

func _on_phase_changed(new_phase: String):
	"""Handle phase changes"""
	Logger.log_info("GameBoard", "Phase changed to: " + new_phase)
	current_phase = new_phase
	update_game_display()

func _on_turn_changed(new_turn: int, new_player: int):
	"""Handle turn changes"""
	Logger.log_info("GameBoard", "Turn changed", {"turn": new_turn, "player": new_player})
	is_my_turn = (new_player == my_team)
	update_game_display()

func _on_timer_updated(remaining_ms: int):
	"""Handle timer updates"""
	phase_timer.text = _format_time(remaining_ms)

func _format_time(ms: int) -> String:
	"""Format milliseconds as MM:SS"""
	var seconds = ms / 1000
	var minutes = seconds / 60
	var remaining_seconds = seconds % 60
	return "%02d:%02d" % [minutes, remaining_seconds]

func update_match_stats():
	"""Update match statistics display"""
	cards_played_label.text = "Cards: " + str(cards_played_count)
	damage_dealt_label.text = "Damage: " + str(total_damage_dealt)
	energy_used_label.text = "Energy: " + str(total_energy_used)

func _on_match_end(message: Dictionary):
	"""Handle match end"""
	var result = message.get("result", {})
	Logger.log_info("GameBoard", "Match ended", {"result": result})
	
	# Stop NFC scanning
	nfc_manager.stop_monitoring()
	
	# Show match results
	transition_to_match_results(result)

func transition_to_match_results(result: Dictionary):
	"""Transition to match results scene"""
	Logger.log_info("GameBoard", "Transitioning to match results")
	
	# Store result data globally
	Global.last_match_result = result
	
	# Fade out and change scene
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	await tween.finished
	
	get_tree().change_scene_to_file("res://scenes/MatchResults.tscn")

func _on_nfc_error(error_message: String):
	"""Handle NFC scanning errors"""
	Logger.log_error("GameBoard", "NFC error during gameplay: " + error_message)

func _on_connection_error(error_message: String):
	"""Handle network connection errors"""
	Logger.log_error("GameBoard", "Network error during gameplay: " + error_message)
	
	# Show connection error overlay
	# TODO: Implement connection error UI

func _input(event):
	"""Handle input during gameplay"""
	if Global.is_development() and event.is_pressed():
		if event is InputEventKey:
			match event.keycode:
				KEY_F1:
					# Simulate card scan
					nfc_manager.force_scan_card("RADIANT-001")
				KEY_F2:
					nfc_manager.force_scan_card("AZURE-014")
				KEY_F3:
					nfc_manager.force_scan_card("VERDANT-007")
				KEY_ESCAPE:
					# Emergency exit to main menu
					get_tree().change_scene_to_file("res://scenes/MainMenu.tscn")

func _exit_tree():
	"""Cleanup when leaving game board"""
	Logger.log_info("GameBoard", "Game board scene exiting")
	
	# Stop NFC monitoring
	if nfc_manager:
		nfc_manager.stop_monitoring()
	
	# Stop videos
	if action_video_player.is_playing():
		action_video_player.stop()
