extends Node
class_name NetworkClient

# Network Client for Console-Server Communication
# Handles WebSocket connection and real-time messaging

signal connected()
signal disconnected()
signal message_received(message: Dictionary)
signal connection_error(error: String)

var websocket: WebSocketPeer
var connection_url: String = ""
var is_network_connected: bool = false
var is_connecting: bool = false
var reconnect_attempts: int = 0
var max_reconnect_attempts: int = 5

# Message queue for when disconnected
var message_queue: Array = []
var max_queue_size: int = 100

func _ready():
	Logger.log_info("NetworkClient", "Network client initialized")
	websocket = WebSocketPeer.new()

func connect_to_server():
	"""Connect to the real-time server"""
	if is_connecting or is_network_connected:
		Logger.log_warning("NetworkClient", "Already connected or connecting")
		return
	
	# Build WebSocket URL with authentication
	var base_url = Global.server_url.replace("http://", "ws://").replace("https://", "wss://")
	var ws_port = "8003"  # Real-time service port
	
	if Global.is_development():
		connection_url = "ws://127.0.0.1:8003/ws"
	else:
		connection_url = "wss://ws.deckport.ai/ws"
	
	# Add authentication token
	if Global.player_token != "":
		connection_url += "?token=" + Global.player_token
	elif Global.device_token != "":
		connection_url += "?token=" + Global.device_token
	else:
		Logger.log_error("NetworkClient", "No authentication token available")
		connection_error.emit("No authentication token")
		return
	
	Logger.log_info("NetworkClient", "Connecting to: " + connection_url)
	is_connecting = true
	
	# Connect to WebSocket
	var error = websocket.connect_to_url(connection_url)
	if error != OK:
		Logger.log_error("NetworkClient", "Failed to initiate connection", {"error": error})
		is_connecting = false
		connection_error.emit("Connection failed: " + str(error))
		return
	
	# Start connection monitoring
	_start_connection_monitoring()

func _start_connection_monitoring():
	"""Monitor WebSocket connection status"""
	while is_connecting or is_network_connected:
		websocket.poll()
		
		var state = websocket.get_ready_state()
		
		match state:
			WebSocketPeer.STATE_CONNECTING:
				# Still connecting
				pass
			
			WebSocketPeer.STATE_OPEN:
				if not is_network_connected:
					_on_connection_established()
			
			WebSocketPeer.STATE_CLOSING:
				Logger.log_info("NetworkClient", "Connection closing")
				
			WebSocketPeer.STATE_CLOSED:
				if is_network_connected or is_connecting:
					_on_connection_lost()
		
		# Process incoming messages
		while websocket.get_available_packet_count() > 0:
			var packet = websocket.get_packet()
			var message_text = packet.get_string_from_utf8()
			_process_incoming_message(message_text)
		
		await get_tree().process_frame

func _on_connection_established():
	"""Handle successful WebSocket connection"""
	Logger.log_info("NetworkClient", "WebSocket connection established")
	is_connecting = false
	is_network_connected = true
	reconnect_attempts = 0
	
	Global.server_connected = true
	Global.connection_status = "connected"
	
	# Send queued messages
	_send_queued_messages()
	
	connected.emit()

func _on_connection_lost():
	"""Handle WebSocket connection loss"""
	Logger.log_warning("NetworkClient", "WebSocket connection lost")
	is_connecting = false
	is_network_connected = false
	
	Global.server_connected = false
	Global.connection_status = "disconnected"
	
	disconnected.emit()
	
	# Attempt reconnection
	_attempt_reconnection()

func _attempt_reconnection():
	"""Attempt to reconnect to server"""
	if reconnect_attempts >= max_reconnect_attempts:
		Logger.log_error("NetworkClient", "Max reconnection attempts reached")
		connection_error.emit("Connection lost - max retries exceeded")
		return
	
	reconnect_attempts += 1
	Logger.log_info("NetworkClient", "Attempting reconnection", {"attempt": reconnect_attempts})
	
	# Wait before reconnecting (exponential backoff)
	var wait_time = min(pow(2, reconnect_attempts), 30)  # Max 30 seconds
	await get_tree().create_timer(wait_time).timeout
	
	connect_to_server()

func _process_incoming_message(message_text: String):
	"""Process incoming WebSocket message"""
	var json = JSON.new()
	var parse_result = json.parse(message_text)
	
	if parse_result != OK:
		Logger.log_error("NetworkClient", "Failed to parse message", {"text": message_text})
		return
	
	var message = json.data
	if not message:
		Logger.log_error("NetworkClient", "Invalid message data", {"text": message_text})
		return
		
	Logger.log_info("NetworkClient", "Message received", {"type": message.get("type")})
	
	# Emit message for scene handlers
	message_received.emit(message)
	
	# Handle global messages
	_handle_global_message(message)

func _handle_global_message(message: Dictionary):
	"""Handle messages that affect global state"""
	var msg_type = message.get("type", "")
	
	match msg_type:
		"connected":
			Logger.log_info("NetworkClient", "Server confirmed connection")
		
		"error":
			var error_msg = message.get("error", "Unknown error")
			Logger.log_error("NetworkClient", "Server error: " + error_msg)
			connection_error.emit(error_msg)
		
		"match.found":
			Global.current_match_id = message.get("match_id", "")
			Global.in_match = true
			Logger.log_info("NetworkClient", "Match found", {"match_id": Global.current_match_id})

func send_message(message: Dictionary):
	"""Send message to server"""
	if not is_network_connected:
		Logger.log_warning("NetworkClient", "Not connected, queuing message")
		_queue_message(message)
		return
	
	var message_text = JSON.stringify(message)
	if message_text == "":
		Logger.log_error("NetworkClient", "Failed to stringify message")
		_queue_message(message)
		return
		
	var error = websocket.send_text(message_text)
	
	if error != OK:
		Logger.log_error("NetworkClient", "Failed to send message", {"error": error})
		_queue_message(message)  # Queue for retry
	else:
		Logger.log_info("NetworkClient", "Message sent", {"type": message.get("type")})

func _queue_message(message: Dictionary):
	"""Queue message for sending when reconnected"""
	if message_queue.size() >= max_queue_size:
		message_queue.pop_front()  # Remove oldest message
	
	message_queue.append(message)
	Logger.log_info("NetworkClient", "Message queued", {"queue_size": message_queue.size()})

func _send_queued_messages():
	"""Send all queued messages"""
	if message_queue.is_empty():
		return
	
	Logger.log_info("NetworkClient", "Sending queued messages", {"count": message_queue.size()})
	
	var messages_to_send = message_queue.duplicate()
	message_queue.clear()
	
	for message in messages_to_send:
		send_message(message)
		await get_tree().create_timer(0.1).timeout  # Small delay between messages

func disconnect_from_server():
	"""Disconnect from server"""
	Logger.log_info("NetworkClient", "Disconnecting from server")
	is_connecting = false
	is_network_connected = false
	
	if websocket:
		websocket.close()
	
	Global.server_connected = false
	Global.connection_status = "disconnected"

func join_matchmaking_queue(mode: String = "1v1"):
	"""Join matchmaking queue"""
	var message = {
		"type": "queue.join",
		"mode": mode,
		"timestamp": Time.get_datetime_string_from_system()
	}
	
	send_message(message)
	Logger.log_info("NetworkClient", "Joined matchmaking queue", {"mode": mode})

func leave_matchmaking_queue():
	"""Leave matchmaking queue"""
	var message = {
		"type": "queue.leave",
		"timestamp": Time.get_datetime_string_from_system()
	}
	
	send_message(message)
	Logger.log_info("NetworkClient", "Left matchmaking queue")

func send_match_ready():
	"""Send match ready signal"""
	if Global.current_match_id == "":
		Logger.log_error("NetworkClient", "No current match ID")
		return
	
	var message = {
		"type": "match.ready",
		"match_id": Global.current_match_id,
		"timestamp": Time.get_datetime_string_from_system()
	}
	
	send_message(message)
	Logger.log_info("NetworkClient", "Match ready sent")

func send_card_play(card_id: String, action: String, target: String = ""):
	"""Send card play action"""
	if Global.current_match_id == "":
		Logger.log_error("NetworkClient", "No current match ID")
		return
	
	var message = {
		"type": "card.play",
		"match_id": Global.current_match_id,
		"card_id": card_id,
		"action": action,
		"target": target,
		"client_timestamp": Time.get_datetime_string_from_system()
	}
	
	send_message(message)
	Logger.log_info("NetworkClient", "Card play sent", {"card_id": card_id, "action": action})

func send_state_update(delta: Dictionary):
	"""Send game state update"""
	if Global.current_match_id == "":
		Logger.log_error("NetworkClient", "No current match ID")
		return
	
	var message = {
		"type": "state.update",
		"match_id": Global.current_match_id,
		"delta": delta,
		"timestamp": Time.get_datetime_string_from_system()
	}
	
	send_message(message)
	Logger.log_info("NetworkClient", "State update sent")

func get_connection_status() -> String:
	"""Get current connection status"""
	if is_network_connected:
		return "Connected"
	elif is_connecting:
		return "Connecting"
	else:
		return "Disconnected"

func _exit_tree():
	"""Cleanup when node is removed"""
	Logger.log_info("NetworkClient", "Network client shutting down")
	disconnect_from_server()
