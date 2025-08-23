extends Control

# Real QR Login Scene - Server-integrated authentication

@onready var title_label = $CenterContainer/VBoxContainer/TitleLabel
@onready var qr_container = $CenterContainer/VBoxContainer/QRContainer
@onready var qr_image = $CenterContainer/VBoxContainer/QRContainer/QRImageContainer/QRImage
@onready var qr_text = $CenterContainer/VBoxContainer/QRContainer/QRText
@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var timer_label = $CenterContainer/VBoxContainer/TimerLabel
@onready var cancel_button = $CenterContainer/VBoxContainer/CancelButton
@onready var background_video = $BackgroundVideo

var server_logger
var device_connection_manager
var server_url = "http://127.0.0.1:8002"

# QR Login state
var login_token = ""
var qr_url = ""
var remaining_time = 300.0  # 5 minutes
var is_polling = false
var http_request: HTTPRequest
var poll_timer: Timer

func _ready():
	print("📱 QR Login Scene loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_scene_change("main_menu", "qr_login")
	
	# Get device connection manager from parent or create new one
	device_connection_manager = preload("res://device_connection_manager.gd").new()
	add_child(device_connection_manager)
	
	# Check if device is properly authenticated
	if not device_connection_manager.is_connected():
		_show_error("Device not authenticated. Please restart console.")
		return
	
	# Setup HTTP request
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_http_response)
	
	# Configure HTTP request settings
	http_request.timeout = 10.0
	http_request.use_threads = false  # Disable threading for better compatibility
	http_request.accept_gzip = false  # Disable compression for debugging
	
	# Allow insecure connections (for localhost)
	http_request.set_tls_options(TLSOptions.client_unsafe())
	
	print("📡 HTTPRequest configured:")
	print("  Timeout: ", http_request.timeout)
	print("  Use threads: ", http_request.use_threads)
	print("  Accept gzip: ", http_request.accept_gzip)
	
	# Setup polling timer
	poll_timer = Timer.new()
	poll_timer.wait_time = 2.0  # Poll every 2 seconds
	poll_timer.timeout.connect(_poll_login_status)
	add_child(poll_timer)
	
	# Connect cancel button
	cancel_button.pressed.connect(_on_cancel_pressed)
	
	# Setup background
	setup_background()
	
	# Start QR login flow
	start_qr_login_flow()
	


func setup_background():
	"""Setup background video/animation"""
	var video_path = "res://assets/videos/ui/qr_login_background.mp4"
	if ResourceLoader.exists(video_path):
		background_video.stream = load(video_path)
		background_video.loop = true
		background_video.play()
		print("🎬 QR login background video loaded")
	else:
		# Animated background
		var tween = create_tween()
		tween.set_loops()
		tween.tween_property($Background, "color", Color(0.05, 0.15, 0.25, 1), 4.0)
		tween.tween_property($Background, "color", Color(0.15, 0.05, 0.25, 1), 4.0)
		print("🎨 QR login background animation started")

func start_qr_login_flow():
	"""Start real QR login flow with server"""
	print("📱 Starting real QR login flow")
	server_logger.log_login_attempt("qr_code", false, {"status": "started"})
	
	title_label.text = "CONSOLE LOGIN"
	status_label.text = "Generating QR code..."
	qr_text.text = "⏳ Loading..."
	
	# Call server to start QR login with device authentication
	var headers = device_connection_manager.get_authenticated_headers()
	var body = "{}"
	var url = server_url + "/v1/console-login/start"
	
	print("📡 Sending QR request to: ", url)
	print("📡 Headers: ", headers)
	print("📡 Body: ", body)
	print("📡 Method: POST")
	
	# Try the request
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, body)
	print("📡 HTTP Request result: ", error, " (OK = ", OK, ")")
	
	if error != OK:
		var error_msg = "HTTP request setup failed: " + str(error)
		match error:
			ERR_INVALID_PARAMETER:
				error_msg += " (Invalid parameter)"
			ERR_CANT_CONNECT:
				error_msg += " (Can't connect)"
			ERR_CANT_RESOLVE:
				error_msg += " (Can't resolve hostname)"
			_:
				error_msg += " (Unknown error)"
		
		server_logger.log_error("QRLogin", error_msg, {"error": error, "url": url})
		_show_error("Failed to send request to server: " + error_msg)
		return
	
	server_logger.log_system_event("qr_request_sent", {"url": url})

func _on_http_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle server response"""
	var response_text = body.get_string_from_utf8()
	
	print("📡 FULL HTTP Response Details:")
	print("  Result: ", result, " (HTTPRequest.Result enum)")
	print("  Response Code: ", response_code)
	print("  Headers: ", headers)
	print("  Body Size: ", body.size())
	print("  Body Text: ", response_text)
	
	# Log the response details
	server_logger.log_system_event("qr_response", {
		"result": result,
		"code": response_code, 
		"body_length": body.size(),
		"headers_count": headers.size()
	})
	
	# Check for network errors first
	if result != HTTPRequest.RESULT_SUCCESS:
		var error_msg = "Network error: "
		match result:
			HTTPRequest.RESULT_CHUNKED_BODY_SIZE_MISMATCH:
				error_msg += "Chunked body size mismatch"
			HTTPRequest.RESULT_CANT_CONNECT:
				error_msg += "Can't connect to server"
			HTTPRequest.RESULT_CANT_RESOLVE:
				error_msg += "Can't resolve hostname"
			HTTPRequest.RESULT_CONNECTION_ERROR:
				error_msg += "Connection error"
			HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:
				error_msg += "TLS handshake error"
			HTTPRequest.RESULT_NO_RESPONSE:
				error_msg += "No response from server"
			HTTPRequest.RESULT_BODY_SIZE_LIMIT_EXCEEDED:
				error_msg += "Response too large"
			HTTPRequest.RESULT_BODY_DECOMPRESS_FAILED:
				error_msg += "Failed to decompress response"
			HTTPRequest.RESULT_REQUEST_FAILED:
				error_msg += "Request failed"
			HTTPRequest.RESULT_DOWNLOAD_FILE_CANT_OPEN:
				error_msg += "Can't open download file"
			HTTPRequest.RESULT_DOWNLOAD_FILE_WRITE_ERROR:
				error_msg += "Download file write error"
			HTTPRequest.RESULT_REDIRECT_LIMIT_REACHED:
				error_msg += "Too many redirects"
			HTTPRequest.RESULT_TIMEOUT:
				error_msg += "Request timeout"
			_:
				error_msg += "Unknown error (" + str(result) + ")"
		
		server_logger.log_error("QRLogin", error_msg, {"result": result})
		_show_error(error_msg)
		return
	
	# Check HTTP status code
	if response_code == 200:
		if body.size() > 0:
			var json = JSON.new()
			var parse_result = json.parse(response_text)
			
			if parse_result == OK:
				var data = json.data
				
				if data.has("login_token"):
					# QR start response
					_handle_qr_start_response(data)
				elif data.has("status"):
					# Poll response
					_handle_poll_response(data)
			else:
				_show_error("Failed to parse server response: " + str(parse_result))
		else:
			_show_error("Server returned empty response")
	else:
		server_logger.log_error("QRLogin", "Server error", {"code": response_code, "response": response_text})
		var error_msg = "Server HTTP error: " + str(response_code)
		if response_text.length() > 0:
			error_msg += "\n" + response_text
		_show_error(error_msg)

func _handle_qr_start_response(data: Dictionary):
	"""Handle QR login start response"""
	login_token = data.get("login_token", "")
	qr_url = data.get("qr_url", "")
	var qr_image_url = data.get("qr_image_url", "")
	remaining_time = data.get("expires_in", 300)
	
	server_logger.log_system_event("qr_generated", {
		"token_length": login_token.length(),
		"expires_in": remaining_time
	})
	
	# Create a test placeholder texture to verify TextureRect works
	create_placeholder_texture()
	
	# Load the real QR code image
	if qr_image_url:
		print("📱 Loading QR image from server: ", qr_image_url)
		load_qr_image(qr_image_url)
	else:
		print("❌ No QR image URL provided by server")
		qr_text.text = "❌ Failed to generate QR code - no image URL"
	
	qr_text.text = "📱 SCAN QR CODE WITH PHONE CAMERA"
	status_label.text = "1. Scan QR code with phone camera\n2. Login on your phone\n3. Console will continue automatically"
	
	# Make QR text clickable
	qr_container.gui_input.connect(_on_qr_clicked)
	
	# Start polling
	_start_polling()

func create_placeholder_texture():
	"""Create a placeholder texture to test TextureRect"""
	var image = Image.create(300, 300, false, Image.FORMAT_RGB8)
	image.fill(Color.DARK_GRAY)
	
	# Draw a simple pattern
	for x in range(50, 250, 20):
		for y in range(50, 250, 20):
			image.set_pixel(x, y, Color.WHITE)
	
	var texture = ImageTexture.new()
	texture.set_image(image)
	qr_image.texture = texture
	print("🔲 Placeholder texture created and assigned")

func load_qr_image(image_url: String):
	"""Load QR code image from server"""
	print("📱 Loading QR image from: ", image_url)
	
	# Create HTTP request for image
	var image_request = HTTPRequest.new()
	add_child(image_request)
	image_request.request_completed.connect(_on_qr_image_loaded)
	
	# Request the QR code image
	image_request.request(image_url)

func _on_qr_image_loaded(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle QR code image loaded"""
	print("📥 QR Image response - Result: ", result, " Code: ", response_code, " Body size: ", body.size())
	
	if response_code == 200 and body.size() > 0:
		# Create texture from image data
		var image = Image.new()
		var error = image.load_png_from_buffer(body)
		
		print("🖼️ Image load result: ", error, " (OK = ", OK, ")")
		
		if error == OK:
			print("📐 Image size: ", image.get_width(), "x", image.get_height())
			var texture = ImageTexture.new()
			texture.set_image(image)  # Use set_image instead of create_from_image
			qr_image.texture = texture
			qr_image.visible = true  # Make sure it's visible
			print("✅ QR code image loaded and assigned to TextureRect")
			server_logger.log_system_event("qr_image_loaded", {"success": true, "size": body.size()})
		else:
			print("❌ Failed to decode PNG image, error code: ", error)
			qr_text.text = "❌ Failed to decode QR code image"
			server_logger.log_system_event("qr_image_loaded", {"success": false, "error": "image_decode_failed", "error_code": error})
	else:
		print("❌ Failed to download QR image - Code: ", response_code, " Size: ", body.size())
		qr_text.text = "❌ Failed to download QR code (HTTP " + str(response_code) + ")"
		server_logger.log_system_event("qr_image_loaded", {"success": false, "error": "download_failed", "code": response_code, "size": body.size()})



func _handle_poll_response(data: Dictionary):
	"""Handle polling response"""
	var status = data.get("status", "")
	
	if status == "confirmed":
		# Login successful!
		var player_data = data.get("player_data", {})
		_on_login_success(player_data)
	elif status == "pending":
		# Still waiting
		server_logger.log_system_event("qr_poll_pending", {})
	elif status == "expired":
		_on_login_timeout()

func _start_polling():
	"""Start polling for login confirmation"""
	print("📡 Starting login polling")
	is_polling = true
	poll_timer.start()
	_poll_login_status()

func _poll_login_status():
	"""Poll server for login status"""
	if not is_polling or login_token.is_empty():
		return
	
	var headers = device_connection_manager.get_authenticated_headers()
	var url = server_url + "/v1/console-login/poll?login_token=" + login_token
	
	http_request.request(url, headers, HTTPClient.METHOD_GET)

func _process(delta):
	"""Update countdown timer"""
	if is_polling and remaining_time > 0:
		remaining_time -= delta
		var minutes = int(remaining_time / 60)
		var seconds = int(remaining_time) % 60
		timer_label.text = "Time remaining: %d:%02d" % [minutes, seconds]
		
		if remaining_time <= 0:
			_on_login_timeout()

func _on_login_success(player_data: Dictionary):
	"""Handle successful login"""
	print("✅ QR Login successful!")
	is_polling = false
	poll_timer.stop()
	
	server_logger.log_login_attempt("qr_code", true, {
		"player_id": player_data.get("player_id", "unknown"),
		"player_email": player_data.get("email", "unknown")
	})
	
	status_label.text = "✅ Login successful!\nWelcome " + player_data.get("display_name", "Player")
	qr_text.text = "🎉 SUCCESS!"
	
	# Transition to player menu after brief pause
	await get_tree().create_timer(2.0).timeout
	_transition_to_player_menu()

func _on_login_timeout():
	"""Handle login timeout"""
	print("⏰ QR Login timed out")
	is_polling = false
	poll_timer.stop()
	
	server_logger.log_login_attempt("qr_code", false, {"reason": "timeout"})
	_show_error("Login timed out. Please try again.")

func _show_error(error_message: String):
	"""Show error message"""
	status_label.text = "❌ " + error_message
	qr_text.text = "❌ ERROR\n\n" + error_message
	cancel_button.text = "Retry"

func _on_cancel_pressed():
	"""Handle cancel/retry button"""
	print("🔙 Returning to main menu")
	server_logger.log_user_action("qr_login_cancelled", {})
	_transition_to_main_menu()

func _on_qr_clicked(event):
	"""Handle QR code area click"""
	if event is InputEventMouseButton and event.pressed:
		# Copy URL to clipboard (if possible)
		DisplayServer.clipboard_set(qr_url)
		server_logger.log_user_action("qr_url_copied", {"url_length": qr_url.length()})
		status_label.text = "📋 URL copied to clipboard!\nOpen on your phone to login"
		print("📋 QR URL copied to clipboard")

func _transition_to_main_menu():
	"""Return to main menu"""
	server_logger.log_scene_change("qr_login", "main_menu")
	get_tree().change_scene_to_file("res://simple_menu.tscn")

func _transition_to_player_menu():
	"""Go to player menu after successful login"""
	server_logger.log_scene_change("qr_login", "player_menu")
	get_tree().change_scene_to_file("res://player_menu.tscn")

func _input(event):
	"""Handle input"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			_on_cancel_pressed()
		elif event.keycode == KEY_F11:
			# Toggle fullscreen
			if DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
			else:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		elif event.keycode == KEY_F12:
			# Development: Skip to old menu
			server_logger.log_user_action("dev_skip_to_menu", {})
			print("🔧 Development: Skipping to main menu")
			get_tree().change_scene_to_file("res://simple_menu.tscn")
