extends Node

# Video Stream Manager - Handles secure video streaming for battles and admin surveillance
# Manages camera, screen sharing, and communication with the video streaming API

signal stream_started(stream_id: String, success: bool)
signal stream_joined(stream_id: String, success: bool)
signal stream_ended(stream_id: String)
signal participant_joined(participant_info: Dictionary)
signal participant_left(participant_info: Dictionary)
signal surveillance_detected(admin_info: Dictionary)

# Server configuration
var server_url: String = "https://deckport.ai"
var api_headers: Array[String] = []

# Stream state
var current_stream_id: String = ""
var current_stream_type: String = ""
var is_streaming: bool = false
var is_being_surveilled: bool = false

# Video components
var camera_texture: CameraTexture = null
var screen_capture: ImageTexture = null
var video_display: VideoStreamPlayer = null
var opponent_video_display: VideoStreamPlayer = null

# HTTP requests
var http_request: HTTPRequest
var stream_status_timer: Timer

# Device connection manager reference
var device_connection_manager

# Server logger
var server_logger

func _ready():
	print("🎥 Video Stream Manager initialized")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Setup HTTP request
	setup_http_request()
	
	# Setup stream status monitoring
	setup_status_monitoring()
	
	# Get device connection manager
	device_connection_manager = get_node("/root/DeviceConnectionManager")
	if device_connection_manager:
		api_headers = device_connection_manager.get_auth_headers()
	else:
		print("⚠️ DeviceConnectionManager not found - using basic headers")
		api_headers = ["Content-Type: application/json", "User-Agent: Deckport-Console/1.0"]

func setup_http_request():
	"""Setup HTTP request for API communication"""
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_http_response)
	http_request.timeout = 30.0
	print("📡 HTTP request configured for video streaming")

func setup_status_monitoring():
	"""Setup timer for monitoring stream status"""
	stream_status_timer = Timer.new()
	add_child(stream_status_timer)
	stream_status_timer.wait_time = 5.0  # Check every 5 seconds
	stream_status_timer.timeout.connect(_check_stream_status)
	print("⏱️ Stream status monitoring configured")

# === BATTLE VIDEO STREAMING ===

func start_battle_stream(opponent_console_id: int, battle_id: String, options: Dictionary = {}):
	"""Start a video stream for battle with another player"""
	if is_streaming:
		print("⚠️ Already streaming, cannot start new battle stream")
		return false
	
	print("🎮 Starting battle stream - Opponent: ", opponent_console_id, " Battle: ", battle_id)
	
	var request_data = {
		"opponent_console_id": opponent_console_id,
		"battle_id": battle_id,
		"enable_camera": options.get("camera", false),
		"enable_screen_share": options.get("screen_share", true),
		"enable_audio": options.get("audio", false)
	}
	
	server_logger.log_system_event("battle_stream_start_request", {
		"opponent_console_id": opponent_console_id,
		"battle_id": battle_id,
		"options": options
	})
	
	var url = server_url + "/v1/video/battle/start"
	var headers = api_headers.duplicate()
	headers.append("Content-Type: application/json")
	
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(request_data))
	if error != OK:
		print("❌ Failed to start battle stream request: ", error)
		stream_started.emit("", false)
		return false
	
	return true

func join_battle_stream(stream_id: String, options: Dictionary = {}):
	"""Join an existing battle stream"""
	if is_streaming:
		print("⚠️ Already streaming, cannot join battle stream")
		return false
	
	print("🎮 Joining battle stream: ", stream_id)
	
	var request_data = {
		"enable_camera": options.get("camera", false),
		"enable_screen_share": options.get("screen_share", true),
		"enable_audio": options.get("audio", false)
	}
	
	server_logger.log_system_event("battle_stream_join_request", {
		"stream_id": stream_id,
		"options": options
	})
	
	var url = server_url + "/v1/video/battle/" + stream_id + "/join"
	var headers = api_headers.duplicate()
	headers.append("Content-Type: application/json")
	
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(request_data))
	if error != OK:
		print("❌ Failed to join battle stream request: ", error)
		stream_joined.emit(stream_id, false)
		return false
	
	return true

# === CAMERA AND SCREEN CAPTURE ===

func setup_camera_capture():
	"""Setup camera capture for video streaming"""
	if camera_texture:
		print("📷 Camera already configured")
		return true
	
	# Try to access camera
	var camera_feed = CameraServer.get_feed(0)  # Primary camera
	if camera_feed:
		camera_texture = CameraTexture.new()
		camera_texture.camera_feed_id = camera_feed.get_id()
		camera_texture.camera_is_active = true
		
		print("📷 Camera capture configured - Feed ID: ", camera_feed.get_id())
		server_logger.log_system_event("camera_configured", {
			"feed_id": camera_feed.get_id(),
			"name": camera_feed.get_name()
		})
		return true
	else:
		print("❌ No camera available")
		server_logger.log_system_event("camera_unavailable", {})
		return false

func setup_screen_capture():
	"""Setup screen capture for streaming"""
	print("🖥️ Setting up screen capture")
	
	# Get the main viewport
	var viewport = get_viewport()
	if viewport:
		# Create screen capture texture
		screen_capture = ImageTexture.new()
		
		# Capture current screen
		var screen_image = viewport.get_texture().get_image()
		screen_capture.set_image(screen_image)
		
		print("🖥️ Screen capture configured")
		server_logger.log_system_event("screen_capture_configured", {
			"resolution": str(screen_image.get_size())
		})
		return true
	else:
		print("❌ Failed to setup screen capture")
		return false

func update_screen_capture():
	"""Update screen capture (call periodically during streaming)"""
	if not screen_capture or not is_streaming:
		return
	
	var viewport = get_viewport()
	if viewport:
		var screen_image = viewport.get_texture().get_image()
		screen_capture.set_image(screen_image)

# === VIDEO DISPLAY ===

func setup_video_display(container: Control):
	"""Setup video display components in the provided container"""
	print("📺 Setting up video display in container")
	
	# Create main video display (opponent's stream)
	opponent_video_display = VideoStreamPlayer.new()
	opponent_video_display.name = "OpponentVideo"
	opponent_video_display.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	opponent_video_display.size = Vector2(640, 480)
	opponent_video_display.volume_db = -10.0  # Slightly reduced volume
	container.add_child(opponent_video_display)
	
	# Create picture-in-picture for own camera (if enabled)
	video_display = VideoStreamPlayer.new()
	video_display.name = "SelfVideo"
	video_display.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	video_display.size = Vector2(160, 120)
	video_display.position = Vector2(-170, 10)
	video_display.volume_db = -80.0  # Mute own video
	container.add_child(video_display)
	
	print("📺 Video display components created")
	server_logger.log_system_event("video_display_setup", {
		"opponent_video_size": str(opponent_video_display.size),
		"self_video_size": str(video_display.size)
	})

func show_surveillance_warning():
	"""Show warning that admin surveillance is active"""
	print("🚨 SURVEILLANCE DETECTED - Admin is monitoring this console")
	is_being_surveilled = true
	
	# Create surveillance warning overlay
	var warning_overlay = ColorRect.new()
	warning_overlay.name = "SurveillanceWarning"
	warning_overlay.color = Color(1, 0, 0, 0.3)  # Semi-transparent red
	warning_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	get_viewport().add_child(warning_overlay)
	
	# Add warning text
	var warning_label = Label.new()
	warning_label.text = "⚠️ ADMIN SURVEILLANCE ACTIVE ⚠️\nThis console is being monitored"
	warning_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	warning_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	warning_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	warning_label.add_theme_color_override("font_color", Color.WHITE)
	warning_overlay.add_child(warning_label)
	
	# Flash the warning
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property(warning_overlay, "modulate:a", 0.5, 1.0)
	tween.tween_property(warning_overlay, "modulate:a", 1.0, 1.0)
	
	server_logger.log_system_event("surveillance_warning_shown", {
		"timestamp": Time.get_unix_time_from_system()
	})
	
	surveillance_detected.emit({"active": true})

func hide_surveillance_warning():
	"""Hide surveillance warning overlay"""
	var warning_overlay = get_viewport().get_node_or_null("SurveillanceWarning")
	if warning_overlay:
		warning_overlay.queue_free()
		is_being_surveilled = false
		print("✅ Surveillance warning hidden")
		
		server_logger.log_system_event("surveillance_warning_hidden", {
			"timestamp": Time.get_unix_time_from_system()
		})

# === STREAM MANAGEMENT ===

func end_current_stream():
	"""End the current video stream"""
	if not is_streaming or current_stream_id.is_empty():
		print("⚠️ No active stream to end")
		return
	
	print("⏹️ Ending video stream: ", current_stream_id)
	
	var url = server_url + "/v1/video/" + current_stream_id + "/end"
	var error = http_request.request(url, api_headers, HTTPClient.METHOD_POST)
	
	if error != OK:
		print("❌ Failed to end stream request: ", error)
	
	# Clean up local resources
	cleanup_stream_resources()

func cleanup_stream_resources():
	"""Clean up video streaming resources"""
	print("🧹 Cleaning up video stream resources")
	
	# Stop camera
	if camera_texture:
		camera_texture.camera_is_active = false
	
	# Clear video displays
	if video_display:
		video_display.stop()
		video_display.stream = null
	
	if opponent_video_display:
		opponent_video_display.stop()
		opponent_video_display.stream = null
	
	# Stop status monitoring
	if stream_status_timer:
		stream_status_timer.stop()
	
	# Reset state
	is_streaming = false
	current_stream_id = ""
	current_stream_type = ""
	
	# Hide surveillance warning if active
	if is_being_surveilled:
		hide_surveillance_warning()
	
	server_logger.log_system_event("stream_resources_cleaned", {
		"timestamp": Time.get_unix_time_from_system()
	})

func _check_stream_status():
	"""Periodically check stream status"""
	if not is_streaming or current_stream_id.is_empty():
		return
	
	var url = server_url + "/v1/video/" + current_stream_id + "/status"
	var error = http_request.request(url, api_headers, HTTPClient.METHOD_GET)
	
	if error != OK:
		print("❌ Failed to check stream status: ", error)

# === HTTP RESPONSE HANDLERS ===

func _on_http_response(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP responses from video streaming API"""
	var response_text = body.get_string_from_utf8()
	
	print("📡 Video API Response - Code: ", response_code, " Size: ", body.size())
	
	if result != HTTPRequest.RESULT_SUCCESS:
		print("❌ Network error: ", result)
		return
	
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(response_text)
		
		if parse_result == OK:
			var data = json.data
			
			# Handle different response types
			if data.has("stream_id"):
				var stream_id = data.stream_id
				
				if data.has("participant_id"):
					# Battle stream started or joined
					current_stream_id = stream_id
					current_stream_type = "battle"
					is_streaming = true
					
					# Start status monitoring
					stream_status_timer.start()
					
					# Setup video components if needed
					if data.get("joined_successfully", false):
						print("✅ Successfully joined battle stream: ", stream_id)
						stream_joined.emit(stream_id, true)
					else:
						print("✅ Successfully started battle stream: ", stream_id)
						stream_started.emit(stream_id, true)
					
					server_logger.log_system_event("battle_stream_active", {
						"stream_id": stream_id,
						"participant_id": data.get("participant_id")
					})
				
				elif data.has("surveillance_url"):
					# Admin surveillance started
					current_stream_id = stream_id
					current_stream_type = "surveillance"
					is_streaming = true
					
					# Show surveillance warning
					show_surveillance_warning()
					
					print("🚨 Admin surveillance active: ", stream_id)
					server_logger.log_system_event("surveillance_active", {
						"stream_id": stream_id,
						"started_by": data.get("started_by")
					})
			
			elif data.has("status"):
				# Stream status update
				var status = data.status
				
				if status == "ended":
					print("⏹️ Stream ended: ", current_stream_id)
					stream_ended.emit(current_stream_id)
					cleanup_stream_resources()
				
				elif data.has("participants"):
					# Update participant information
					for participant in data.participants:
						if participant.get("joined_at") and not participant.get("left_at"):
							participant_joined.emit(participant)
						elif participant.get("left_at"):
							participant_left.emit(participant)
		else:
			print("❌ Failed to parse video API response")
	else:
		print("❌ Video API error: ", response_code, " - ", response_text)

# === UTILITY METHODS ===

func is_camera_available() -> bool:
	"""Check if camera is available"""
	return CameraServer.get_feed_count() > 0

func get_stream_info() -> Dictionary:
	"""Get current stream information"""
	return {
		"stream_id": current_stream_id,
		"stream_type": current_stream_type,
		"is_streaming": is_streaming,
		"is_being_surveilled": is_being_surveilled,
		"camera_available": is_camera_available()
	}

func set_api_headers(headers: Array[String]):
	"""Set API headers for authentication"""
	api_headers = headers

func _exit_tree():
	"""Clean up when node is removed"""
	if is_streaming:
		end_current_stream()
	cleanup_stream_resources()
