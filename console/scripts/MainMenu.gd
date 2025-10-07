extends Control
class_name MainMenu

# Main Menu Scene
# Post-login interface with match options and player info

signal match_game_requested()
signal logout_requested()

# UI References
@onready var player_name_label: Label = $UI/PlayerInfo/NameLabel
@onready var player_level_label: Label = $UI/PlayerInfo/LevelLabel
@onready var player_elo_label: Label = $UI/PlayerInfo/ELOLabel

@onready var match_game_button: Button = $UI/Actions/MatchGameButton
@onready var practice_button: Button = $UI/Actions/PracticeButton
@onready var collection_button: Button = $UI/Actions/CollectionButton
@onready var settings_button: Button = $UI/Actions/SettingsButton
@onready var logout_button: Button = $UI/Actions/LogoutButton

@onready var queue_status_panel: Panel = $UI/QueueStatus
@onready var queue_status_label: Label = $UI/QueueStatus/StatusLabel
@onready var queue_position_label: Label = $UI/QueueStatus/PositionLabel
@onready var leave_queue_button: Button = $UI/QueueStatus/LeaveQueueButton

@onready var nfc_scan_area: Panel = $UI/NFCScanArea
@onready var nfc_status_label: Label = $UI/NFCScanArea/StatusLabel
@onready var last_scanned_label: Label = $UI/NFCScanArea/LastScannedLabel

@onready var background_video: VideoStreamPlayer = $BackgroundVideo

# State
var player_data: Dictionary = {}
var is_in_queue: bool = false
var current_queue_mode: String = "1v1"
var last_scanned_card: Dictionary = {}

# Managers
var network_client: NetworkClient
var nfc_manager: NFCManager
var auth_manager
var server_logger

# Queue polling timer
var queue_poll_timer: Timer

func _ready():
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("main_menu_initialized", {})
	
	# Get manager references
	network_client = get_node("/root/NetworkClient")
	nfc_manager = get_node("/root/NFCManager")
	# auth_manager = get_node("/root/AuthManager")  # Disabled - not implemented
	
	# Connect signals
	_connect_signals()
	
	# Initialize UI
	_initialize_ui()
	
	# Setup queue polling
	_setup_queue_polling()
	
	# Start background video if available
	_setup_background_video()

func _connect_signals():
	"""Connect all necessary signals"""
	# Button signals
	match_game_button.pressed.connect(_on_match_game_pressed)
	practice_button.pressed.connect(_on_practice_pressed)
	collection_button.pressed.connect(_on_collection_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	logout_button.pressed.connect(_on_logout_pressed)
	leave_queue_button.pressed.connect(_on_leave_queue_pressed)
	
	# Network client signals
	network_client.match_found.connect(_on_match_found)
	network_client.match_started.connect(_on_match_started)
	network_client.error_occurred.connect(_on_network_error)
	network_client.connected_to_server.connect(_on_connected_to_server)
	network_client.disconnected_from_server.connect(_on_disconnected_from_server)
	
	# NFC Manager signals
	nfc_manager.card_scanned.connect(_on_card_scanned)
	nfc_manager.scan_failed.connect(_on_scan_failed)

func _initialize_ui():
	"""Initialize UI elements"""
	# Hide queue status initially
	queue_status_panel.visible = false
	
	# Initialize NFC scan area
	nfc_status_label.text = "Ready to scan cards"
	last_scanned_label.text = "No cards scanned yet"
	
	# Set initial button states
	match_game_button.disabled = false
	practice_button.disabled = true  # Not implemented yet
	collection_button.disabled = true  # Not implemented yet

func _setup_queue_polling():
	"""Setup timer for queue status polling"""
	queue_poll_timer = Timer.new()
	queue_poll_timer.wait_time = 2.0  # Poll every 2 seconds
	queue_poll_timer.timeout.connect(_poll_queue_status)
	add_child(queue_poll_timer)

func _setup_background_video():
	"""Setup background video if available"""
	if background_video and FileAccess.file_exists("res://assets/videos/main_menu_bg.mp4"):
		var video_stream = VideoStreamTheora.new()
		video_stream.file = "res://assets/videos/main_menu_bg.mp4"
		background_video.stream = video_stream
		background_video.loop = true
		background_video.play()
		server_logger.log_system_event("mainmenu_background_video_started", {})

func set_player_data(data: Dictionary):
	"""Set player information"""
	player_data = data
	
	# Update UI
	player_name_label.text = data.get("display_name", "Player")
	player_level_label.text = "Level: " + str(data.get("level", 1))
	player_elo_label.text = "ELO: " + str(data.get("elo_rating", 1000))
	
	# Set player info in network client
	network_client.set_player_info(data.get("id", 0))
	
	server_logger.log_system_event("mainmenu_player_data_set", {
		"name": data.get("display_name", "unknown"),
		"elo": data.get("elo_rating", 1000)
	})

# === BUTTON HANDLERS ===

func _on_match_game_pressed():
	"""Handle match game button press"""
	server_logger.log_system_event("mainmenu_match_game_requested", {})
	
	if is_in_queue:
		_show_message("Already in matchmaking queue!")
		return
	
	# Check if we have a valid hero card scanned
	if not _has_valid_hero():
		_show_message("Please scan a Creature or Structure card to use as your hero!")
		return
	
	# Join matchmaking queue
	_join_matchmaking_queue()

func _on_practice_pressed():
	"""Handle practice button press"""
	server_logger.log_system_event("mainmenu_practice_mode_requested", {})
	_show_message("Practice mode coming soon!")

func _on_collection_pressed():
	"""Handle collection button press"""
	server_logger.log_system_event("mainmenu_collection_requested", {})
	_show_message("Collection viewer coming soon!")

func _on_settings_pressed():
	"""Handle settings button press"""
	server_logger.log_system_event("mainmenu_settings_requested", {})
	_show_message("Settings coming soon!")

func _on_logout_pressed():
	"""Handle logout button press"""
	server_logger.log_system_event("mainmenu_logout_requested", {})
	
	# Leave queue if in one
	if is_in_queue:
		_leave_matchmaking_queue()
	
	# Disconnect from server
	network_client.disconnect_from_server()
	
	# Emit logout signal
	logout_requested.emit()

func _on_leave_queue_pressed():
	"""Handle leave queue button press"""
	_leave_matchmaking_queue()

# === MATCHMAKING ===

func _join_matchmaking_queue():
	"""Join the matchmaking queue"""
	server_logger.log_system_event("mainmenu_joining_matchmaking_queue", {"mode": current_queue_mode})
	
	# Disable match button
	match_game_button.disabled = true
	match_game_button.text = "Joining Queue..."
	
	# Join queue via network client
	network_client.join_matchmaking_queue(current_queue_mode)
	
	# Show queue status
	queue_status_panel.visible = true
	queue_status_label.text = "Joining queue..."
	queue_position_label.text = ""
	
	# Start polling for queue status
	queue_poll_timer.start()

func _leave_matchmaking_queue():
	"""Leave the matchmaking queue"""
	server_logger.log_system_event("mainmenu_leaving_matchmaking_queue", {})
	
	# Leave queue via network client
	network_client.leave_matchmaking_queue(current_queue_mode)
	
	# Update UI
	is_in_queue = false
	queue_status_panel.visible = false
	match_game_button.disabled = false
	match_game_button.text = "Match Game"
	
	# Stop polling
	queue_poll_timer.stop()

func _poll_queue_status():
	"""Poll for queue status updates"""
	if is_in_queue:
		network_client.get_queue_status(current_queue_mode)

func _has_valid_hero() -> bool:
	"""Check if we have a valid hero card scanned"""
	if last_scanned_card.is_empty():
		return false
	
	var category = last_scanned_card.get("category", "")
	return category in ["CREATURE", "STRUCTURE"]

# === NETWORK SIGNAL HANDLERS ===

func _on_connected_to_server():
	"""Handle connection to server"""
	server_logger.log_system_event("mainmenu_connected_to_server", {})
	_show_message("Connected to server!")
	
	# Enable network-dependent buttons
	match_game_button.disabled = false

func _on_disconnected_from_server():
	"""Handle disconnection from server"""
	server_logger.log_system_event("mainmenu_disconnected_from_server", {})
	_show_message("Disconnected from server!")
	
	# Disable network-dependent buttons
	match_game_button.disabled = true
	
	# Hide queue status if visible
	if is_in_queue:
		is_in_queue = false
		queue_status_panel.visible = false
		queue_poll_timer.stop()

func _on_match_found(match_data: Dictionary):
	"""Handle match found"""
	var match_id = match_data.get("match_id", "")
	var opponent = match_data.get("opponent", {})
	
	server_logger.log_system_event("mainmenu_match_found", {
		"match_id": match_id,
		"opponent": opponent.get("display_name", "unknown")
	})
	
	# Update UI
	is_in_queue = false
	queue_status_panel.visible = false
	queue_poll_timer.stop()
	
	_show_message("Match found! Opponent: " + opponent.get("display_name", "Unknown"))
	
	# Send ready signal
	network_client.send_match_ready(match_id)
	
	# Update button
	match_game_button.text = "Match Starting..."
	match_game_button.disabled = true

func _on_match_started(match_data: Dictionary):
	"""Handle match start"""
	var match_id = str(match_data.get("match_id", ""))
	var your_team = match_data.get("your_team", 0)
	
	server_logger.log_system_event("mainmenu_match_started", {
		"match_id": match_id,
		"team": your_team
	})
	
	# Transition to game board
	_transition_to_game_board(match_id, your_team, match_data)

func _on_network_error(error_message: String):
	"""Handle network error"""
	server_logger.log_error("MainMenu", "Network error", {"message": error_message})
	_show_message("Network Error: " + error_message)
	
	# Reset queue state if error during matchmaking
	if is_in_queue:
		is_in_queue = false
		queue_status_panel.visible = false
		match_game_button.disabled = false
		match_game_button.text = "Match Game"
		queue_poll_timer.stop()

# === NFC SIGNAL HANDLERS ===

func _on_card_scanned(card_data: Dictionary):
	"""Handle NFC card scan"""
	last_scanned_card = card_data
	
	var card_name = card_data.get("name", "Unknown Card")
	var card_category = card_data.get("category", "Unknown")
	
	server_logger.log_system_event("mainmenu_card_scanned", {
		"name": card_name,
		"category": card_category
	})
	
	# Update UI
	nfc_status_label.text = "Card Scanned!"
	nfc_status_label.modulate = Color.GREEN
	last_scanned_label.text = "Last: " + card_name + " (" + card_category + ")"
	
	# Check if it's a valid hero card
	if card_category in ["CREATURE", "STRUCTURE"]:
		_show_message("✨ Hero selected: " + card_name)
		match_game_button.text = "Match Game (Hero: " + card_name + ")"
	else:
		_show_message("ℹ️ Scanned: " + card_name + " (Not a hero card)")
	
	# Reset status after delay
	await get_tree().create_timer(2.0).timeout
	nfc_status_label.text = "Ready to scan cards"
	nfc_status_label.modulate = Color.WHITE

func _on_scan_failed(error: String):
	"""Handle NFC scan failure"""
	server_logger.log_error("MainMenu", "Card scan failed", {"error": error})
	
	nfc_status_label.text = "Scan Failed!"
	nfc_status_label.modulate = Color.RED
	
	# Reset status after delay
	await get_tree().create_timer(2.0).timeout
	nfc_status_label.text = "Ready to scan cards"
	nfc_status_label.modulate = Color.WHITE

# === SCENE TRANSITIONS ===

func _transition_to_game_board(match_id: String, team: int, match_data: Dictionary):
	"""Transition to game board scene"""
	server_logger.log_system_event("mainmenu_transitioning_to_game_board", {})
	
	# Load game board scene
	var game_board_scene = preload("res://scenes_backup/GameBoard.tscn")
	var game_board = game_board_scene.instantiate()
	
	# Connect completion signal
	game_board.match_completed.connect(_on_match_completed)
	
	# Start the match
	game_board.start_match(match_id, team, match_data)
	
	# Replace current scene
	get_tree().current_scene.queue_free()
	get_tree().root.add_child(game_board)
	get_tree().current_scene = game_board

func _on_match_completed(result: Dictionary):
	"""Handle match completion"""
	server_logger.log_system_event("mainmenu_match_completed", result)
	
	# Return to main menu
	_return_to_main_menu()

func _return_to_main_menu():
	"""Return to main menu from game"""
	server_logger.log_system_event("mainmenu_returning_to_main_menu", {})
	
	# Reset button state
	match_game_button.disabled = false
	match_game_button.text = "Match Game"
	
	# Reset queue state
	is_in_queue = false
	queue_status_panel.visible = false
	queue_poll_timer.stop()

# === UTILITY METHODS ===

func _show_message(message: String):
	"""Show a temporary message to the user"""
	server_logger.log_system_event("mainmenu_showing_message", {"message": message})
	
	# Create temporary label for message
	var message_label = Label.new()
	message_label.text = message
	message_label.add_theme_color_override("font_color", Color.YELLOW)
	message_label.position = Vector2(50, 50)
	add_child(message_label)
	
	# Remove after delay
	await get_tree().create_timer(3.0).timeout
	if message_label and is_instance_valid(message_label):
		message_label.queue_free()

# === INPUT HANDLING ===

func _input(event):
	"""Handle input events"""
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_Q:
				# Simulate scanning a creature card
				_simulate_card_scan("RADIANT-001")
			KEY_W:
				# Simulate scanning an enchantment card
				_simulate_card_scan("AZURE-014")
			KEY_E:
				# Simulate scanning another creature card
				_simulate_card_scan("VERDANT-007")
			KEY_M:
				# Quick match (bypass hero requirement for testing)
				if not is_in_queue:
					_join_matchmaking_queue()
			KEY_T:
				# Test functionality removed
				pass

func _simulate_card_scan(card_sku: String):
	"""Simulate NFC card scan for testing"""
	server_logger.log_system_event("mainmenu_simulating_card_scan", {"sku": card_sku})
	network_client.simulate_card_scan(card_sku)

# Test match function removed

# === CLEANUP ===

func _exit_tree():
	"""Clean up when exiting"""
	if queue_poll_timer:
		queue_poll_timer.stop()
	
	if background_video and background_video.is_playing():
		background_video.stop()
