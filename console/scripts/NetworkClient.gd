extends Node
class_name NetworkClient

# Network Client for Deckport Console
# Handles all API communication including gameplay, matchmaking, and real-time features

signal connected_to_server()
signal disconnected_from_server()
signal match_found(match_data: Dictionary)
signal match_started(game_state: Dictionary)
signal match_ended(result: Dictionary)
signal game_state_updated(state: Dictionary)
signal card_played(card_data: Dictionary)
signal phase_changed(phase_data: Dictionary)
signal timer_updated(timer_data: Dictionary)
signal error_occurred(error_message: String)

# Server configuration
var server_url: String = "http://127.0.0.1:8002"
var websocket_url: String = "ws://127.0.0.1:8003"
var api_token: String = ""
var device_uid: String = ""
var player_id: int = 0
var current_match_id: String = ""

# HTTP client for API calls
var http_client: HTTPRequest
var websocket: WebSocketPeer

# Connection state
var is_connected: bool = false
var is_in_match: bool = false
var reconnect_attempts: int = 0
var max_reconnect_attempts: int = 5

func _ready():
	Logger.log_info("NetworkClient", "Network client initialized")
	
	# Create HTTP client
	http_client = HTTPRequest.new()
	add_child(http_client)
	http_client.request_completed.connect(_on_http_request_completed)
	
	# Initialize WebSocket
	websocket = WebSocketPeer.new()

func _process(delta):
	# Poll WebSocket
	if websocket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		websocket.poll()
		
		# Handle WebSocket state
		var state = websocket.get_ready_state()
		if state == WebSocketPeer.STATE_OPEN:
			if not is_connected:
				is_connected = true
				connected_to_server.emit()
				Logger.log_info("NetworkClient", "WebSocket connected")
			
			# Process messages
			while websocket.get_available_packet_count():
				var packet = websocket.get_packet()
				var message_text = packet.get_string_from_utf8()
				_handle_websocket_message(message_text)
		
		elif state == WebSocketPeer.STATE_CLOSED:
			if is_connected:
				is_connected = false
				disconnected_from_server.emit()
				Logger.log_warning("NetworkClient", "WebSocket disconnected")
				_attempt_reconnect()

# === AUTHENTICATION ===

func authenticate(token: String, device_id: String):
	"""Authenticate with the server"""
	api_token = token
	device_uid = device_id
	
	Logger.log_info("NetworkClient", "Authenticating with server")
	
	# Connect to WebSocket with authentication
	var headers = ["Authorization: Bearer " + api_token]
	var error = websocket.connect_to_url(websocket_url, headers)
	
	if error != OK:
		Logger.log_error("NetworkClient", "Failed to connect WebSocket", {"error": error})
		error_occurred.emit("Failed to connect to server")

# === MATCHMAKING ===

func join_matchmaking_queue(mode: String = "1v1"):
	"""Join the matchmaking queue"""
	Logger.log_info("NetworkClient", "Joining matchmaking queue", {"mode": mode})
	
	var data = {
		"player_id": player_id,
		"console_id": device_uid,
		"mode": mode
	}
	
	_make_api_request("POST", "/v1/gameplay/queue/join", data, "_on_queue_join_response")

func leave_matchmaking_queue(mode: String = "1v1"):
	"""Leave the matchmaking queue"""
	Logger.log_info("NetworkClient", "Leaving matchmaking queue")
	
	var data = {
		"player_id": player_id,
		"mode": mode
	}
	
	_make_api_request("POST", "/v1/gameplay/queue/leave", data, "_on_queue_leave_response")

func get_queue_status(mode: String = "1v1"):
	"""Get current queue status"""
	var url = "/v1/gameplay/queue/status?player_id=" + str(player_id) + "&mode=" + mode
	_make_api_request("GET", url, null, "_on_queue_status_response")

# === MATCH MANAGEMENT ===

func create_test_match(players: Array):
	"""Create a test match (for development)"""
	Logger.log_info("NetworkClient", "Creating test match")
	
	var data = {
		"mode": "1v1",
		"players": players
	}
	
	_make_api_request("POST", "/v1/gameplay/matches", data, "_on_match_created_response")

func start_match(match_id: int):
	"""Start a match"""
	Logger.log_info("NetworkClient", "Starting match", {"match_id": match_id})
	
	var url = "/v1/gameplay/matches/" + str(match_id) + "/start"
	_make_api_request("POST", url, {}, "_on_match_start_response")

func get_match_state(match_id: int, team: int = -1):
	"""Get current match state"""
	var url = "/v1/gameplay/matches/" + str(match_id) + "/state"
	if team >= 0:
		url += "?team=" + str(team)
	
	_make_api_request("GET", url, null, "_on_match_state_response")

func send_match_ready(match_id: String):
	"""Send ready signal for match"""
	if not is_connected:
		Logger.log_error("NetworkClient", "Not connected to server")
		return
	
	var message = {
		"type": "match.ready",
		"match_id": match_id
	}
	
	_send_websocket_message(message)

# === GAMEPLAY ACTIONS ===

func play_card(match_id: int, player_team: int, card_id: String, action: String = "play", target: String = ""):
	"""Play a card in the current match"""
	Logger.log_info("NetworkClient", "Playing card", {
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
	if not is_connected:
		Logger.log_error("NetworkClient", "Not connected to server")
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
	if not is_connected:
		Logger.log_error("NetworkClient", "Not connected to server")
		return
	
	var message = {
		"type": "sync.request",
		"match_id": match_id
	}
	
	_send_websocket_message(message)

# === ADMIN/DEBUG FUNCTIONS ===

func force_advance_phase(match_id: int):
	"""Force advance to next phase (admin)"""
	Logger.log_info("NetworkClient", "Force advancing phase", {"match_id": match_id})
	
	var url = "/v1/gameplay/matches/" + str(match_id) + "/advance-phase"
	_make_api_request("POST", url, {}, "_on_phase_advance_response")

func end_match(match_id: int, result: Dictionary = {}):
	"""End a match (admin)"""
	Logger.log_info("NetworkClient", "Ending match", {"match_id": match_id})
	
	var data = {"result": result}
	var url = "/v1/gameplay/matches/" + str(match_id) + "/end"
	_make_api_request("POST", url, data, "_on_match_end_response")

func get_active_matches():
	"""Get list of active matches"""
	_make_api_request("GET", "/v1/gameplay/matches/active", null, "_on_active_matches_response")

# === CARD SCANNING SIMULATION ===

func simulate_card_scan(card_sku: String):
	"""Simulate NFC card scan (for development)"""
	Logger.log_info("NetworkClient", "Simulating card scan", {"sku": card_sku})
	
	# Get card data from catalog
	var url = "/v1/catalog/cards/" + card_sku
	_make_api_request("GET", url, null, "_on_card_scan_response")

# === PRIVATE METHODS ===

func _make_api_request(method: String, endpoint: String, data: Dictionary, callback: String):
	"""Make HTTP API request"""
	var url = server_url + endpoint
	var headers = [
		"Content-Type: application/json",
		"Authorization: Bearer " + api_token
	]
	
	var json_data = ""
	if data != null:
		json_data = JSON.stringify(data)
	
	Logger.log_debug("NetworkClient", "API Request", {
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
		Logger.log_error("NetworkClient", "HTTP request failed", {"error": error})
		error_occurred.emit("Network request failed")

func _send_websocket_message(message: Dictionary):
	"""Send message via WebSocket"""
	if websocket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		Logger.log_error("NetworkClient", "WebSocket not connected")
		return
	
	var json_string = JSON.stringify(message)
	var error = websocket.send_text(json_string)
	
	if error != OK:
		Logger.log_error("NetworkClient", "Failed to send WebSocket message", {"error": error})
	else:
		Logger.log_debug("NetworkClient", "Sent WebSocket message", message)

func _handle_websocket_message(message_text: String):
	"""Handle incoming WebSocket message"""
	var json = JSON.new()
	var parse_result = json.parse(message_text)
	
	if parse_result != OK:
		Logger.log_error("NetworkClient", "Failed to parse WebSocket message", {"text": message_text})
		return
	
	var message = json.data
	var msg_type = message.get("type", "")
	
	Logger.log_debug("NetworkClient", "Received WebSocket message", {"type": msg_type})
	
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
			Logger.log_warning("NetworkClient", "Unknown WebSocket message type", {"type": msg_type})

func _handle_match_found(message: Dictionary):
	"""Handle match found message"""
	Logger.log_info("NetworkClient", "Match found", message)
	current_match_id = message.get("match_id", "")
	match_found.emit(message)

func _handle_match_start(message: Dictionary):
	"""Handle match start message"""
	Logger.log_info("NetworkClient", "Match started", {"match_id": message.get("match_id")})
	is_in_match = true
	match_started.emit(message)

func _handle_match_end(message: Dictionary):
	"""Handle match end message"""
	Logger.log_info("NetworkClient", "Match ended", message.get("result", {}))
	is_in_match = false
	current_match_id = ""
	match_ended.emit(message)

func _handle_state_update(message: Dictionary):
	"""Handle game state update"""
	var patch = message.get("patch", {})
	Logger.log_debug("NetworkClient", "Game state updated", patch)
	
	# Check for phase changes
	if "phase" in patch:
		phase_changed.emit(patch)
	
	game_state_updated.emit(message)

func _handle_card_played(message: Dictionary):
	"""Handle card played message"""
	Logger.log_info("NetworkClient", "Card played", {
		"player": message.get("player_team"),
		"card": message.get("card_id")
	})
	card_played.emit(message)

func _handle_timer_tick(message: Dictionary):
	"""Handle timer tick message"""
	timer_updated.emit(message)

func _handle_sync_snapshot(message: Dictionary):
	"""Handle full state synchronization"""
	Logger.log_info("NetworkClient", "Received state sync")
	var full_state = message.get("full_state", {})
	game_state_updated.emit({"type": "full_sync", "state": full_state})

func _handle_error_message(message: Dictionary):
	"""Handle error message from server"""
	var error_msg = message.get("message", "Unknown error")
	Logger.log_error("NetworkClient", "Server error", message)
	error_occurred.emit(error_msg)

# === HTTP RESPONSE HANDLERS ===

func _on_http_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP request completion"""
	var callback = http_client.get_meta("callback", "")
	var endpoint = http_client.get_meta("endpoint", "")
	
	Logger.log_debug("NetworkClient", "HTTP Response", {
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
		Logger.log_warning("NetworkClient", "No callback handler", {"callback": callback})

func _on_queue_join_response(code: int, data: Dictionary):
	"""Handle queue join response"""
	if code == 200:
		var status = data.get("status", "")
		if status == "match_found":
			Logger.log_info("NetworkClient", "Match found immediately", {"match_id": data.get("match_id")})
			current_match_id = str(data.get("match_id", ""))
			match_found.emit(data)
		else:
			Logger.log_info("NetworkClient", "Joined queue", {"position": data.get("position")})
	else:
		var error_msg = data.get("error", "Failed to join queue")
		Logger.log_error("NetworkClient", "Queue join failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_queue_leave_response(code: int, data: Dictionary):
	"""Handle queue leave response"""
	if code == 200:
		Logger.log_info("NetworkClient", "Left queue successfully")
	else:
		var error_msg = data.get("error", "Failed to leave queue")
		Logger.log_error("NetworkClient", "Queue leave failed", {"error": error_msg})

func _on_queue_status_response(code: int, data: Dictionary):
	"""Handle queue status response"""
	if code == 200:
		Logger.log_debug("NetworkClient", "Queue status", data)
	else:
		Logger.log_error("NetworkClient", "Failed to get queue status")

func _on_match_created_response(code: int, data: Dictionary):
	"""Handle match creation response"""
	if code == 200:
		var match_id = data.get("match_id")
		Logger.log_info("NetworkClient", "Match created", {"match_id": match_id})
		current_match_id = str(match_id)
	else:
		var error_msg = data.get("error", "Failed to create match")
		Logger.log_error("NetworkClient", "Match creation failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_match_start_response(code: int, data: Dictionary):
	"""Handle match start response"""
	if code == 200:
		Logger.log_info("NetworkClient", "Match started successfully")
		is_in_match = true
		match_started.emit(data.get("game_state", {}))
	else:
		var error_msg = data.get("error", "Failed to start match")
		Logger.log_error("NetworkClient", "Match start failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_match_state_response(code: int, data: Dictionary):
	"""Handle match state response"""
	if code == 200:
		Logger.log_debug("NetworkClient", "Received match state")
		game_state_updated.emit({"type": "state_response", "state": data})
	else:
		var error_msg = data.get("error", "Failed to get match state")
		Logger.log_error("NetworkClient", "Match state request failed", {"error": error_msg})

func _on_card_play_response(code: int, data: Dictionary):
	"""Handle card play response"""
	if code == 200:
		Logger.log_info("NetworkClient", "Card played successfully")
		card_played.emit(data.get("result", {}))
	else:
		var error_msg = data.get("error", "Failed to play card")
		Logger.log_error("NetworkClient", "Card play failed", {"error": error_msg})
		error_occurred.emit(error_msg)

func _on_phase_advance_response(code: int, data: Dictionary):
	"""Handle phase advance response"""
	if code == 200:
		Logger.log_info("NetworkClient", "Phase advanced successfully")
	else:
		var error_msg = data.get("error", "Failed to advance phase")
		Logger.log_error("NetworkClient", "Phase advance failed", {"error": error_msg})

func _on_match_end_response(code: int, data: Dictionary):
	"""Handle match end response"""
	if code == 200:
		Logger.log_info("NetworkClient", "Match ended successfully")
		is_in_match = false
		current_match_id = ""
	else:
		var error_msg = data.get("error", "Failed to end match")
		Logger.log_error("NetworkClient", "Match end failed", {"error": error_msg})

func _on_active_matches_response(code: int, data: Dictionary):
	"""Handle active matches response"""
	if code == 200:
		var matches = data.get("active_matches", [])
		Logger.log_info("NetworkClient", "Active matches", {"count": len(matches)})
	else:
		Logger.log_error("NetworkClient", "Failed to get active matches")

func _on_card_scan_response(code: int, data: Dictionary):
	"""Handle card scan simulation response"""
	if code == 200:
		Logger.log_info("NetworkClient", "Card scanned", {"name": data.get("name", "Unknown")})
		# Emit as if NFC scan occurred
		NFCManager.card_scanned.emit(data)
	else:
		Logger.log_error("NetworkClient", "Card scan failed")

# === CONNECTION MANAGEMENT ===

func _attempt_reconnect():
	"""Attempt to reconnect to server"""
	if reconnect_attempts >= max_reconnect_attempts:
		Logger.log_error("NetworkClient", "Max reconnection attempts reached")
		error_occurred.emit("Connection lost - max retries exceeded")
		return
	
	reconnect_attempts += 1
	Logger.log_info("NetworkClient", "Attempting reconnection", {"attempt": reconnect_attempts})
	
	# Wait before reconnecting
	await get_tree().create_timer(2.0).timeout
	
	if api_token != "":
		authenticate(api_token, device_uid)

func disconnect_from_server():
	"""Disconnect from server"""
	Logger.log_info("NetworkClient", "Disconnecting from server")
	
	is_connected = false
	is_in_match = false
	current_match_id = ""
	
	if websocket.get_ready_state() != WebSocketPeer.STATE_CLOSED:
		websocket.close()
	
	disconnected_from_server.emit()

# === UTILITY METHODS ===

func get_connection_status() -> Dictionary:
	"""Get current connection status"""
	return {
		"connected": is_connected,
		"in_match": is_in_match,
		"match_id": current_match_id,
		"player_id": player_id,
		"device_uid": device_uid
	}

func set_player_info(id: int):
	"""Set current player information"""
	player_id = id
	Logger.log_info("NetworkClient", "Player info set", {"player_id": player_id})
