extends Control

# QR Code Login Scene
# Shows QR code for player to scan and login with phone

signal login_successful(player_data: Dictionary)
signal login_cancelled()
signal login_failed(error: String)

@onready var qr_code_image = $CenterContainer/VBoxContainer/QRCodeContainer/QRCodeImage
#@onready var qr_code_text = $CenterContainer/VBoxContainer/QRCodeContainer/QRCodeText
#@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var progress_bar = $CenterContainer/VBoxContainer/ProgressBar
@onready var cancel_button = $CancelButton
@onready var http_request = $HTTPRequest
@onready var poll_timer = $PollTimer

var login_token: String = ""
var qr_url: String = ""
var expires_at: String = ""
var remaining_time: float = 300.0  # 5 minutes
var is_polling: bool = false

func _ready():
	Logger.log_info("QRLogin", "QR Login scene loaded")
	Global.current_scene = "QRLogin"
	
	# Connect signals
	cancel_button.pressed.connect(_on_cancel_pressed)
	http_request.request_completed.connect(_on_http_request_completed)
	poll_timer.timeout.connect(_on_poll_timer_timeout)
	login_successful.connect(_on_login_successful_signal)
	
	# Start QR login flow
	start_qr_login()

func _on_login_successful_signal(player_data: Dictionary):
	"""Handle login successful signal"""
	# Transition to main menu
	await get_tree().create_timer(1.0).timeout  # Brief pause to show success
	transition_to_main_menu()

func _process(delta):
	"""Update countdown timer"""
	if is_polling and remaining_time > 0:
		remaining_time -= delta
		progress_bar.value = remaining_time
		
		var minutes = int(remaining_time / 60)
		var seconds = int(remaining_time) % 60
		status_label.text = "Waiting for login... %d:%02d" % [minutes, seconds]
		
		if remaining_time <= 0:
			_on_login_timeout()

func start_qr_login():
	"""Start the QR code login flow"""
	Logger.log_info("QRLogin", "Starting QR login flow")
	status_label.text = "Generating QR code..."
	
	# Call /v1/console-login/start
	var headers = ["Content-Type: application/json"]
	
	# Add device authentication if available
	if Global.device_token:
		headers.append("Authorization: Bearer " + Global.device_token)
	else:
		# Fallback for development
		headers.append("X-Device-UID: " + Global.device_uid)
	
	var url = Global.get_api_url("/v1/console-login/start")
	var body = "{}"
	
	http_request.request(url, headers, HTTPClient.METHOD_POST, body)
	Logger.log_info("QRLogin", "QR login request sent")

func _on_http_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP response"""
	var response_text = body.get_string_from_utf8()
	Logger.log_info("QRLogin", "HTTP response received", {"code": response_code})
	
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(response_text)
		
		if parse_result == OK:
			var data = json.data
			
			# Check if this is a QR start response or poll response
			if data.has("login_token"):
				# QR start response
				login_token = data.get("login_token", "")
				qr_url = data.get("qr_url", "")
				expires_at = data.get("expires_at", "")
				remaining_time = data.get("expires_in", 300)
				
				Logger.log_info("QRLogin", "QR login started successfully")
				_show_qr_code()
				_start_polling()
			elif data.has("status"):
				# Poll response
				var status = data.get("status", "")
				if status == "confirmed":
					# Login successful!
					var player_data = data.get("player_data", {})
					_on_login_success(player_data)
				elif status == "pending":
					# Still waiting
					Logger.log_debug("QRLogin", "Still waiting for login confirmation")
				elif status == "expired":
					_on_login_timeout()
		else:
			Logger.log_error("QRLogin", "Failed to parse response")
			_show_error("Failed to parse server response")
	else:
		Logger.log_error("QRLogin", "Request failed", {"code": response_code, "body": response_text})
		_show_error("Server error: " + str(response_code))

func _show_qr_code():
	"""Display the QR code"""
	# For now, show the URL as text
	# TODO: Generate actual QR code image
	qr_code_text.text = "Scan with phone:\n\n" + qr_url
	status_label.text = "Scan QR code with your phone"
	progress_bar.max_value = remaining_time
	progress_bar.value = remaining_time

func _start_polling():
	"""Start polling for login confirmation"""
	Logger.log_info("QRLogin", "Starting login polling")
	is_polling = true
	poll_timer.start()
	_poll_login_status()

func _poll_login_status():
	"""Poll the server for login confirmation"""
	if not is_polling or login_token.is_empty():
		return
	
	var headers = ["Content-Type: application/json"]
	
	# Add device authentication
	if Global.device_token:
		headers.append("Authorization: Bearer " + Global.device_token)
	else:
		headers.append("X-Device-UID: " + Global.device_uid)
	
	var url = Global.get_api_url("/v1/console-login/poll?login_token=" + login_token)
	http_request.request(url, headers, HTTPClient.METHOD_GET)

func _on_poll_timer_timeout():
	"""Handle poll timer timeout"""
	if is_polling:
		_poll_login_status()

func _on_login_success(player_data: Dictionary):
	"""Handle successful login"""
	Logger.log_info("QRLogin", "Player login successful")
	is_polling = false
	poll_timer.stop()
	
	# Store player data
	Global.player_id = player_data.get("player_id", 0)
	Global.player_email = player_data.get("email", "")
	Global.player_display_name = player_data.get("display_name", "Player")
	Global.player_elo = player_data.get("elo", 1000)
	Global.player_token = player_data.get("access_token", "")
	
	status_label.text = "Login successful! Loading..."
	login_successful.emit(player_data)

func _on_login_timeout():
	"""Handle login timeout"""
	Logger.log_warning("QRLogin", "QR login timed out")
	is_polling = false
	poll_timer.stop()
	_show_error("Login timed out. Please try again.")

func _show_error(error_message: String):
	"""Show error message"""
	status_label.text = error_message
	qr_code_text.text = "❌ ERROR\n\n" + error_message
	cancel_button.text = "Retry"

func _on_cancel_pressed():
	"""Handle cancel button press"""
	Logger.log_info("QRLogin", "QR login cancelled by user")
	is_polling = false
	poll_timer.stop()
	login_cancelled.emit()

func transition_to_main_menu():
	"""Transition to main menu after successful login"""
	Logger.log_info("QRLogin", "Transitioning to main menu")
	
	# Fade out
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	await tween.finished
	
	# Change scene
	get_tree().change_scene_to_file("res://scenes/MainMenu.tscn")
