extends Node
# class_name NetworkClient  # Commented out to avoid autoload conflict

##
## Network Client - Real-time Multiplayer Communication System
##
## This class handles all network communication between the console and server,
## including HTTP API calls for game data and WebSocket connections for real-time
## multiplayer features like matchmaking, battle synchronization, and live updates.
##
## Key Features:
## - HTTP API communication for game data and authentication
## - WebSocket real-time communication for multiplayer features
## - Automatic reconnection and error handling
## - Match state synchronization between players
## - Matchmaking queue management
## - Card play validation and broadcasting
## - Connection state management with fallback mechanisms
##
## Network Architecture:
## - HTTP API (Port 8002): Game data, authentication, card validation
## - WebSocket (Port 8003): Real-time multiplayer, matchmaking, live updates
##
## Dependencies:
## - Server Logger: Network event logging
## - Game State Manager: Local state synchronization
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2024-12-28
##

#region Network Signals
## Emitted when successfully connected to the server
signal connected_to_server()
## Emitted when disconnected from the server
signal disconnected_from_server()
## Emitted when matchmaking finds a match
signal match_found(match_data: Dictionary)
## Emitted when a match begins
signal match_started(game_state: Dictionary)
## Emitted when a match concludes
signal match_ended(result: Dictionary)
## Emitted when game state is updated during battle
signal game_state_updated(state: Dictionary)
## Emitted when a card is played by any player
signal card_played(card_data: Dictionary)
## Emitted when battle phase changes (start, main, attack, end)
signal phase_changed(phase_data: Dictionary)
## Emitted when turn or battle timer updates
signal timer_updated(timer_data: Dictionary)
## Emitted when a network error occurs
signal error_occurred(error_message: String)
#endregion

#region Server Configuration
## Network endpoints and connection settings
var server_url: String = "https://deckport.ai"    ## HTTP API endpoint
var websocket_url: String = "ws://127.0.0.1:8004"   ## WebSocket real-time endpoint
var api_token: String = ""                          ## Authentication token
var device_uid: String = ""                         ## Console device identifier
var player_id: int = 0                             ## Current player ID
var current_match_id: String = ""                  ## Active match identifier
#endregion

#region Network Components
## Core networking objects and connection management
var http_client: HTTPRequest    ## HTTP client for API calls
var websocket: WebSocketPeer   ## WebSocket for real-time communication
#endregion

#region Connection State
## Network connection status and retry management
var is_network_connected: bool = false    ## Whether connected to server
var is_in_match: bool = false            ## Whether currently in an active match
var reconnect_attempts: int = 0          ## Current reconnection attempt count
var max_reconnect_attempts: int = 5      ## Maximum reconnection attempts before giving up
var server_logger                       ## Server logging instance
#endregion

func _ready():
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("network_client_initialized", {})
	
	# Create HTTP client
	http_client = HTTPRequest.new()
	add_child(http_client)
	http_client.request_completed.connect(_on_http_request_completed)
	
	# Initialize WebSocket
	websocket = WebSocketPeer.new()

func _process(_delta):
	# Poll WebSocket
	if websocket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		websocket.poll()
		
		# Handle WebSocket state
		var state = websocket.get_ready_state()
		if state == WebSocketPeer.STATE_OPEN:
			if not is_network_connected:
				is_network_connected = true
				connected_to_server.emit()
				server_logger.log_system_event("NetworkClient", "WebSocket connected")
			
			# Process messages
			while websocket.get_available_packet_count():
				var packet = websocket.get_packet()
				var message_text = packet.get_string_from_utf8()
				_handle_websocket_message(message_text)
		
		elif state == WebSocketPeer.STATE_CLOSED:
			if is_network_connected:
				is_network_connected = false
				disconnected_from_server.emit()
				server_logger.log_error("NetworkClient", "WebSocket disconnected")
				_attempt_reconnect()

# === AUTHENTICATION ===

func authenticate_with_managers():
	"""Authenticate using device and player session managers"""
	# Get device connection manager
	var device_manager = get_node("/root/DeviceConnectionManager")
	if not device_manager:
		server_logger.log_error("NetworkClient", "Device connection manager not found")
		error_occurred.emit("Device authentication not available")
		return
	
	# Get player session manager
	var player_manager = get_node("/root/PlayerSessionManager")
	if not player_manager:
		server_logger.log_error("NetworkClient", "Player session manager not found")
		error_occurred.emit("Player authentication not available")
		return
	
	# Check if both are authenticated
	if not device_manager.is_authenticated():
		server_logger.log_error("NetworkClient", "Device not authenticated")
		error_occurred.emit("Device authentication required")
		return
	
	if not player_manager.is_session_valid():
		server_logger.log_error("NetworkClient", "Player not authenticated")
		error_occurred.emit("Player authentication required")
		return
	
	# Use player JWT for WebSocket connection (includes player identity)
	api_token = player_manager.player_jwt
	device_uid = device_manager.get_device_uid()
	player_id = player_manager.player_id
	
	server_logger.log_system_event("NetworkClient", "Authenticating with server", {
		"device_uid": device_uid,
		"player_id": player_id
	})
	
	# Connect to WebSocket with player authentication
	var headers = ["Authorization: Bearer " + api_token]
	var error = websocket.connect_to_url(websocket_url, headers)
	
	if error != OK:
		server_logger.log_error("NetworkClient", "Failed to connect WebSocket", {"error": error})
		error_occurred.emit("Failed to connect to server")

func authenticate(token: String, device_id: String):
	"""Legacy authenticate method - use authenticate_with_managers() instead"""
	api_token = token
	device_uid = device_id
	
	server_logger.log_system_event("NetworkClient", "Legacy authentication")
	
	# Connect to WebSocket with authentication
	var headers = ["Authorization: Bearer " + api_token]
	var error = websocket.connect_to_url(websocket_url, headers)
	
	if error != OK:
		server_logger.log_error("NetworkClient", "Failed to connect WebSocket", {"error": error})
		error_occurred.emit("Failed to connect to server")

# === MATCHMAKING ===

func join_matchmaking_queue(mode: String = "1v1"):
	"""Join the matchmaking queue"""
	server_logger.log_system_event("matchmaking_queue_joined", {"mode": mode})
	
	var data = {
		"player_id": player_id,
		"console_id": device_uid,
		"mode": mode
	}
	
	_make_api_request("POST", "/v1/gameplay/queue/join", data, "_on_queue_join_response")

func leave_matchmaking_queue(mode: String = "1v1"):
	"""Leave the matchmaking queue"""
	server_logger.log_system_event("NetworkClient", "Leaving matchmaking queue")
	
	var data = {
		"player_id": player_id,
		"mode": mode
	}
	
	_make_api_request("POST", "/v1/gameplay/queue/leave", data, "_on_queue_leave_response")

func get_queue_status(mode: String = "1v1"):
	"""Get current queue status"""
	var url = "/v1/gameplay/queue/status?player_id=" + str(player_id) + "&mode=" + mode
	_make_api_request("GET", url, {}, "_on_queue_status_response")

# === MATCH MANAGEMENT ===

# Test function removed - use create_match instead

func start_match(match_id: int):
	"""Start a match"""
	server_logger.log_system_event("networkclient_starting_match", {"match_id": match_id})
	
	var url = "/v1/gameplay/matches/" + str(match_id) + "/start"
	_make_api_request("POST", url, {}, "_on_match_start_response")

func get_match_state(match_id: int, team: int = -1):
	"""Get current match state"""
	var url = "/v1/gameplay/matches/" + str(match_id) + "/state"
	if team >= 0:
		url += "?team=" + str(team)
	
	_make_api_request("GET", url, {}, "_on_match_state_response")

func send_match_ready(match_id: String):
	"""Send ready signal for match"""
	if not is_network_connected:
		server_logger.log_error("NetworkClient", "Not connected to server")
		return
	
	var message = {
		"type": "match.ready",
		"match_id": match_id
	}
	
	_send_websocket_message(message)

# === GAMEPLAY ACTIONS ===

func play_card(match_id: int, player_team: int, card_id: String, action: String = "play", target: String = ""):
	"""Play a card in the current match"""
	server_logger.log_system_event("networkclient_playing_card", {
		"match_id": match_id,
		"card_id": card_id,
		"action": action
	})
	
	var data = {
		"player_team": player_team,
		"card_id": card_id,
		"action": action
	}
	
	if target != "":
		data["target"] = target
	
	var url = "/v1/gameplay/matches/" + str(match_id) + "/play-card"
	_make_api_request("POST", url, data, "_on_card_play_response")

func send_card_play_websocket(match_id: String, card_id: String, action: String, target: String = ""):
	"""Send card play via WebSocket for real-time response"""
	if not is_network_connected:
		server_logger.log_error("NetworkClient", "Not connected to server")
		return
	
	var message = {
		"type": "card.play",
		"match_id": match_id,
		"card_id": card_id,
		"action": action,
		"client_timestamp": Time.get_datetime_string_from_system()
	}
	
	if target != "":
		message["target"] = target
	
	_send_websocket_message(message)

func request_state_sync(match_id: String):
	"""Request full state synchronization"""
	if not is_network_connected:
		server_logger.log_error("NetworkClient", "Not connected to server")
		return
	
	var message = {
		"type": "sync.request",
		"match_id": match_id
	}
	
	_send_websocket_message(message)

# === UTILITY FUNCTIONS ===

func force_advance_phase(match_id: int):
	"""Force advance to next phase (admin)"""
	server_logger.log_system_event("networkclient_force_advancing_phase", {"match_id": match_id})
	
	var url = "/v1/gameplay/matches/" + str(match_id) + "/advance-phase"
	_make_api_request("POST", url, {}, "_on_phase_advance_response")

func end_match(match_id: int, result: Dictionary = {}):
	"""End a match (admin)"""
	server_logger.log_system_event("networkclient_ending_match", {"match_id": match_id})
	
	var data = {"result": result}
	var url = "/v1/gameplay/matches/" + str(match_id) + "/end"
	_make_api_request("POST", url, data, "_on_match_end_response")

func get_active_matches():
	"""Get list of active matches"""
	_make_api_request("GET", "/v1/gameplay/matches/active", {}, "_on_active_matches_response")

# === CARD SCANNING SIMULATION ===

func simulate_card_scan(card_sku: String):
	"""Simulate NFC card scan (for development)"""
	server_logger.log_system_event("networkclient_simulating_card_scan", {"sku": card_sku})
	
	# Get card data from catalog
	var url = "/v1/catalog/cards/" + card_sku
	_make_api_request("GET", url, {}, "_on_card_scan_response")

# === PRIVATE METHODS ===

func _get_authenticated_headers() -> Array[String]:
	"""Get authentication headers using session managers"""
	var headers = ["Content-Type: application/json"]
	
	# Get player session manager for player JWT
	var player_manager = get_node("/root/PlayerSessionManager")
	if player_manager and player_manager.is_session_valid():
		headers.append("Authorization: Bearer " + player_manager.player_jwt)
	
	# Get device manager for device UID
	var device_manager = get_node("/root/DeviceConnectionManager")
	if device_manager:
		headers.append("X-Device-UID: " + device_manager.get_device_uid())
	
	return headers

func _make_api_request(method: String, endpoint: String, data: Dictionary, callback: String):
	"""Make HTTP API request"""
	var url = server_url + endpoint
	
	# Get authentication headers from session managers
	var headers = _get_authenticated_headers()
	
	# Fallback to legacy token if managers not available
	if headers.is_empty():
		headers = [
			"Content-Type: application/json",
			"Authorization: Bearer " + api_token
		]
	
	var json_data = ""
	if data != null:
		json_data = JSON.stringify(data)
	
	server_logger.log_system_event("networkclient_api_request", {
		"method": method,
		"url": url,
		"data": json_data
	})
	
	# Store callback for response handling
	http_client.set_meta("callback", callback)
	http_client.set_meta("endpoint", endpoint)
	
	var error
	if method == "GET":
		error = http_client.request(url, headers)
	else:
		error = http_client.request(url, headers, HTTPClient.METHOD_POST, json_data)
	
	if error != OK:
		server_logger.log_error("NetworkClient", "HTTP request failed", {"error": error})
		error_occurred.emit("Network request failed")

func _send_websocket_message(message: Dictionary):
	"""Send message via WebSocket"""
	if websocket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		server_logger.log_error("NetworkClient", "WebSocket not connected")
		return
	
	var json_string = JSON.stringify(message)
	var error = websocket.send_text(json_string)
	
	if error != OK:
		server_logger.log_error("NetworkClient", "Failed to send WebSocket message", {"error": error})
	else:
		server_logger.log_system_event("NetworkClient", "Sent WebSocket message", message)

func _handle_websocket_message(message_text: String):
	"""Handle incoming WebSocket message"""
	var json = JSON.new()
	var parse_result = json.parse(message_text)
	
	if parse_result != OK:
		server_logger.log_error("NetworkClient", "Failed to parse WebSocket message", {"text": message_text})
		return
	
	var message = json.data
	var msg_type = message.get("type", "")
	
	server_logger.log_system_event("networkclient_received_websocket_message", {"type": msg_type})
	
	match msg_type:
		"match.found":
			_handle_match_found(message)
		"match.start":
			_handle_match_start(message)
		"match.end":
			_handle_match_end(message)
		"state.apply":
			_handle_state_update(message)
		"card.played":
			_handle_card_played(message)
		"timer.tick":
			_handle_timer_tick(message)
		"sync.snapshot":
			_handle_sync_snapshot(message)
		"error":
			_handle_error_message(message)
		_:
			server_logger.log_error("NetworkClient", "Unknown WebSocket message type", {"type": msg_type})

func _handle_match_found(message: Dictionary):
	"""Handle match found message"""
	server_logger.log_system_event("NetworkClient", "Match found", message)
	current_match_id = message.get("match_id", "")
	match_found.emit(message)

func _handle_match_start(message: Dictionary):
	"""Handle match start message"""
	server_logger.log_system_event("networkclient_match_started", {"match_id": message.get("match_id")})
	is_in_match = true
	match_started.emit(message)

func _handle_match_end(message: Dictionary):
	"""Handle match end message"""
	server_logger.log_system_event("NetworkClient", "Match ended", message.get("result", {}))
	is_in_match = false
	current_match_id = ""
	match_ended.emit(message)

func _handle_state_update(message: Dictionary):
	"""Handle game state update"""
	var patch = message.get("patch", {})
	server_logger.log_system_event("NetworkClient", "Game state updated", patch)
	
	# Check for phase changes
	if "phase" in patch:
		phase_changed.emit(patch)
	
	game_state_updated.emit(message)

func _handle_card_played(message: Dictionary):
	"""Handle card played message"""
	server_logger.log_system_event("networkclient_card_played", {
		"player": message.get("player_team"),
		"card": message.get("card_id")
	})
	card_played.emit(message)

func _handle_timer_tick(message: Dictionary):
	"""Handle timer tick message"""
	timer_updated.emit(message)

func _handle_sync_snapshot(message: Dictionary):
	"""Handle full state synchronization"""
	server_logger.log_system_event("networkclient_received_state_sync")
	var state_data = message.get("full_state", {})
	game_state_updated.emit({"type": "full_sync", "state": state_data})

func _handle_error_message(message: Dictionary):
	"""Handle error message from server"""
	var error_msg = message.get("message", "Unknown error")
	server_logger.log_error("NetworkClient", "Server error", message)
	error_occurred.emit(error_msg)

# === HTTP RESPONSE HANDLERS ===

func _on_http_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP request completion"""
	var callback = http_client.get_meta("callback", "")
	var endpoint = http_client.get_meta("endpoint", "")
	
	server_logger.log_system_event("networkclient_http_response", {
		"endpoint": endpoint,
		"code": response_code,
		"callback": callback
	})
	
	var response_text = body.get_string_from_utf8()
	var response_data = {}
	
	if response_text != "":
		var json = JSON.new()
		if json.parse(response_text) == OK:
			response_data = json.data
	
	# Call specific response handler
	if callback != "" and has_method(callback):
		call(callback, response_code, response_data)
	else:
		server_logger.log_error("NetworkClient", "No callback handler", {"callback": callback})

func _on_queue_join_response(code: int, data: Dictionary):
	"""Handle queue join response"""
	if code == 200:
		var status = data.get("status", "")
		if status == "match_found":
			server_logger.log_system_event("networkclient_match_found_immediately", {"match_id": data.get("match_id")})
			current_match_id = str(data.get("match_id", ""))
			match_found.emit(data)
		else:
			server_logger.log_system_event("networkclient_joined_queue", {"position": data.get("position")})
	else:
		var error_msg = data.get("error", "Failed to join queue")
		server_logger.log_error("NetworkClient", "Queue join failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_queue_leave_response(code: int, data: Dictionary):
	"""Handle queue leave response"""
	if code == 200:
		server_logger.log_system_event("NetworkClient", "Left queue successfully")
	else:
		var error_msg = data.get("error", "Failed to leave queue")
		server_logger.log_error("NetworkClient", "Queue leave failed", {"error": error_msg})

func _on_queue_status_response(code: int, data: Dictionary):
	"""Handle queue status response"""
	if code == 200:
		server_logger.log_system_event("NetworkClient", "Queue status", data)
	else:
		server_logger.log_error("NetworkClient", "Failed to get queue status")

func _on_match_created_response(code: int, data: Dictionary):
	"""Handle match creation response"""
	if code == 200:
		var match_id = data.get("match_id")
		server_logger.log_system_event("networkclient_match_created", {"match_id": match_id})
		current_match_id = str(match_id)
	else:
		var error_msg = data.get("error", "Failed to create match")
		server_logger.log_error("NetworkClient", "Match creation failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_match_start_response(code: int, data: Dictionary):
	"""Handle match start response"""
	if code == 200:
		server_logger.log_system_event("networkclient_match_started_successfully")
		is_in_match = true
		match_started.emit(data.get("game_state", {}))
	else:
		var error_msg = data.get("error", "Failed to start match")
		server_logger.log_error("NetworkClient", "Match start failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_match_state_response(code: int, data: Dictionary):
	"""Handle match state response"""
	if code == 200:
		server_logger.log_system_event("NetworkClient", "Received match state")
		game_state_updated.emit({"type": "state_response", "state": data})
	else:
		var error_msg = data.get("error", "Failed to get match state")
		server_logger.log_error("NetworkClient", "Match state request failed", {"error": error_msg})

func _on_card_play_response(code: int, data: Dictionary):
	"""Handle card play response"""
	if code == 200:
		server_logger.log_system_event("networkclient_card_played_successfully")
		card_played.emit(data.get("result", {}))
	else:
		var error_msg = data.get("error", "Failed to play card")
		server_logger.log_error("NetworkClient", "Card play failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_phase_advance_response(code: int, data: Dictionary):
	"""Handle phase advance response"""
	if code == 200:
		server_logger.log_system_event("NetworkClient", "Phase advanced successfully")
	else:
		var error_msg = data.get("error", "Failed to advance phase")
		server_logger.log_error("NetworkClient", "Phase advance failed", {"error": error_msg})

func _on_match_end_response(code: int, data: Dictionary):
	"""Handle match end response"""
	if code == 200:
		server_logger.log_system_event("NetworkClient", "Match ended successfully")
		is_in_match = false
		current_match_id = ""
	else:
		var error_msg = data.get("error", "Failed to end match")
		server_logger.log_error("NetworkClient", "Match end failed", {"error": error_msg})

func _on_active_matches_response(code: int, data: Dictionary):
	"""Handle active matches response"""
	if code == 200:
		var matches = data.get("active_matches", [])
		server_logger.log_system_event("networkclient_active_matches", {"count": len(matches)})
	else:
		server_logger.log_error("NetworkClient", "Failed to get active matches")

func _on_card_scan_response(code: int, data: Dictionary):
	"""Handle card scan simulation response"""
	if code == 200:
		server_logger.log_system_event("networkclient_card_scanned", {"name": data.get("name", "Unknown")})
		# Emit as if NFC scan occurred
		# Note: NFCManager signal would be emitted here in full implementation
		print("🃏 Simulated card scan: ", data.get("name", "Unknown"))
	else:
		server_logger.log_error("NetworkClient", "Card scan failed")

# === CONNECTION MANAGEMENT ===

func _attempt_reconnect():
	"""Attempt to reconnect to server"""
	if reconnect_attempts >= max_reconnect_attempts:
		server_logger.log_error("NetworkClient", "Max reconnection attempts reached")
		error_occurred.emit("Connection lost - max retries exceeded")
		return
	
	reconnect_attempts += 1
	server_logger.log_system_event("networkclient_attempting_reconnection", {"attempt": reconnect_attempts})
	
	# Wait before reconnecting
	await get_tree().create_timer(2.0).timeout
	
	if api_token != "":
		authenticate(api_token, device_uid)

func disconnect_from_server():
	"""Disconnect from server"""
	server_logger.log_system_event("NetworkClient", "Disconnecting from server")
	
	is_network_connected = false
	is_in_match = false
	current_match_id = ""
	
	if websocket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		websocket.close()
	
	disconnected_from_server.emit()

# === UTILITY METHODS ===

func get_connection_status() -> Dictionary:
	"""Get current connection status"""
	return {
		"connected": is_network_connected,
		"in_match": is_in_match,
		"match_id": current_match_id,
		"player_id": player_id,
		"device_uid": device_uid
	}

func set_player_info(id: int):
	"""Set current player information"""
	player_id = id
	server_logger.log_system_event("networkclient_player_info_set", {"player_id": player_id})
