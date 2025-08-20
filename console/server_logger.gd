extends Node

# Server Logger - Sends real-time logs to server for monitoring and security

var server_url = "http://127.0.0.1:8002"
var device_id = ""
var log_queue = []
var http_request: HTTPRequest
var is_sending = false

func _ready():
	print("📡 Server Logger initialized")
	device_id = "DECK_DEV_CONSOLE_01"  # Fixed device ID for development
	
	# Create HTTP request node
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_log_sent)
	
	# Send logs every 5 seconds
	var timer = Timer.new()
	timer.wait_time = 5.0
	timer.timeout.connect(send_queued_logs)
	timer.autostart = true
	add_child(timer)

func log_to_server(level: String, component: String, message: String, data: Dictionary = {}):
	"""Queue log entry to be sent to server"""
	var log_entry = {
		"timestamp": Time.get_datetime_string_from_system(),
		"device_id": device_id,
		"level": level,
		"component": component,
		"message": message,
		"data": data,
		"session_id": get_session_id()
	}
	
	log_queue.append(log_entry)
	print("[%s] %s: %s" % [level, component, message])
	
	# Send immediately for critical logs
	if level in ["ERROR", "CRITICAL", "SECURITY"]:
		send_queued_logs()

func log_info(component: String, message: String, data: Dictionary = {}):
	"""Log info message"""
	log_to_server("INFO", component, message, data)

func log_warning(component: String, message: String, data: Dictionary = {}):
	"""Log warning message"""
	log_to_server("WARNING", component, message, data)

func log_error(component: String, message: String, data: Dictionary = {}):
	"""Log error message"""
	log_to_server("ERROR", component, message, data)

func log_security(component: String, message: String, data: Dictionary = {}):
	"""Log security event (sent immediately)"""
	log_to_server("SECURITY", component, message, data)

func log_user_action(action: String, data: Dictionary = {}):
	"""Log user action for security monitoring"""
	log_security("UserAction", action, data)

func log_system_event(event: String, data: Dictionary = {}):
	"""Log system event"""
	log_info("System", event, data)

func log_nfc_scan(card_uid: String, success: bool, card_data: Dictionary = {}):
	"""Log NFC card scan for security"""
	log_security("NFC", "Card scan: " + ("success" if success else "failed"), {
		"card_uid": card_uid,
		"success": success,
		"card_data": card_data
	})

func send_queued_logs():
	"""Send all queued logs to server"""
	if log_queue.is_empty() or is_sending:
		return
	
	is_sending = true
	
	var payload = {
		"device_id": device_id,
		"logs": log_queue.duplicate(),
		"timestamp": Time.get_datetime_string_from_system()
	}
	
	var json = JSON.stringify(payload)
	var headers = ["Content-Type: application/json"]
	
	# TODO: Add device authentication header when available
	# headers.append("Authorization: Bearer " + device_token)
	
	var url = server_url + "/v1/console/logs"
	http_request.request(url, headers, HTTPClient.METHOD_POST, json)
	
	print("📡 Sending %d logs to server" % log_queue.size())

func _on_log_sent(_result: int, response_code: int, _headers: PackedStringArray, _body: PackedByteArray):
	"""Handle log send response"""
	is_sending = false
	
	if response_code == 200 or response_code == 201:
		print("✅ Logs sent successfully (%d entries)" % log_queue.size())
		log_queue.clear()
	else:
		print("❌ Failed to send logs (HTTP %d)" % response_code)
		# Keep logs in queue for retry
		if log_queue.size() > 100:  # Prevent infinite growth
			log_queue = log_queue.slice(-50)  # Keep last 50 logs

func get_session_id() -> String:
	"""Get current session identifier"""
	# Simple session ID for now
	return device_id + "_" + str(Time.get_unix_time_from_system())

func log_scene_change(from_scene: String, to_scene: String):
	"""Log scene transitions for monitoring"""
	log_user_action("scene_change", {
		"from": from_scene,
		"to": to_scene
	})

func log_button_press(button_name: String, context: String = ""):
	"""Log button presses for user behavior analysis"""
	log_user_action("button_press", {
		"button": button_name,
		"context": context
	})

func log_login_attempt(method: String, success: bool, details: Dictionary = {}):
	"""Log login attempts for security"""
	log_security("Login", method + ": " + ("success" if success else "failed"), details)

func log_match_event(event: String, match_data: Dictionary = {}):
	"""Log match events"""
	log_info("Match", event, match_data)

func log_console_boot(boot_time: float):
	"""Log console boot completion"""
	log_system_event("console_boot", {
		"boot_time_seconds": boot_time,
		"godot_version": Engine.get_version_info(),
		"platform": OS.get_name()
	})
