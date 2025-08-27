extends Control

# Battle Scene - Physical card battle with video streaming
# Players scan real NFC cards to play, attack, and defend

# UI Components
@onready var title_label = $VBoxContainer/TitleLabel
@onready var status_label = $VBoxContainer/StatusLabel
@onready var arena_info_label = $VBoxContainer/ArenaInfoLabel
@onready var battle_info_label = $VBoxContainer/BattleInfoLabel
@onready var turn_timer_display = $VBoxContainer/TurnTimerDisplay
@onready var card_scan_prompt = $VBoxContainer/CardScanPrompt
@onready var pending_cards_display = $VBoxContainer/PendingCardsDisplay
@onready var played_cards_display = $VBoxContainer/PlayedCardsDisplay
@onready var video_container = $VBoxContainer/VideoContainer
@onready var battle_controls = $VBoxContainer/BattleControls
@onready var background_video = $BackgroundVideo

# Managers
var arena_video_manager
var video_stream_manager
var device_connection_manager
var game_state_manager
var turn_timer_manager
var server_logger

# Battle state
var current_arena_data: Dictionary = {}
var current_battle_data: Dictionary = {}
var opponent_data: Dictionary = {}
var battle_stream_id: String = ""
var video_streaming_enabled: bool = false

# Physical card battle state
var is_my_turn: bool = false
var my_health: int = 20
var opponent_health: int = 20
var my_mana: int = 1
var opponent_mana: int = 1
var turn_number: int = 1
var played_cards_this_turn: Array[Dictionary] = []
var scanned_card_queue: Array[Dictionary] = []

# Player data
var player_id: int = 0
var player_name: String = "Player"
var selected_hero: Dictionary = {}

func _ready():
	print("⚔️ Battle Scene initialized")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get manager references
	arena_video_manager = get_node("/root/ArenaVideoManager")
	video_stream_manager = get_node("/root/VideoStreamManager")
	device_connection_manager = get_node("/root/DeviceConnectionManager")
	game_state_manager = get_node("/root/GameStateManager")
	
	# Create turn timer manager
	turn_timer_manager = preload("res://turn_timer_manager.gd").new()
	add_child(turn_timer_manager)
	
	# Connect to NFC Manager for real card scanning
	var nfc_manager = get_node("/root/NFCManager")
	if nfc_manager:
		nfc_manager.card_scanned.connect(_on_nfc_card_scanned)
		nfc_manager.scan_error.connect(_on_nfc_scan_error)
		print("✅ Connected to NFC Manager for card scanning")
	else:
		print("⚠️ NFC Manager not found - card scanning disabled")
	
	# Get battle data from game state manager
	if game_state_manager:
		current_battle_data = game_state_manager.get_battle_data()
		opponent_data = game_state_manager.get_opponent_data()
		selected_hero = game_state_manager.get_selected_hero()
		is_my_turn = game_state_manager.is_player_turn()
		my_mana = game_state_manager.get_available_mana()
	
	# Connect signals
	connect_manager_signals()
	
	# Setup UI
	setup_battle_ui()
	
	# Load arena and start battle
	start_battle_sequence()

func connect_manager_signals():
	"""Connect signals from various managers"""
	if arena_video_manager:
		arena_video_manager.arena_loaded.connect(_on_arena_loaded)
		arena_video_manager.video_loaded.connect(_on_arena_video_loaded)
	
	if video_stream_manager:
		video_stream_manager.stream_started.connect(_on_video_stream_started)
		video_stream_manager.stream_joined.connect(_on_video_stream_joined)
		video_stream_manager.participant_joined.connect(_on_participant_joined)
		video_stream_manager.surveillance_detected.connect(_on_surveillance_detected)
	
	if game_state_manager:
		game_state_manager.card_scanned.connect(_on_card_scanned)
		game_state_manager.battle_ended.connect(_on_battle_ended)
	
	if turn_timer_manager:
		turn_timer_manager.turn_timer_updated.connect(_on_turn_timer_updated)
		turn_timer_manager.turn_timer_expired.connect(_on_turn_timer_expired)
		turn_timer_manager.card_timer_started.connect(_on_card_timer_started)
		turn_timer_manager.card_timer_updated.connect(_on_card_timer_updated)
		turn_timer_manager.card_timer_expired.connect(_on_card_timer_expired)

func setup_battle_ui():
	"""Setup the physical card battle interface"""
	title_label.text = "PORTAL BATTLE"
	status_label.text = "Preparing for battle..."
	arena_info_label.text = ""
	
	# Setup battle info display
	update_battle_info()
	
	# Setup turn timer display
	turn_timer_display.text = "TURN TIMER\n\nWaiting for turn..."
	
	# Setup card scanning prompt
	update_card_scan_prompt()
	
	# Setup pending cards display
	pending_cards_display.text = "PENDING CARDS\n\nNo cards scanned"
	
	# Setup played cards display
	played_cards_display.text = "PLAYED CARDS\n\nNo cards played yet"
	
	# Setup video container
	video_container.visible = false
	
	# Setup battle controls
	setup_battle_controls()
	
	print("🎮 Physical card battle UI configured")

func update_battle_info():
	"""Update battle information display"""
	var hero_name = selected_hero.get("name", "Unknown Hero")
	var opponent_name = opponent_data.get("player_name", "Unknown Opponent")
	
	battle_info_label.text = "BATTLE STATUS\n\n" + "Your Hero: " + hero_name + " (HP: " + str(my_health) + ")\n" + "Opponent: " + opponent_name + " (HP: " + str(opponent_health) + ")\n\n" + "Turn: " + str(turn_number) + " | Your Mana: " + str(my_mana) + "\n" + ("YOUR TURN" if is_my_turn else "OPPONENT'S TURN")

func update_card_scan_prompt():
	"""Update card scanning prompt"""
	if is_my_turn:
		if my_mana > 0:
			card_scan_prompt.text = "🃏 YOUR TURN\n\nScan a card to play\n(Mana available: " + str(my_mana) + ")\n\nOr press SPACE to attack\nPress E to end turn"
		else:
			card_scan_prompt.text = "⚡ NO MANA\n\nPress SPACE to attack\nPress E to end turn"
	else:
		card_scan_prompt.text = "⏳ OPPONENT'S TURN\n\nWaiting for opponent to play...\n\nWatch their moves on video stream"

func update_played_cards_display():
	"""Update the display of played cards"""
	if played_cards_this_turn.is_empty():
		played_cards_display.text = "PLAYED CARDS\n\nNo cards played this turn"
	else:
		var cards_text = "PLAYED CARDS THIS TURN\n\n"
		for card in played_cards_this_turn:
			cards_text += "• " + card.get("name", "Unknown") + " (Cost: " + str(card.get("mana_cost", 1)) + ")\n"
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
	
	# Generate battle ID
	current_battle_id = "battle_" + str(Time.get_unix_time_from_system()) + "_" + str(randi() % 10000)
	
	# For demo purposes, set opponent console ID
	opponent_console_id = 999  # This would come from matchmaking
	
	server_logger.log_system_event("battle_sequence_start", {
		"battle_id": current_battle_id,
		"opponent_console_id": opponent_console_id
	})
	
	# Step 1: Get weighted arena
	request_battle_arena()

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
	turn_number += 1
	my_mana = min(my_mana + 1, 10)  # Gain 1 mana per turn, max 10
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
		"turn": turn_number - 1,
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
	
	# Simulate opponent actions
	opponent_mana = min(opponent_mana + 1, 10)
	
	# Random opponent action
	var action = randi() % 3
	match action:
		0:
			# Opponent plays a card
			print("🃏 Opponent played a card")
			opponent_mana -= 2
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
	is_my_turn = true
	
	# Start player's turn timer
	if turn_timer_manager:
		turn_timer_manager.start_turn()
	
	# Update UI
	update_battle_info()
	update_card_scan_prompt()
	update_turn_timer_display()
	
	status_label.text = "Your turn! Scan cards or take actions"

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
		if event.keycode == KEY_1:
			simulate_card_scan("CREATURE_GOBLIN_001", "Goblin Warrior")
		elif event.keycode == KEY_2:
			simulate_card_scan("SPELL_FIREBALL_001", "Fireball")
		elif event.keycode == KEY_3:
			simulate_card_scan("STRUCTURE_TOWER_001", "Guard Tower")
		elif event.keycode == KEY_4:
			simulate_card_scan("CREATURE_DRAGON_001", "Fire Dragon")
		
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
	var mana_cost = card_data.get("mana_cost", 1)
	
	# Check if we have enough mana
	if my_mana < mana_cost:
		return false
	
	# Stop the card timer (card is being played)
	if turn_timer_manager:
		turn_timer_manager.play_card(card_data)
	
	# Play the card
	my_mana -= mana_cost
	played_cards_this_turn.append(card_data)
	
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
		"mana_cost": mana_cost,
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
