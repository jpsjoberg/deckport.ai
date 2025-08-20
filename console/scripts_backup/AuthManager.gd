extends Node

# Console Authentication Manager
# Handles device registration, device authentication, and player login

signal device_authenticated(success: bool)
signal player_authenticated(player_data: Dictionary)
signal authentication_error(error: String)

# Device Authentication
var device_private_key: CryptoKey
var device_public_key: CryptoKey
var device_token: String = ""
var device_token_expires: float = 0

# Player Authentication  
var player_token: String = ""
var player_data: Dictionary = {}
var current_login_token: String = ""

# Network
var http_request: HTTPRequest

func _ready():
	Logger.log_info("AuthManager", "Authentication manager initialized")
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)
	
	# Load or generate device keys
	load_or_generate_device_keys()

func load_or_generate_device_keys():
	"""Load existing device keys or generate new ones"""
	var crypto = Crypto.new()
	
	# Try to load existing keys
	if FileAccess.file_exists("user://device_private_key.pem") and FileAccess.file_exists("user://device_public_key.pem"):
		Logger.log_info("AuthManager", "Loading existing device keys")
		
		var existing_private_file = FileAccess.open("user://device_private_key.pem", FileAccess.READ)
		var existing_public_file = FileAccess.open("user://device_public_key.pem", FileAccess.READ)
		
		if existing_private_file and existing_public_file:
			var private_pem = existing_private_file.get_as_text()
			var public_pem = existing_public_file.get_as_text()
			
			device_private_key = CryptoKey.new()
			device_public_key = CryptoKey.new()
			
			# Try to load keys, handle errors gracefully
			var private_load_result = device_private_key.load_from_string(private_pem)
			var public_load_result = device_public_key.load_from_string(public_pem)
			
			if private_load_result != OK or public_load_result != OK:
				Logger.log_warning("AuthManager", "Failed to load existing keys, regenerating")
				existing_private_file.close()
				existing_public_file.close()
				# Fall through to generate new keys
			else:
				existing_private_file.close()
				existing_public_file.close()
				Logger.log_info("AuthManager", "Device keys loaded successfully")
				return
	
	# Generate new keys if not found
	Logger.log_info("AuthManager", "Generating new device keys")
	
	# For development, skip complex crypto and use mock keys
	if Global.is_development():
		Logger.log_warning("AuthManager", "Using mock device keys for development")
		device_private_key = CryptoKey.new()
		device_public_key = CryptoKey.new()
		# Don't try to save invalid keys
		Logger.log_info("AuthManager", "Mock device keys generated")
		return
	
	device_private_key = crypto.generate_rsa(2048)
	# TODO: Fix public key extraction for Godot 4.x
	# device_public_key = device_private_key.get_public_key()  # ❌ Not available in Godot 4.x
	device_public_key = CryptoKey.new()  # Placeholder for now
	
	# Save keys
	var private_file = FileAccess.open("user://device_private_key.pem", FileAccess.WRITE)
	var public_file = FileAccess.open("user://device_public_key.pem", FileAccess.WRITE)
	
	if private_file and public_file:
		var private_key_pem = device_private_key.save_to_string()
		private_file.store_string(private_key_pem)
		
		# Extract public key from private key PEM (workaround for Godot 4.x)
		var public_key_pem = _extract_public_key_from_private_pem(private_key_pem)
		public_file.store_string(public_key_pem)
		
		private_file.close()
		public_file.close()
		Logger.log_info("AuthManager", "New device keys generated and saved")
	else:
		Logger.log_error("AuthManager", "Failed to save device keys")

func _extract_public_key_from_private_pem(_private_key_pem: String) -> String:
	"""Extract public key from private key PEM (Godot 4.x workaround)"""
	# For development, return a mock public key
	# TODO: Implement proper public key extraction
	var mock_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890ABCDEF
GHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890ABCD
EFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890AB
CDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890
ABCDEFGHIJKLMNOPQRSTUVWXYZ
-----END PUBLIC KEY-----"""
	
	Logger.log_warning("AuthManager", "Using mock public key for development")
	return mock_public_key

func register_device():
	"""Register this console device with the server (one-time setup)"""
	Logger.log_info("AuthManager", "Starting device registration")
	
	# Get public key PEM (using workaround for Godot 4.x)
	var private_key_pem = device_private_key.save_to_string()
	var public_key_pem = _extract_public_key_from_private_pem(private_key_pem)
	var request_data = {
		"device_uid": Global.device_uid,
		"public_key": public_key_pem
	}
	
	var json = JSON.stringify(request_data)
	var headers = ["Content-Type: application/json"]
	
	var url = Global.get_api_url("/v1/auth/device/register")
	http_request.request(url, headers, HTTPClient.METHOD_POST, json)
	
	Logger.log_info("AuthManager", "Device registration request sent")

func authenticate_device():
	"""Authenticate device with server using signed nonce"""
	Logger.log_info("AuthManager", "Starting device authentication")
	
	# Note: This is DEVICE authentication (console hardware)
	# Player authentication happens later via QR code flow
	
	# For development, use mock device authentication
	if Global.is_development():
		Logger.log_warning("AuthManager", "Using mock device authentication for development")
		# Simulate successful device authentication
		await get_tree().create_timer(0.5).timeout
		Global.device_token = "mock_device_token_" + Global.device_uid
		device_authenticated.emit(true)
		return
	
	# Check if we have valid keys
	if not device_private_key:
		Logger.log_error("AuthManager", "No private key available for authentication")
		authentication_error.emit("No device keys")
		return
	
	# Generate nonce
	var crypto = Crypto.new()
	var nonce_bytes = crypto.generate_random_bytes(32)
	var nonce = Marshalls.raw_to_base64(nonce_bytes)
	
	# Create hash of nonce for signing
	var hash_ctx = HashingContext.new()
	hash_ctx.start(HashingContext.HASH_SHA256)
	hash_ctx.update(nonce.to_utf8_buffer())
	var nonce_hash = hash_ctx.finish()
	
	# Sign the hash
	var signature_bytes = crypto.sign(HashingContext.HASH_SHA256, nonce_hash, device_private_key)
	if signature_bytes.is_empty():
		Logger.log_error("AuthManager", "Failed to sign nonce")
		authentication_error.emit("Signature generation failed")
		return
		
	var signature = Marshalls.raw_to_base64(signature_bytes)
	
	var request_data = {
		"device_uid": Global.device_uid,
		"nonce": nonce,
		"signature": signature
	}
	
	var json = JSON.stringify(request_data)
	var headers = ["Content-Type: application/json"]
	
	var url = Global.get_api_url("/v1/auth/device/login")
	http_request.request(url, headers, HTTPClient.METHOD_POST, json)
	
	Logger.log_info("AuthManager", "Device authentication request sent")

func start_player_login():
	"""Start QR code login flow for player"""
	Logger.log_info("AuthManager", "Starting player login flow")
	
	if device_token == "":
		Logger.log_error("AuthManager", "Device not authenticated - cannot start player login")
		authentication_error.emit("Device not authenticated")
		return
	
	var headers = [
		"Content-Type: application/json",
		"Authorization: Bearer " + device_token
	]
	
	var url = Global.get_api_url("/v1/console-login/start")
	http_request.request(url, headers, HTTPClient.METHOD_POST, "{}")

func poll_player_login():
	"""Poll server for player login confirmation"""
	if current_login_token == "":
		Logger.log_error("AuthManager", "No login token available for polling")
		return
	
	var headers = ["Authorization: Bearer " + device_token]
	var url = Global.get_api_url("/v1/console-login/poll?login_token=" + current_login_token)
	
	http_request.request(url, headers, HTTPClient.METHOD_GET)

func _on_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP request completion"""
	var response_text = body.get_string_from_utf8()
	Logger.log_info("AuthManager", "HTTP response received", {"code": response_code, "body_length": body.size()})
	
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(response_text)
		
		if parse_result == OK:
			var data = json.data
			_handle_successful_response(data)
		else:
			Logger.log_error("AuthManager", "Failed to parse JSON response")
			authentication_error.emit("Invalid server response")
	else:
		Logger.log_error("AuthManager", "HTTP request failed", {"code": response_code, "response": response_text})
		_handle_error_response(response_code, response_text)

func _handle_successful_response(data: Dictionary):
	"""Handle successful API responses"""
	Logger.log_info("AuthManager", "Processing successful response", {"keys": data.keys()})
	
	# Device registration response
	if data.has("status") and data.status == "pending":
		Logger.log_info("AuthManager", "Device registration pending admin approval")
		Global.log_event("device_registration_pending")
		return
	
	# Device authentication response
	if data.has("access_token"):
		device_token = data.access_token
		device_token_expires = Time.get_unix_time_from_system() + data.get("expires_in", 86400)
		Global.device_token = device_token
		Logger.log_info("AuthManager", "Device authenticated successfully")
		device_authenticated.emit(true)
		return
	
	# Player login start response
	if data.has("login_token") and data.has("qr_url"):
		current_login_token = data.login_token
		Logger.log_info("AuthManager", "Player login QR generated", {"qr_url": data.qr_url})
		# Signal to display QR code
		Global.log_event("player_login_qr_generated", {"qr_url": data.qr_url})
		# Start polling for confirmation
		_start_login_polling()
		return
	
	# Player login poll response
	if data.has("status"):
		if data.status == "confirmed" and data.has("player_jwt"):
			player_token = data.player_jwt
			Global.player_token = player_token
			# TODO: Decode JWT to get player info
			Logger.log_info("AuthManager", "Player authenticated successfully")
			player_authenticated.emit(data)
		elif data.status == "pending":
			# Continue polling
			await get_tree().create_timer(2.0).timeout
			poll_player_login()

func _handle_error_response(code: int, response: String):
	"""Handle API error responses"""
	var error_message = "Authentication failed"
	
	match code:
		401:
			error_message = "Authentication denied"
		403:
			error_message = "Device not approved"
		404:
			error_message = "Service not found"
		409:
			error_message = "Device already registered"
		500:
			error_message = "Server error"
	
	Logger.log_error("AuthManager", error_message, {"code": code, "response": response})
	authentication_error.emit(error_message)

func _start_login_polling():
	"""Start polling for player login confirmation"""
	Logger.log_info("AuthManager", "Starting login polling")
	await get_tree().create_timer(1.0).timeout
	poll_player_login()

func is_device_authenticated() -> bool:
	"""Check if device is currently authenticated"""
	return device_token != "" and Time.get_unix_time_from_system() < device_token_expires

func is_player_authenticated() -> bool:
	"""Check if player is currently authenticated"""
	return player_token != ""

func logout_player():
	"""Logout current player"""
	Logger.log_info("AuthManager", "Player logged out")
	player_token = ""
	player_data = {}
	current_login_token = ""
	Global.player_token = ""
	Global.player_id = 0
	Global.player_email = ""
	Global.player_display_name = ""

func get_device_headers() -> Array:
	"""Get headers for device-authenticated requests"""
	return ["Authorization: Bearer " + device_token, "Content-Type: application/json"]

func get_player_headers() -> Array:
	"""Get headers for player-authenticated requests"""
	return ["Authorization: Bearer " + player_token, "Content-Type: application/json"]
