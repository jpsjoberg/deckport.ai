extends Control

##
## Battle Scene - Physical Card Battle System
##
## This is the core gameplay scene where players engage in real-time card battles
## using physical NFC cards. Handles turn management, card scanning, ability execution,
## arena effects, and live video streaming between players.
##
## Key Features:
## - Real-time multiplayer battle synchronization
## - Physical NFC card scanning and validation
## - Turn-based gameplay with timer management
## - Arena effects and environmental bonuses
## - Card ability execution with video playback
## - Live video streaming between opponents
## - Comprehensive battle state management
##
## Dependencies:
## - ArenaManager: Handles arena selection and effects
## - ResourceManager: Manages mana and energy systems
## - CardAbilitiesCatalog: Card ability definitions and execution
## - CardDisplayManager: UI display for scanned cards
## - VideoBackgroundManager: Arena background videos
## - GameStateManager: Overall game state coordination
## - NetworkClient: Real-time multiplayer communication
## - NFCManager: Physical card scanning hardware interface
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2024-12-28
##

#region UI Component References
## Core UI elements for battle interface
@onready var title_label = $VBoxContainer/TitleLabel                    ## Battle scene title display
@onready var status_label = $VBoxContainer/StatusLabel                  ## Current battle status messages
@onready var arena_info_label = $VBoxContainer/ArenaInfoLabel          ## Arena name and effects info
@onready var battle_info_label = $VBoxContainer/BattleInfoLabel        ## Turn and player information
@onready var turn_timer_display = $VBoxContainer/TurnTimerDisplay      ## Turn countdown timer
@onready var card_scan_prompt = $VBoxContainer/CardScanPrompt          ## NFC card scanning instructions
@onready var pending_cards_display = $VBoxContainer/PendingCardsDisplay ## Cards waiting to be played
@onready var played_cards_display = $VBoxContainer/PlayedCardsDisplay  ## Cards played this turn
@onready var video_container = $VBoxContainer/VideoContainer           ## Container for ability videos
@onready var battle_controls = $VBoxContainer/BattleControls           ## Action buttons and controls
@onready var background_video = $BackgroundVideo                       ## Arena background video player
@onready var attack_button = $VBoxContainer/BattleControls/AttackButton ## Touch attack button
@onready var end_turn_button = $VBoxContainer/BattleControls/EndTurnButton ## Touch end turn button
@onready var forfeit_button = $VBoxContainer/BattleControls/ForfeitButton ## Touch forfeit button
@onready var scan_card1_button = $VBoxContainer/CardScanButtons/ScanCard1 ## Touch card scan 1
@onready var scan_card2_button = $VBoxContainer/CardScanButtons/ScanCard2 ## Touch card scan 2
@onready var scan_card3_button = $VBoxContainer/CardScanButtons/ScanCard3 ## Touch card scan 3
#endregion

#region Manager References
## Core system managers for battle functionality
var arena_manager                ## Handles arena effects and environmental bonuses
var resource_manager             ## Manages mana, energy, and resource generation
var card_abilities_catalog       ## Card ability definitions and execution logic
var card_display_manager         ## UI management for card information display
var video_background_manager     ## Arena background video playback
var device_connection_manager    ## Console device authentication and connection
var game_state_manager          ## Overall game state coordination and transitions
var turn_timer_manager          ## Turn timing and countdown management
var server_logger               ## Real-time logging to server for monitoring
var player_session_manager      ## Player authentication and session data
var network_client              ## Real-time multiplayer communication
var arena_video_manager         ## Arena video management  
var video_stream_manager        ## Video streaming management
var current_battle_id: String = ""  ## Current battle identifier
var opponent_console_id: String = "" ## Opponent console identifier
#endregion

#region Battle State Variables
## Core battle data and match information
var current_arena_data: Dictionary = {}      ## Active arena with effects and bonuses
var current_battle_data: Dictionary = {}     ## Current battle session data
var opponent_data: Dictionary = {}           ## Opponent player information and stats
var battle_stream_id: String = ""           ## Video streaming session identifier
var video_streaming_enabled: bool = false   ## Whether video streaming is active

## Arena system and environmental effects
var arena_effects: Dictionary = {}          ## Active arena-specific effects and modifiers
var hero_arena_bonuses: Dictionary = {}     ## Hero-specific bonuses in current arena

## Physical card battle state tracking
var is_my_turn: bool = false                ## Whether it's currently this player's turn
var my_health: int = 20                     ## Current player health points
var opponent_health: int = 20               ## Opponent's current health points
var turn_number: int = 1                    ## Current turn number in the battle
var played_cards_this_turn: Array[Dictionary] = []  ## Cards played in current turn
var scanned_card_queue: Array[Dictionary] = []      ## NFC cards scanned but not yet processed

## Player identification and session data
var player_id: int = 0                      ## Unique player identifier from server
var player_name: String = "Player"         ## Display name for this player
var selected_hero: Dictionary = {}          ## Hero card selected for this battle
#endregion

#region Initialization

##
## Initialize the battle scene and set up all required components
## Called automatically when the scene is loaded
##
func _ready():
	print("⚔️ Battle Scene initialized")
	
	_initialize_logging()
	_setup_manager_references()
	_setup_turn_timer()
	_setup_video_systems()
	_setup_card_display()
	_setup_nfc_scanning()
	_setup_network_connections()
	_initialize_battle_state()
	_setup_touch_controls()
	
	print("✅ Battle Scene setup complete")

##
## Initialize server logging for real-time monitoring
##
func _initialize_logging():
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("battle_scene_initialized", {
		"scene": "battle",
		"timestamp": Time.get_unix_time_from_system()
	})

##
## Set up references to all required manager singletons
##
func _setup_manager_references():
	arena_manager = get_node("/root/ArenaManager")
	resource_manager = get_node("/root/ResourceManager")
	card_abilities_catalog = get_node("/root/CardAbilitiesCatalog")
	card_display_manager = get_node("/root/CardDisplayManager")
	video_background_manager = get_node("/root/VideoBackgroundManager")
	device_connection_manager = get_node("/root/DeviceConnectionManager")
	game_state_manager = get_node("/root/GameStateManager")
	player_session_manager = get_node("/root/PlayerSessionManager")
	network_client = get_node("/root/NetworkClient")
	
	# Additional managers (create if not autoloaded)
	arena_video_manager = get_node("/root/ArenaVideoManager")
	if not arena_video_manager:
		arena_video_manager = preload("res://arena_video_manager.gd").new()
		add_child(arena_video_manager)
	
	video_stream_manager = get_node("/root/VideoStreamManager")
	if not video_stream_manager:
		video_stream_manager = preload("res://video_stream_manager.gd").new()
		add_child(video_stream_manager)

##
## Set up turn timer management system
##
func _setup_turn_timer():
	turn_timer_manager = preload("res://turn_timer_manager.gd").new()
	add_child(turn_timer_manager)
	print("✅ Turn timer manager initialized")

##
## Initialize video systems for arena backgrounds and ability playback
##
func _setup_video_systems():
	if video_background_manager:
		video_background_manager.setup_video_player(background_video)
		print("✅ Video background manager setup")

##
## Configure card display UI components and layout
##
func _setup_card_display():
	if card_display_manager:
		var display_components = {
			"frame_container": $VBoxContainer/CardDisplayFrame,
			"info_panel": $VBoxContainer/CardDisplayFrame/CardInfo,
			"video_player": $VBoxContainer/CardDisplayFrame/AbilityVideo,
			"name_label": $VBoxContainer/CardDisplayFrame/CardInfo/NameLabel,
			"stats_label": $VBoxContainer/CardDisplayFrame/CardInfo/StatsLabel,
			"abilities_label": $VBoxContainer/CardDisplayFrame/CardInfo/AbilitiesLabel,
			"cost_label": $VBoxContainer/CardDisplayFrame/CardInfo/CostLabel
		}
		card_display_manager.setup_display_components(display_components)
		print("✅ Card display manager setup")

##
## Connect to NFC hardware for physical card scanning
##
func _setup_nfc_scanning():
	var nfc_manager = get_node("/root/NFCManager")
	if nfc_manager:
		nfc_manager.card_scanned.connect(_on_nfc_card_scanned)
		nfc_manager.scan_error.connect(_on_nfc_scan_error)
		print("✅ Connected to NFC Manager for card scanning")
	else:
		print("⚠️ NFC Manager not found - card scanning disabled")

##
## Set up network connections and signal handlers for real-time multiplayer
##
func _setup_network_connections():
	if network_client:
		network_client.match_state_updated.connect(_on_match_state_updated)
		network_client.card_play_result.connect(_on_card_play_result)
		network_client.error_occurred.connect(_on_network_error)
		print("✅ Network client connected")
	
	# Connect resource manager signals for mana/energy updates
	if resource_manager:
		resource_manager.energy_changed.connect(_on_energy_changed)
		resource_manager.mana_changed.connect(_on_mana_changed)
		resource_manager.resource_insufficient.connect(_on_resource_insufficient)
		print("✅ Resource manager signals connected")
	
	# Connect arena manager signals for environmental effects
	if arena_manager:
		arena_manager.arena_selected.connect(_on_arena_selected)
		arena_manager.arena_effect_triggered.connect(_on_arena_effect_triggered)
		arena_manager.mana_generated.connect(_on_mana_generated)
		print("✅ Arena manager signals connected")
	
	connect_manager_signals()

##
## Initialize battle state from game session data
##
func _initialize_battle_state():
	# Get player data from session manager
	if player_session_manager and player_session_manager.is_session_valid():
		player_id = player_session_manager.player_id
		player_name = player_session_manager.display_name
		print("👤 Player: ", player_name, " (ID: ", player_id, ")")
	else:
		print("❌ No valid player session found")
		_show_error("Player authentication required")
		return
	
	# Get battle/match data from game state manager
	if game_state_manager:
		current_battle_data = game_state_manager.get_current_match()
		opponent_data = game_state_manager.get_opponent_data()
		selected_hero = game_state_manager.get_selected_hero()
		is_my_turn = game_state_manager.is_player_turn()
		
		# If no match data, this might be a direct battle scene load
		if current_battle_data.is_empty():
			print("⚠️ No match data found - this may be a test battle")
			# Create test arena for development
			if arena_manager:
				current_arena_data = arena_manager.get_random_arena()
				print("🏟️ Using test arena: ", current_arena_data.get("name", "Unknown"))
	
	# Setup UI and start battle sequence
	setup_battle_ui()
	start_battle_sequence()

##
## Setup touch controls for console touchscreen
##
func _setup_touch_controls():
	"""Connect touch button signals for console interface"""
	# Connect battle control buttons
	if attack_button:
		attack_button.pressed.connect(_on_attack_pressed)
	if end_turn_button:
		end_turn_button.pressed.connect(_on_end_turn_pressed)
	if forfeit_button:
		forfeit_button.pressed.connect(_on_forfeit_pressed)
	
	# Connect card scanning buttons
	if scan_card1_button:
		scan_card1_button.pressed.connect(func(): simulate_card_scan("CREATURE_GOBLIN_001", "Goblin Warrior"))
	if scan_card2_button:
		scan_card2_button.pressed.connect(func(): simulate_card_scan("SPELL_FIREBALL_001", "Fireball"))
	if scan_card3_button:
		scan_card3_button.pressed.connect(func(): simulate_card_scan("STRUCTURE_TOWER_001", "Guard Tower"))
	
	print("✅ Touch controls configured for console")

##
## Connect additional manager signals for video streaming and arena management
##
func connect_manager_signals():
	# Connect arena video manager signals for background video management
	if arena_video_manager:
		arena_video_manager.arena_loaded.connect(_on_arena_loaded)
		arena_video_manager.video_loaded.connect(_on_arena_video_loaded)
		print("✅ Arena video manager signals connected")
	
	# Connect video streaming manager for live opponent video
	if video_stream_manager:
		video_stream_manager.stream_started.connect(_on_video_stream_started)
		video_stream_manager.stream_joined.connect(_on_video_stream_joined)
		video_stream_manager.participant_joined.connect(_on_participant_joined)
		video_stream_manager.surveillance_detected.connect(_on_surveillance_detected)
		print("✅ Video stream manager signals connected")

	
	# Connect game state manager signals for battle coordination
	if game_state_manager:
		game_state_manager.card_scanned.connect(_on_card_scanned)
		game_state_manager.battle_ended.connect(_on_battle_ended)
		print("✅ Game state manager signals connected")
	
	# Connect turn timer manager signals for timing events
	if turn_timer_manager:
		turn_timer_manager.turn_timer_updated.connect(_on_turn_timer_updated)
		turn_timer_manager.turn_timer_expired.connect(_on_turn_timer_expired)
		turn_timer_manager.card_timer_started.connect(_on_card_timer_started)
		turn_timer_manager.card_timer_updated.connect(_on_card_timer_updated)
		turn_timer_manager.card_timer_expired.connect(_on_card_timer_expired)
		print("✅ Turn timer manager signals connected")

#endregion

#region UI Setup and Management

##
## Configure the physical card battle interface and UI elements
##
func setup_battle_ui():
	# Initialize main UI labels
	title_label.text = "PORTAL BATTLE"
	status_label.text = "Preparing for battle..."
	arena_info_label.text = ""
	
	# Configure battle information displays
	update_battle_info()
	
	# Initialize turn timer display
	turn_timer_display.text = "TURN TIMER\n\nWaiting for turn..."
	
	# Set up card scanning interface
	update_card_scan_prompt()
	
	# Initialize card status displays
	pending_cards_display.text = "PENDING CARDS\n\nNo cards scanned"
	played_cards_display.text = "PLAYED CARDS\n\nNo cards played yet"
	
	# Configure video container (hidden initially)
	video_container.visible = false
	
	# Set up interactive battle controls
	setup_battle_controls()
	
	print("🎮 Physical card battle UI configured")

func update_battle_info():
	"""Update battle information display"""
	var hero_name = selected_hero.get("name", "Unknown Hero")
	var opponent_name = opponent_data.get("player_name", "Unknown Opponent")
	var arena_name = current_arena_data.get("name", "Unknown Arena")
	
	# Get resource status
	var energy_status = resource_manager.get_energy_status() if resource_manager else {"current": 0, "maximum": 0}
	var mana_status = resource_manager.get_mana_status() if resource_manager else {"total": 0, "colors": []}
	
	# Format mana display
	var mana_text = "None"
	if mana_status.total > 0:
		var mana_parts = []
		for color_data in mana_status.colors:
			mana_parts.append(color_data.color + ":" + str(color_data.amount))
		mana_text = " ".join(mana_parts)
	
	battle_info_label.text = "BATTLE STATUS\n\n" + \
		"Arena: " + arena_name + "\n" + \
		"Your Hero: " + hero_name + " (HP: " + str(my_health) + ")\n" + \
		"Opponent: " + opponent_name + " (HP: " + str(opponent_health) + ")\n\n" + \
		"Turn: " + str(turn_number) + "\n" + \
		"⚡ Energy: " + str(energy_status.current) + "/" + str(energy_status.maximum) + "\n" + \
		"🔮 Mana: " + mana_text + "\n\n" + \
		("YOUR TURN" if is_my_turn else "OPPONENT'S TURN")

func update_card_scan_prompt():
	"""Update card scanning prompt"""
	if is_my_turn:
		var energy_status = resource_manager.get_energy_status() if resource_manager else {"current": 0}
		var mana_status = resource_manager.get_mana_status() if resource_manager else {"total": 0}
		
		if energy_status.current > 0:
			var prompt_text = "🃏 YOUR TURN\n\nScan a card to play\n"
			prompt_text += "⚡ Energy: " + str(energy_status.current) + "\n"
			if mana_status.total > 0:
				prompt_text += "🔮 Mana available\n"
			else:
				prompt_text += "🔮 No mana (arena will generate)\n"
			prompt_text += "\nOr press SPACE to attack\nPress E to end turn"
			card_scan_prompt.text = prompt_text
		else:
			card_scan_prompt.text = "⚡ NO ENERGY\n\nPress SPACE to attack\nPress E to end turn"
	else:
		card_scan_prompt.text = "⏳ OPPONENT'S TURN\n\nWaiting for opponent to play...\n\nWatch their moves on video stream"

func update_played_cards_display():
	"""Update the display of played cards"""
	if played_cards_this_turn.is_empty():
		played_cards_display.text = "PLAYED CARDS\n\nNo cards played this turn"
	else:
		var cards_text = "PLAYED CARDS THIS TURN\n\n"
		for card in played_cards_this_turn:
			var energy_cost = card.get("energy_cost", 1)
			var mana_costs = card.get("mana_cost", {})
			var cost_text = "⚡" + str(energy_cost)
			if not mana_costs.is_empty():
				cost_text += " 🔮"
				for color in mana_costs:
					cost_text += color + ":" + str(mana_costs[color]) + " "
			cards_text += "• " + card.get("name", "Unknown") + " (" + cost_text + ")\n"
		played_cards_display.text = cards_text

func update_pending_cards_display():
	"""Update the display of pending cards with timers"""
	if not turn_timer_manager:
		pending_cards_display.text = "PENDING CARDS\n\nTimer manager not available"
		return
	
	var pending_cards = turn_timer_manager.get_pending_cards()
	
	if pending_cards.is_empty():
		pending_cards_display.text = "PENDING CARDS\n\nNo cards scanned"
	else:
		var cards_text = "PENDING CARDS\n\n"
		for card in pending_cards:
			var time_left = turn_timer_manager.get_card_time_left(card.get("sku", ""))
			var is_validating = turn_timer_manager.is_card_validating(card.get("sku", ""))
			
			var status_text = "⏰ " + str(int(time_left)) + "s"
			if is_validating:
				status_text = "🔄 Validating..."
			
			cards_text += "• " + card.get("name", "Unknown") + " " + status_text + "\n"
		
		pending_cards_display.text = cards_text

func update_turn_timer_display():
	"""Update the turn timer display"""
	if not turn_timer_manager:
		turn_timer_display.text = "TURN TIMER\n\nTimer not available"
		return
	
	if not turn_timer_manager.is_turn_active():
		turn_timer_display.text = "TURN TIMER\n\nOpponent's turn"
		return
	
	var time_left = turn_timer_manager.get_turn_time_left()
	var timer_state = turn_timer_manager.current_timer_state
	var state_text = turn_timer_manager.get_timer_state_text()
	var formatted_time = turn_timer_manager.format_time(time_left)
	
	# Color-code based on timer state
	var color_tag = ""
	match timer_state:
		turn_timer_manager.TimerState.NORMAL:
			color_tag = "[color=green]"
		turn_timer_manager.TimerState.WARNING:
			color_tag = "[color=yellow]"
		turn_timer_manager.TimerState.URGENT:
			color_tag = "[color=orange]"
		turn_timer_manager.TimerState.CRITICAL:
			color_tag = "[color=red]"
	
	turn_timer_display.text = "TURN TIMER\n\n" + color_tag + formatted_time + "[/color]\n" + state_text

func setup_battle_controls():
	"""Setup battle control buttons"""
	# Clear existing controls
	for child in battle_controls.get_children():
		child.queue_free()
	
	# Video streaming toggle
	var video_toggle = Button.new()
	video_toggle.text = "Enable Video Streaming"
	video_toggle.pressed.connect(_on_video_toggle_pressed)
	battle_controls.add_child(video_toggle)
	
	# Camera toggle (if available)
	if video_stream_manager and video_stream_manager.is_camera_available():
		var camera_toggle = Button.new()
		camera_toggle.text = "Enable Camera"
		camera_toggle.pressed.connect(_on_camera_toggle_pressed)
		battle_controls.add_child(camera_toggle)
	
	# Physical card battle actions
	var attack_button = Button.new()
	attack_button.text = "Direct Attack"
	attack_button.pressed.connect(_on_attack_pressed)
	battle_controls.add_child(attack_button)
	
	var end_turn_button = Button.new()
	end_turn_button.text = "End Turn"
	end_turn_button.pressed.connect(_on_end_turn_pressed)
	battle_controls.add_child(end_turn_button)
	
	var forfeit_button = Button.new()
	forfeit_button.text = "Forfeit Battle"
	forfeit_button.pressed.connect(_on_forfeit_pressed)
	battle_controls.add_child(forfeit_button)

func start_battle_sequence():
	"""Start the complete battle sequence"""
	print("🚀 Starting battle sequence")
	
	# Initialize arena if we have one
	if not current_arena_data.is_empty():
		initialize_arena_system()
	else:
		# Select random arena for testing
		if arena_manager:
			current_arena_data = arena_manager.get_random_arena()
			initialize_arena_system()
	
	# Initialize resources for turn 1
	if resource_manager:
		var arena_mana = arena_manager.generate_turn_mana() if arena_manager else {}
		resource_manager.start_new_turn(1, arena_mana)
	
	# Setup battle ready state
	setup_battle_ready()

func request_battle_arena():
	"""Request a weighted arena for the battle"""
	status_label.text = "Selecting battle arena..."
	
	if arena_video_manager:
		# Player preferences (this would come from player profile)
		var player_preferences = {
			"preferred_themes": ["nature", "crystal", "divine"],
			"preferred_rarities": ["rare", "epic"],
			"difficulty_preference": 5,
			"player_level": 10
		}
		
		arena_video_manager.get_weighted_arena(player_preferences)
	else:
		print("❌ Arena Video Manager not available")
		status_label.text = "Error: Arena system unavailable"

func _on_arena_loaded(arena_data: Dictionary, success: bool):
	"""Handle arena loading response"""
	if success and arena_data.has("id"):
		current_arena_data = arena_data
		var arena_name = arena_data.get("name", "Unknown Arena")
		var arena_theme = arena_data.get("theme", "unknown")
		var arena_rarity = arena_data.get("rarity", "common")
		
		print("🏟️ Arena selected: ", arena_name, " (", arena_theme, " - ", arena_rarity, ")")
		
		arena_info_label.text = "Arena: " + arena_name + "\nTheme: " + arena_theme.capitalize() + "\nRarity: " + arena_rarity.capitalize()
		status_label.text = "Loading arena background..."
		
		# Load arena video background
		if arena_video_manager:
			arena_video_manager.load_arena_video(arena_data, background_video, false)
		
		server_logger.log_system_event("battle_arena_selected", {
			"arena_id": arena_data.get("id"),
			"arena_name": arena_name,
			"arena_theme": arena_theme,
			"arena_rarity": arena_rarity
		})
	else:
		print("❌ Failed to load arena")
		status_label.text = "Failed to load arena. Using default background."
		# Continue with battle anyway
		setup_battle_ready()

func _on_arena_video_loaded(arena_id: int, video_type: String, success: bool):
	"""Handle arena video loading"""
	if success:
		print("✅ Arena video loaded for arena: ", arena_id)
		status_label.text = "Arena ready! Preparing for battle..."
		
		# Arena is ready, now setup battle
		await get_tree().create_timer(2.0).timeout
		setup_battle_ready()
	else:
		print("❌ Failed to load arena video")
		status_label.text = "Arena video failed to load. Continuing with battle..."
		setup_battle_ready()

func setup_battle_ready():
	"""Setup battle when arena is ready"""
	status_label.text = "Battle arena ready!\n\nPress 'Enable Video Streaming' to connect with opponent"
	
	# Show battle controls
	battle_controls.visible = true
	
	print("⚔️ Battle ready - Arena: ", current_arena_data.get("name", "Default"))
	
	server_logger.log_system_event("battle_ready", {
		"battle_id": current_battle_id,
		"arena_id": current_arena_data.get("id", 0),
		"opponent_console_id": opponent_console_id
	})

# === VIDEO STREAMING CONTROLS ===

func _on_video_toggle_pressed():
	"""Toggle video streaming for the battle"""
	if not video_streaming_enabled:
		enable_video_streaming()
	else:
		disable_video_streaming()

func enable_video_streaming():
	"""Enable video streaming for the battle"""
	if not video_stream_manager:
		print("❌ Video Stream Manager not available")
		return
	
	print("📹 Enabling video streaming for battle")
	status_label.text = "Starting video stream..."
	
	# Setup video streaming options
	var streaming_options = {
		"camera": false,  # Start with camera off
		"screen_share": true,  # Always share screen for battles
		"audio": false  # Start with audio off
	}
	
	# Setup video display
	video_stream_manager.setup_video_display(video_container)
	video_container.visible = true
	
	# Start battle stream
	if video_stream_manager.start_battle_stream(opponent_console_id, current_battle_id, streaming_options):
		video_streaming_enabled = true
		
		# Update button text
		var video_button = battle_controls.get_child(0)
		if video_button:
			video_button.text = "Disable Video Streaming"
		
		server_logger.log_system_event("battle_video_streaming_enabled", {
			"battle_id": current_battle_id,
			"options": streaming_options
		})
	else:
		print("❌ Failed to start video streaming")
		status_label.text = "Failed to start video streaming"

func disable_video_streaming():
	"""Disable video streaming for the battle"""
	print("📹 Disabling video streaming")
	
	if video_stream_manager:
		video_stream_manager.end_current_stream()
	
	video_container.visible = false
	video_streaming_enabled = false
	
	# Update button text
	var video_button = battle_controls.get_child(0)
	if video_button:
		video_button.text = "Enable Video Streaming"
	
	status_label.text = "Video streaming disabled"
	
	server_logger.log_system_event("battle_video_streaming_disabled", {
		"battle_id": current_battle_id
	})

func _on_camera_toggle_pressed():
	"""Toggle camera for video streaming"""
	if not video_stream_manager or not video_streaming_enabled:
		return
	
	# This would send an update to the streaming server
	print("📷 Camera toggle requested (not implemented yet)")
	
	server_logger.log_system_event("battle_camera_toggle", {
		"battle_id": current_battle_id
	})

# === VIDEO STREAMING EVENTS ===

func _on_video_stream_started(stream_id: String, success: bool):
	"""Handle video stream started"""
	if success:
		battle_stream_id = stream_id
		status_label.text = "Video stream active!\nWaiting for opponent to join..."
		
		print("✅ Battle video stream started: ", stream_id)
		
		server_logger.log_system_event("battle_stream_started", {
			"battle_id": current_battle_id,
			"stream_id": stream_id
		})
	else:
		print("❌ Failed to start battle video stream")
		status_label.text = "Failed to start video stream"
		disable_video_streaming()

func _on_video_stream_joined(stream_id: String, success: bool):
	"""Handle video stream joined"""
	if success:
		battle_stream_id = stream_id
		status_label.text = "Connected to battle stream!\nBattle can begin!"
		
		print("✅ Joined battle video stream: ", stream_id)
		
		server_logger.log_system_event("battle_stream_joined", {
			"battle_id": current_battle_id,
			"stream_id": stream_id
		})
	else:
		print("❌ Failed to join battle video stream")
		status_label.text = "Failed to join video stream"

func _on_participant_joined(participant_info: Dictionary):
	"""Handle participant joining the video stream"""
	var console_id = participant_info.get("console_id", 0)
	var role = participant_info.get("role", "unknown")
	
	print("👥 Participant joined stream - Console: ", console_id, " Role: ", role)
	
	if console_id == opponent_console_id:
		status_label.text = "Opponent connected!\nBattle ready to begin!"
	
	server_logger.log_system_event("battle_participant_joined", {
		"battle_id": current_battle_id,
		"participant_info": participant_info
	})

func _on_surveillance_detected(admin_info: Dictionary):
	"""Handle admin surveillance detection"""
	print("🚨 Admin surveillance detected during battle!")
	
	# Show additional warning in battle context
	var surveillance_label = Label.new()
	surveillance_label.text = "⚠️ ADMIN MONITORING ACTIVE ⚠️"
	surveillance_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	surveillance_label.add_theme_color_override("font_color", Color.RED)
	add_child(surveillance_label)
	
	server_logger.log_system_event("battle_surveillance_detected", {
		"battle_id": current_battle_data.get("battle_id", ""),
		"admin_info": admin_info
	})

# === GAME STATE MANAGER EVENTS ===

func _on_card_scanned(card_data: Dictionary):
	"""Handle card scanned event from game state manager"""
	print("🃏 Card scanned event received: ", card_data.get("name", "Unknown"))
	
	# Update UI to show card was played
	var card_name = card_data.get("name", "Unknown")
	card_scan_prompt.text = "✅ CARD PLAYED\n\n" + card_name + "\n\nCard effects applied!"
	
	# Wait then update prompt
	await get_tree().create_timer(2.0).timeout
	update_card_scan_prompt()

func _on_battle_ended(results: Dictionary):
	"""Handle battle ended event from game state manager"""
	print("🏁 Battle ended event received")
	
	var player_won = results.get("player_won", false)
	end_battle(player_won)

# === TIMER EVENT HANDLERS ===

func _on_turn_timer_updated(time_left: float, state):
	"""Handle turn timer updates"""
	update_turn_timer_display()
	
	# Update card scan prompt based on timer state
	if state == turn_timer_manager.TimerState.CRITICAL:
		card_scan_prompt.text = "🔴 CRITICAL TIME!\n\nTurn ending in " + str(int(time_left)) + " seconds!\nMake your move NOW!"
	elif state == turn_timer_manager.TimerState.URGENT:
		card_scan_prompt.text = "🟠 HURRY UP!\n\nOnly " + str(int(time_left)) + " seconds left!\nScan cards or end turn!"

func _on_turn_timer_expired():
	"""Handle turn timer expiration"""
	print("⏰ Turn timer expired - auto-ending turn")
	
	status_label.text = "⏰ TIME'S UP! Turn ended automatically"
	card_scan_prompt.text = "⏰ TIME EXPIRED\n\nTurn ended automatically\nWaiting for opponent..."
	
	# Auto-end turn
	_on_end_turn_pressed()

func _on_card_timer_started(card_data: Dictionary, time_left: float):
	"""Handle card timer started"""
	print("🃏 Card timer started: ", card_data.get("name", "Unknown"), " - ", time_left, "s")
	
	update_pending_cards_display()
	
	# Show card scan feedback
	var card_name = card_data.get("name", "Unknown")
	card_scan_prompt.text = "🃏 CARD SCANNED!\n\n" + card_name + "\n⏰ " + str(int(time_left)) + " seconds to decide\n\nPress P to play or wait to discard"

func _on_card_timer_updated(card_data: Dictionary, time_left: float):
	"""Handle card timer updates"""
	update_pending_cards_display()
	
	# Show urgent warning for cards about to expire
	if time_left <= 3.0 and time_left > 2.0:
		var card_name = card_data.get("name", "Unknown")
		card_scan_prompt.text = "🔴 CARD EXPIRING!\n\n" + card_name + "\n⏰ " + str(int(time_left)) + " seconds left!\n\nDecide NOW or lose the card!"

func _on_card_timer_expired(card_data: Dictionary):
	"""Handle card timer expiration"""
	var card_name = card_data.get("name", "Unknown")
	print("⏰ Card timer expired: ", card_name, " - card discarded")
	
	# Remove from scanned queue if present
	for i in range(scanned_card_queue.size()):
		if scanned_card_queue[i].get("sku", "") == card_data.get("sku", ""):
			scanned_card_queue.remove_at(i)
			break
	
	# Update UI
	update_pending_cards_display()
	card_scan_prompt.text = "⏰ CARD EXPIRED!\n\n" + card_name + " was discarded\n\nScan another card or take action"
	
	# Reset prompt after a moment
	await get_tree().create_timer(2.0).timeout
	update_card_scan_prompt()

# === PENDING CARD MANAGEMENT ===

func _try_play_pending_card():
	"""Try to play the first pending card"""
	if not turn_timer_manager:
		return
	
	var pending_cards = turn_timer_manager.get_pending_cards()
	if pending_cards.is_empty():
		print("⚠️ No pending cards to play")
		return
	
	# Try to play the first pending card
	var card_data = pending_cards[0]
	var can_play = try_play_card(card_data)
	
	if can_play:
		print("✅ Played pending card: ", card_data.get("name", "Unknown"))
	else:
		print("❌ Cannot play pending card: insufficient mana")

func _discard_pending_card():
	"""Discard the first pending card"""
	if not turn_timer_manager:
		return
	
	var pending_cards = turn_timer_manager.get_pending_cards()
	if pending_cards.is_empty():
		print("⚠️ No pending cards to discard")
		return
	
	# Discard the first pending card
	var card_data = pending_cards[0]
	turn_timer_manager.discard_card(card_data)
	
	print("🗑️ Discarded pending card: ", card_data.get("name", "Unknown"))
	
	# Update UI
	update_pending_cards_display()
	card_scan_prompt.text = "🗑️ CARD DISCARDED\n\n" + card_data.get("name", "Unknown") + " was discarded\n\nScan another card or take action"
	
	# Reset prompt after a moment
	await get_tree().create_timer(2.0).timeout
	update_card_scan_prompt()

# === BATTLE ACTIONS ===

func _on_attack_pressed():
	"""Handle direct attack action"""
	if not is_my_turn:
		print("⚠️ Not your turn")
		return
	
	print("⚔️ Direct attack on opponent")
	
	# Deal 1 damage to opponent (basic attack)
	opponent_health -= 1
	
	status_label.text = "Direct attack! Dealt 1 damage to opponent"
	
	# Update UI
	update_battle_info()
	
	# Log attack
	server_logger.log_system_event("battle_action", {
		"battle_id": current_battle_data.get("battle_id", ""),
		"action": "direct_attack",
		"damage": 1,
		"turn": turn_number
	})
	
	# Check for battle end
	if opponent_health <= 0:
		end_battle(true)

func _on_end_turn_pressed():
	"""Handle end turn action"""
	if not is_my_turn:
		print("⚠️ Not your turn")
		return
	
	print("⏭️ Ending turn")
	
	# End turn timer
	if turn_timer_manager:
		turn_timer_manager.end_turn()
	
	# Tell game state manager to end turn
	if game_state_manager:
		game_state_manager.end_turn()
	
	# Update local state
	is_my_turn = false
	played_cards_this_turn.clear()
	
	# Update UI
	update_battle_info()
	update_card_scan_prompt()
	update_played_cards_display()
	update_pending_cards_display()
	update_turn_timer_display()
	
	status_label.text = "Turn ended - waiting for opponent"
	
	server_logger.log_system_event("turn_ended", {
		"battle_id": current_battle_data.get("battle_id", ""),
		"turn": turn_number,
		"cards_played": played_cards_this_turn.size()
	})
	
	# Simulate opponent turn (in real game, this comes from server)
	simulate_opponent_turn()

func _on_forfeit_pressed():
	"""Handle forfeit battle"""
	print("🏳️ Forfeiting battle")
	
	# End battle as loss
	end_battle(false)

func simulate_opponent_turn():
	"""Simulate opponent's turn for testing"""
	await get_tree().create_timer(2.0).timeout
	
	print("🤖 Opponent's turn simulation")
	
	# Random opponent action
	var action = randi() % 3
	match action:
		0:
			# Opponent plays a card
			print("🃏 Opponent played a card")
			status_label.text = "Opponent played a card!"
		1:
			# Opponent attacks
			print("⚔️ Opponent attacks")
			my_health -= 2
			status_label.text = "Opponent attacked! You took 2 damage"
		2:
			# Opponent ends turn
			print("⏭️ Opponent ended turn")
			status_label.text = "Opponent ended turn"
	
	# Check for battle end
	if my_health <= 0:
		end_battle(false)
		return
	
	# Return turn to player
	await get_tree().create_timer(2.0).timeout
	start_player_turn()

func end_battle(player_won: bool):
	"""End the battle with results"""
	print("🏁 Battle ended - Player won: ", player_won)
	
	# Update UI
	if player_won:
		status_label.text = "🏆 VICTORY! You defeated your opponent!"
		card_scan_prompt.text = "🏆 BATTLE WON!\n\nCongratulations!\nReturning to menu..."
	else:
		status_label.text = "💀 DEFEAT! Your opponent was victorious!"
		card_scan_prompt.text = "💀 BATTLE LOST!\n\nBetter luck next time!\nReturning to menu..."
	
	# End video streaming if active
	if video_streaming_enabled:
		disable_video_streaming()
	
	# Log battle end
	server_logger.log_system_event("battle_ended", {
		"battle_id": current_battle_data.get("battle_id", ""),
		"winner": "player" if player_won else "opponent",
		"player_health": my_health,
		"opponent_health": opponent_health,
		"turns": turn_number
	})
	
	# Tell game state manager about battle end
	if game_state_manager:
		var results = {
			"winner_id": player_id if player_won else opponent_data.get("player_id", 0),
			"player_won": player_won,
			"final_health": my_health,
			"turns": turn_number
		}
		current_battle_data["results"] = results
		game_state_manager.change_state(game_state_manager.GameState.BATTLE_RESULTS)
	else:
		# Wait then return to menu
		await get_tree().create_timer(5.0).timeout
		get_tree().change_scene_to_file("res://player_menu.tscn")

func _input(event):
	"""Handle input events for physical card battle"""
	if event is InputEventKey and event.pressed:
		# Card scanning simulation (for testing)
		if event.keycode == KEY_Q:
			simulate_card_scan("CREATURE_GOBLIN_001", "Goblin Warrior")
		elif event.keycode == KEY_W:
			simulate_card_scan("SPELL_FIREBALL_001", "Fireball")
		elif event.keycode == KEY_E:
			simulate_card_scan("STRUCTURE_TOWER_001", "Guard Tower")
		
		# Battle actions
		elif event.keycode == KEY_SPACE:
			_on_attack_pressed()
		elif event.keycode == KEY_E:
			_on_end_turn_pressed()
		elif event.keycode == KEY_P:
			_try_play_pending_card()
		elif event.keycode == KEY_D:
			_discard_pending_card()
		elif event.keycode == KEY_ESCAPE:
			_on_forfeit_pressed()
		
		# Video streaming controls
		elif event.keycode == KEY_V:
			_on_video_toggle_pressed()
		elif event.keycode == KEY_C:
			_on_camera_toggle_pressed()

func _on_nfc_card_scanned(card_data: Dictionary):
	"""Handle real NFC card scan from NFCManager"""
	if not is_my_turn:
		print("⚠️ Not your turn - card scan ignored")
		card_scan_prompt.text = "⚠️ NOT YOUR TURN\n\nWait for opponent to finish their turn"
		return
	
	print("🃏 Real NFC card scanned: ", card_data.get("name", "Unknown"))
	
	# Validate card is suitable for battle
	var nfc_manager = get_node("/root/NFCManager")
	if not nfc_manager.is_card_valid_for_battle(card_data):
		card_scan_prompt.text = "❌ INVALID CARD\n\nCard cannot be used in battle\nCheck activation status"
		return
	
	# Start card timer for this scanned card
	if turn_timer_manager:
		turn_timer_manager.start_card_timer(card_data)
	
	# Try to play the card through game state manager
	if game_state_manager:
		var product_sku = card_data.get("product_sku", "")
		var success = game_state_manager.scan_card(product_sku)
		if success:
			# Add to scanned queue for validation
			scanned_card_queue.append(card_data)
			
			# Show feedback
			var card_name = card_data.get("name", "Unknown Card")
			card_scan_prompt.text = "🃏 CARD SCANNED\n\n" + card_name + "\nValidating with server..."
			
			# Update pending cards display
			update_pending_cards_display()
			
			# Card is already validated by NFCManager, so we can proceed
			_on_card_validated(card_data, true)
		else:
			card_scan_prompt.text = "❌ CARD REJECTED\n\nCannot play this card now\nCheck mana cost and game state"

func _on_nfc_scan_error(error_message: String):
	"""Handle NFC scanning errors"""
	print("❌ NFC scan error: ", error_message)
	card_scan_prompt.text = "❌ NFC ERROR\n\n" + error_message + "\n\nCheck card placement"

func create_test_card_data(sku: String, name: String) -> Dictionary:
	"""Create test card data based on SKU"""
	var card_data = {
		"sku": sku,
		"name": name,
		"type": "creature",
		"mana_cost": 2,
		"attack": 2,
		"health": 2,
		"abilities": [],
		"description": "A test card for battle simulation"
	}
	
	# Customize based on card type
	if "CREATURE" in sku:
		card_data.type = "creature"
		if "GOBLIN" in sku:
			card_data.mana_cost = 1
			card_data.attack = 1
			card_data.health = 1
		elif "DRAGON" in sku:
			card_data.mana_cost = 5
			card_data.attack = 5
			card_data.health = 5
	elif "SPELL" in sku:
		card_data.type = "spell"
		card_data.mana_cost = 3
		card_data.attack = 3
		card_data.health = 0
		card_data.description = "Deal damage to target"
	elif "STRUCTURE" in sku:
		card_data.type = "structure"
		card_data.mana_cost = 2
		card_data.attack = 0
		card_data.health = 4
		card_data.description = "Defensive structure"
	
	return card_data

func simulate_card_scan(card_sku: String, card_name: String = ""):
	"""Simulate NFC card scanning for testing"""
	print("🃏 Simulating card scan: ", card_sku)
	
	# Create test card data
	var card_data = create_test_card_data(card_sku, card_name)
	
	# Process as if it was a real NFC scan
	_on_nfc_card_scanned(card_data)

func _on_card_validated(card_data: Dictionary, is_valid: bool):
	"""Handle card validation response"""
	if is_valid:
		# Card is valid, try to play it
		var can_play = try_play_card(card_data)
		if can_play:
			print("✅ Card played successfully: ", card_data.name)
		else:
			print("❌ Cannot play card: insufficient mana or invalid play")
			card_scan_prompt.text = "❌ CANNOT PLAY CARD\n\nNot enough mana or invalid play\n\nScan another card or end turn"
	else:
		print("❌ Card validation failed")
		card_scan_prompt.text = "❌ INVALID CARD\n\nCard not recognized or not owned\n\nScan a valid card"
	
	# Update UI after a moment
	await get_tree().create_timer(2.0).timeout
	update_card_scan_prompt()

func try_play_card(card_data: Dictionary) -> bool:
	"""Try to play a validated card"""
	if not resource_manager:
		print("❌ Resource manager not available")
		return false
	
	# Check if we can afford the card
	var cost_check = resource_manager.can_afford_card_cost(card_data)
	if not cost_check.can_afford:
		print("❌ Cannot afford card: ", card_data.get("name", "Unknown"))
		for resource in cost_check.missing_resources:
			print("  Missing ", resource.type, ": ", resource.required, "/", resource.available)
		return false
	
	# Stop the card timer (card is being played)
	if turn_timer_manager:
		turn_timer_manager.play_card(card_data)
	
	# Spend resources
	if not resource_manager.spend_card_resources(card_data):
		return false
	
	# Add to played cards
	played_cards_this_turn.append(card_data)
	
	# Display the card with animations
	if card_display_manager:
		var ability_videos = card_display_manager.get_ability_videos_for_card(card_data)
		card_display_manager.display_played_card(card_data, ability_videos)
	
	# Apply card effects
	apply_card_effects(card_data)
	
	# Update UI
	update_battle_info()
	update_card_scan_prompt()
	update_played_cards_display()
	update_pending_cards_display()
	
	# Log the play
	server_logger.log_nfc_scan(card_data.get("sku", ""), true, {
		"card_name": card_data.get("name", ""),
		"energy_cost": card_data.get("energy_cost", 1),
		"mana_cost": card_data.get("mana_cost", {}),
		"battle_id": current_battle_data.get("battle_id", ""),
		"turn": turn_number
	})
	
	return true

func apply_card_effects(card_data: Dictionary):
	"""Apply the effects of a played card"""
	var card_type = card_data.get("type", "creature")
	var card_name = card_data.get("name", "Unknown")
	
	match card_type:
		"creature":
			print("🦎 Creature summoned: ", card_name)
			# Creatures can attack next turn
		"spell":
			print("✨ Spell cast: ", card_name)
			var damage = card_data.get("attack", 1)
			# Apply spell damage to opponent
			opponent_health -= damage
			print("💥 Dealt ", damage, " damage to opponent")
		"structure":
			print("🏗️ Structure built: ", card_name)
			# Structures provide ongoing effects
	
	# Check for battle end conditions
	if opponent_health <= 0:
		end_battle(true)  # Player wins
	elif my_health <= 0:
		end_battle(false)  # Player loses

# === NETWORK CLIENT SIGNAL HANDLERS ===

func _on_match_state_updated(match_state: Dictionary):
	"""Handle real-time match state updates"""
	print("🔄 Match state updated: ", match_state)
	
	# Update battle state from server
	if match_state.has("players"):
		var players = match_state.players
		if players.has("0") and players.has("1"):
			# Determine which player is us
			var my_team = 0 if players["0"].get("player_id") == player_id else 1
			var opponent_team = 1 - my_team
			
			# Update health and mana
			my_health = players[str(my_team)].get("health", 20)
			opponent_health = players[str(opponent_team)].get("health", 20)
			# Energy is now managed by ResourceManager, not directly here
			
			# Update turn state
			var new_turn = match_state.get("turn", 1)
			var new_is_my_turn = match_state.get("current_player", 0) == my_team
			
			# Check if it's a new turn
			if new_turn > turn_number:
				turn_number = new_turn
				if new_is_my_turn:
					start_player_turn()
			
			is_my_turn = new_is_my_turn
			
			# Update UI
			update_battle_info()
	
	server_logger.log_system_event("match_state_updated", {
		"match_id": match_state.get("match_id", ""),
		"turn": turn_number,
		"my_health": my_health,
		"opponent_health": opponent_health
	})

func _on_card_play_result(result: Dictionary):
	"""Handle card play result from server"""
	print("🃏 Card play result: ", result)
	
	var success = result.get("success", false)
	var message = result.get("message", "")
	var card_id = result.get("card_id", "")
	
	if success:
		card_scan_prompt.text = "✅ CARD PLAYED\n\n" + message
		# Remove from scanned queue
		for i in range(scanned_card_queue.size()):
			if scanned_card_queue[i].get("product_sku", "") == card_id:
				scanned_card_queue.remove_at(i)
				break
		update_pending_cards_display()
	else:
		card_scan_prompt.text = "❌ CARD REJECTED\n\n" + message
	
	server_logger.log_system_event("card_play_result", {
		"success": success,
		"card_id": card_id,
		"message": message
	})

func _on_network_error(error_message: String):
	"""Handle network errors during battle"""
	print("❌ Network error during battle: ", error_message)
	_show_error("Network error: " + error_message)

func _show_error(error_message: String):
	"""Show error message in battle UI"""
	status_label.text = "❌ " + error_message
	card_scan_prompt.text = "❌ ERROR\n\n" + error_message

# === ARENA AND RESOURCE MANAGEMENT ===

func initialize_arena_system():
	"""Initialize the arena system for the battle"""
	if not arena_manager or current_arena_data.is_empty():
		print("⚠️ Cannot initialize arena system")
		return
	
	print("🏟️ Initializing arena: ", current_arena_data.get("name", "Unknown"))
	
	# Select the arena in arena manager
	var arena_id = current_arena_data.get("id", 1)
	arena_manager.select_arena(arena_id)
	
	# Calculate hero arena effects
	var hero_mana_affinity = selected_hero.get("mana_affinity", "AETHER")
	hero_arena_bonuses = arena_manager.calculate_hero_arena_effects(hero_mana_affinity)
	
	if not hero_arena_bonuses.is_empty():
		print("🦸 Hero arena effects: ", hero_arena_bonuses)
		# Apply hero bonuses/penalties here
		apply_hero_arena_effects()
	
	# Setup video background
	if video_background_manager:
		video_background_manager.play_arena_background(current_arena_data)
	
	# Update arena info display
	var arena_name = current_arena_data.get("name", "Unknown Arena")
	var mana_color = current_arena_data.get("mana_color", "AETHER")
	arena_info_label.text = "🏟️ Arena: " + arena_name + "\n🔮 Mana: " + mana_color

func apply_hero_arena_effects():
	"""Apply arena bonuses/penalties to hero"""
	if hero_arena_bonuses.is_empty():
		return
	
	var attack_bonus = hero_arena_bonuses.get("attack", 0)
	var defense_bonus = hero_arena_bonuses.get("defense", 0)
	var abilities = hero_arena_bonuses.get("abilities", [])
	var penalties = hero_arena_bonuses.get("penalties", [])
	
	print("🦸 Applying hero arena effects:")
	if attack_bonus != 0:
		print("  ⚔️ Attack: ", ("+" if attack_bonus > 0 else ""), attack_bonus)
	if defense_bonus != 0:
		print("  🛡️ Defense: ", ("+" if defense_bonus > 0 else ""), defense_bonus)
	if not abilities.is_empty():
		print("  ✨ Abilities: ", abilities)
	if not penalties.is_empty():
		print("  ⚠️ Penalties: ", penalties)

func start_player_turn():
	"""Start a new player turn with resource generation"""
	is_my_turn = true
	turn_number += 1
	
	print("🎯 Starting player turn ", turn_number)
	
	# Generate resources for the turn
	if resource_manager and arena_manager:
		var arena_mana = arena_manager.generate_turn_mana()
		resource_manager.start_new_turn(turn_number, arena_mana)
	
	# Start turn timer
	if turn_timer_manager:
		turn_timer_manager.start_turn()
	
	# Trigger arena effects for turn start
	if arena_manager:
		arena_manager.trigger_arena_effect("turn_start", {"turn": turn_number, "player_id": player_id})
	
	# Update UI
	update_battle_info()
	update_card_scan_prompt()
	update_turn_timer_display()
	
	status_label.text = "Your turn! Scan cards or take actions"

# === RESOURCE MANAGER SIGNAL HANDLERS ===

func _on_energy_changed(current: int, maximum: int):
	"""Handle energy changes"""
	print("⚡ Energy changed: ", current, "/", maximum)
	update_battle_info()
	update_card_scan_prompt()

func _on_mana_changed(mana_pool: Dictionary):
	"""Handle mana changes"""
	print("🔮 Mana changed: ", mana_pool)
	update_battle_info()
	update_card_scan_prompt()

func _on_resource_insufficient(resource_type: String, required: int, available: int):
	"""Handle insufficient resources"""
	print("❌ Insufficient ", resource_type, ": need ", required, ", have ", available)
	var message = "Not enough " + resource_type.replace("_", " ") + "!"
	card_scan_prompt.text = "❌ " + message.to_upper() + "\n\nRequired: " + str(required) + "\nAvailable: " + str(available)
	
	# Reset prompt after a moment
	await get_tree().create_timer(2.0).timeout
	update_card_scan_prompt()

# === ARENA MANAGER SIGNAL HANDLERS ===

func _on_arena_selected(arena_data: Dictionary):
	"""Handle arena selection"""
	print("🏟️ Arena selected signal: ", arena_data.get("name", "Unknown"))
	current_arena_data = arena_data
	initialize_arena_system()

func _on_arena_effect_triggered(effect_name: String, effect_data: Dictionary):
	"""Handle arena effects"""
	print("🏟️ Arena effect triggered: ", effect_name)
	
	# Show arena effect in UI
	status_label.text = "🏟️ Arena Effect: " + effect_name
	
	# Play arena effect video if available
	if video_background_manager:
		var clip_path = arena_manager.get_arena_clip(effect_name)
		if clip_path != "":
			video_background_manager.trigger_special_video(effect_name, 2.0)

func _on_mana_generated(color: String, amount: int):
	"""Handle mana generation from arena"""
	print("🔮 Arena generated ", amount, " ", color, " mana")
	
	# This is handled by ResourceManager, but we can show feedback
	var feedback_text = "🔮 +" + str(amount) + " " + color + " mana"
	# Could show this as a temporary overlay
