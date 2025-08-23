extends Control
class_name GameplayTest

# Gameplay Test Scene
# Simple test interface for the new gameplay system

# UI References
@onready var status_label: Label = $UI/StatusLabel
@onready var log_text: RichTextLabel = $UI/LogText
@onready var connect_button: Button = $UI/Buttons/ConnectButton
@onready var create_match_button: Button = $UI/Buttons/CreateMatchButton
@onready var join_queue_button: Button = $UI/Buttons/JoinQueueButton
@onready var leave_queue_button: Button = $UI/Buttons/LeaveQueueButton
@onready var play_card_button: Button = $UI/Buttons/PlayCardButton
@onready var advance_phase_button: Button = $UI/Buttons/AdvancePhaseButton

# Network client
var network_client: NetworkClient
var current_match_id: String = ""
var player_team: int = 0
var test_player_id: int = 5  # Use Test Player 1 (ID: 5)

func _ready():
	Logger.log_info("GameplayTest", "Gameplay test scene initialized")
	
	# Create network client
	network_client = NetworkClient.new()
	add_child(network_client)
	
	# Connect signals
	_connect_signals()
	
	# Initialize UI
	_initialize_ui()

func _connect_signals():
	"""Connect UI and network signals"""
	# Button signals
	connect_button.pressed.connect(_on_connect_pressed)
	create_match_button.pressed.connect(_on_create_match_pressed)
	join_queue_button.pressed.connect(_on_join_queue_pressed)
	leave_queue_button.pressed.connect(_on_leave_queue_pressed)
	play_card_button.pressed.connect(_on_play_card_pressed)
	advance_phase_button.pressed.connect(_on_advance_phase_pressed)
	
	# Network client signals
	network_client.connected_to_server.connect(_on_connected)
	network_client.disconnected_from_server.connect(_on_disconnected)
	network_client.match_found.connect(_on_match_found)
	network_client.match_started.connect(_on_match_started)
	network_client.match_ended.connect(_on_match_ended)
	network_client.game_state_updated.connect(_on_game_state_updated)
	network_client.card_played.connect(_on_card_played)
	network_client.phase_changed.connect(_on_phase_changed)
	network_client.timer_updated.connect(_on_timer_updated)
	network_client.error_occurred.connect(_on_error)

func _initialize_ui():
	"""Initialize UI elements"""
	status_label.text = "Disconnected"
	log_text.clear()
	
	# Disable buttons initially
	create_match_button.disabled = true
	join_queue_button.disabled = true
	leave_queue_button.disabled = true
	play_card_button.disabled = true
	advance_phase_button.disabled = true
	
	_add_log("Gameplay test ready. Click Connect to start.")

func _add_log(message: String):
	"""Add message to log"""
	var timestamp = Time.get_datetime_string_from_system()
	log_text.append_text("[" + timestamp + "] " + message + "\n")
	log_text.scroll_to_line(log_text.get_line_count() - 1)

# === BUTTON HANDLERS ===

func _on_connect_pressed():
	"""Handle connect button"""
	if network_client.is_connected:
		network_client.disconnect_from_server()
		connect_button.text = "Connect"
	else:
		_add_log("Connecting to server...")
		# Use test authentication
		network_client.authenticate("test_token", "test_console_gameplay")
		network_client.set_player_info(test_player_id)

func _on_create_match_pressed():
	"""Handle create match button"""
	_add_log("Creating test match...")
	var players = [
		{"player_id": test_player_id, "console_id": "test_console_gameplay"},
		{"player_id": 6, "console_id": "test_console_2"}  # Test Player 2 (ID: 6)
	]
	network_client.create_test_match(players)

func _on_join_queue_pressed():
	"""Handle join queue button"""
	_add_log("Joining matchmaking queue...")
	network_client.join_matchmaking_queue("1v1")

func _on_leave_queue_pressed():
	"""Handle leave queue button"""
	_add_log("Leaving matchmaking queue...")
	network_client.leave_matchmaking_queue("1v1")

func _on_play_card_pressed():
	"""Handle play card button"""
	if current_match_id == "":
		_add_log("No active match to play card in")
		return
	
	_add_log("Playing test card...")
	network_client.play_card(int(current_match_id), player_team, "test_card_radiant_001", "play")

func _on_advance_phase_pressed():
	"""Handle advance phase button"""
	if current_match_id == "":
		_add_log("No active match to advance phase")
		return
	
	_add_log("Force advancing phase...")
	network_client.force_advance_phase(int(current_match_id))

# === NETWORK SIGNAL HANDLERS ===

func _on_connected():
	"""Handle connection to server"""
	status_label.text = "Connected"
	status_label.modulate = Color.GREEN
	connect_button.text = "Disconnect"
	
	# Enable buttons
	create_match_button.disabled = false
	join_queue_button.disabled = false
	
	_add_log("✅ Connected to server!")

func _on_disconnected():
	"""Handle disconnection from server"""
	status_label.text = "Disconnected"
	status_label.modulate = Color.RED
	connect_button.text = "Connect"
	
	# Disable buttons
	create_match_button.disabled = true
	join_queue_button.disabled = true
	leave_queue_button.disabled = true
	play_card_button.disabled = true
	advance_phase_button.disabled = true
	
	_add_log("❌ Disconnected from server")

func _on_match_found(match_data: Dictionary):
	"""Handle match found"""
	current_match_id = str(match_data.get("match_id", ""))
	var opponent = match_data.get("opponent", {})
	player_team = match_data.get("your_team", 0)
	
	_add_log("🎯 Match found!")
	_add_log("   Match ID: " + current_match_id)
	_add_log("   Opponent: " + opponent.get("display_name", "Unknown"))
	_add_log("   Your team: " + str(player_team))
	
	# Send ready signal
	network_client.send_match_ready(current_match_id)

func _on_match_started(match_data: Dictionary):
	"""Handle match start"""
	_add_log("🚀 Match started!")
	
	# Enable game buttons
	play_card_button.disabled = false
	advance_phase_button.disabled = false
	
	# Disable queue buttons
	join_queue_button.disabled = true
	leave_queue_button.disabled = true

func _on_match_ended(result: Dictionary):
	"""Handle match end"""
	var winner = result.get("winner")
	var condition = result.get("condition", "unknown")
	
	_add_log("🏁 Match ended!")
	_add_log("   Condition: " + condition)
	
	if winner == player_team:
		_add_log("   🎉 YOU WIN!")
	elif winner == null:
		_add_log("   ⚖️ DRAW")
	else:
		_add_log("   💀 YOU LOSE")
	
	# Reset state
	current_match_id = ""
	player_team = 0
	
	# Reset buttons
	play_card_button.disabled = true
	advance_phase_button.disabled = true
	join_queue_button.disabled = false
	leave_queue_button.disabled = false

func _on_game_state_updated(update: Dictionary):
	"""Handle game state update"""
	var update_type = update.get("type", "")
	
	if update_type == "full_sync":
		var state = update.get("state", {})
		_add_log("🔄 Game state synchronized")
		_log_game_state(state)
	elif update_type == "state_response":
		var state = update.get("state", {})
		_add_log("📊 Game state received")
		_log_game_state(state)
	else:
		var patch = update.get("patch", {})
		_add_log("📝 Game state updated: " + str(patch.keys()))

func _log_game_state(state: Dictionary):
	"""Log key game state information"""
	_add_log("   Turn: " + str(state.get("turn", "N/A")))
	_add_log("   Phase: " + str(state.get("phase", "N/A")))
	_add_log("   Current Player: " + str(state.get("current_player", "N/A")))
	_add_log("   Your Turn: " + str(state.get("your_turn", "N/A")))

func _on_card_played(card_data: Dictionary):
	"""Handle card played"""
	var player_team_id = card_data.get("player_team", -1)
	var card_id = card_data.get("card_id", "")
	var action = card_data.get("action", "play")
	
	var player_name = "Player " + str(player_team_id)
	if player_team_id == player_team:
		player_name = "You"
	
	_add_log("🃏 " + player_name + " played: " + card_id + " (" + action + ")")

func _on_phase_changed(phase_data: Dictionary):
	"""Handle phase change"""
	var new_phase = phase_data.get("phase", "unknown")
	var turn = phase_data.get("turn", 1)
	var current_player = phase_data.get("current_player", 0)
	
	_add_log("⏭️ Phase changed to: " + new_phase.capitalize())
	_add_log("   Turn " + str(turn) + " - Player " + str(current_player))

func _on_timer_updated(timer_data: Dictionary):
	"""Handle timer update"""
	var remaining_ms = timer_data.get("remaining_ms", 0)
	var phase = timer_data.get("phase", "")
	
	# Only log every 10 seconds to avoid spam
	if remaining_ms % 10000 == 0:
		_add_log("⏰ " + phase.capitalize() + " phase: " + str(remaining_ms / 1000) + "s remaining")

func _on_error(error_message: String):
	"""Handle error"""
	_add_log("❌ Error: " + error_message)

# === INPUT HANDLING ===

func _input(event):
	"""Handle input events"""
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_1:
				# Quick connect
				if not network_client.is_connected:
					_on_connect_pressed()
			KEY_2:
				# Quick create match
				if network_client.is_connected:
					_on_create_match_pressed()
			KEY_3:
				# Quick join queue
				if network_client.is_connected:
					_on_join_queue_pressed()
			KEY_4:
				# Quick play card
				if current_match_id != "":
					_on_play_card_pressed()
			KEY_5:
				# Quick advance phase
				if current_match_id != "":
					_on_advance_phase_pressed()
			KEY_Q:
				# Simulate card scan
				network_client.simulate_card_scan("RADIANT-001")
			KEY_W:
				# Simulate card scan
				network_client.simulate_card_scan("AZURE-014")
			KEY_E:
				# Simulate card scan
				network_client.simulate_card_scan("VERDANT-007")
			KEY_R:
				# Request state sync
				if current_match_id != "":
					network_client.request_state_sync(current_match_id)
					_add_log("🔄 Requesting state sync...")

func _exit_tree():
	"""Clean up when exiting"""
	if network_client and network_client.is_connected:
		network_client.disconnect_from_server()
