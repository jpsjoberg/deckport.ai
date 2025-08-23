extends Node

# Device Connection Manager - Handles secure console registration and authentication
# This is the missing piece that ensures the console is properly authenticated before player login

signal device_registered(success: bool, message: String)
signal device_authenticated(success: bool, token: String)
signal connection_tested(success: bool, response: Dictionary)
signal error_occurred(error_type: String, message: String, details: Dictionary)

# Device Identity
var device_uid: String = ""
var device_private_key: CryptoKey
var device_public_key: CryptoKey
var device_token: String = ""
var device_token_expires: float = 0

# Network Configuration
var server_url: String = "http://127.0.0.1:8002"
var backup_urls: Array[String] = ["http://localhost:8002"]
var current_server_url: String = ""

# HTTP Management
var http_request: HTTPRequest
var connection_timeout: float = 15.0
var max_retries: int = 3
var current_retry: int = 0

# Connection State
enum ConnectionState {
	DISCONNECTED,
	TESTING_CONNECTION,
	REGISTERING_DEVICE,
	AUTHENTICATING_DEVICE,
	CONNECTED,
	ERROR
}
var current_state: ConnectionState = ConnectionState.DISCONNECTED

func _ready():
	print("🔐 Device Connection Manager initialized")
	
	# Generate or load device identity
	setup_device_identity()
	
	# Setup HTTP request with proper configuration
	setup_http_request()
	
	# Start connection process
	start_connection_process()

func setup_device_identity():
	"""Generate or load device keys and UID"""
	# Generate a consistent device UID based on system info
	var system_info = OS.get_name() + "_" + str(OS.get_processor_count()) + "_" + str(Time.get_unix_time_from_system())
	var hash_ctx = HashingContext.new()
	hash_ctx.start(HashingContext.HASH_SHA256)
	hash_ctx.update(system_info.to_utf8_buffer())
	var hash_result = hash_ctx.finish()
	device_uid = "DECK_" + Marshalls.raw_to_base64(hash_result).substr(0, 16).replace("/", "").replace("+", "")
	
	print("🆔 Device UID: ", device_uid)
	
	# Load or generate RSA keys
	load_or_generate_keys()

func load_or_generate_keys():
	"""Load existing device keys or generate new RSA keypair"""
	var crypto = Crypto.new()
	
	# Try to load existing keys
	if FileAccess.file_exists("user://device_private_key.pem") and FileAccess.file_exists("user://device_public_key.pem"):
		print("🔑 Loading existing device keys...")
		
		var private_file = FileAccess.open("user://device_private_key.pem", FileAccess.READ)
		var public_file = FileAccess.open("user://device_public_key.pem", FileAccess.READ)
		
		if private_file and public_file:
			var private_pem = private_file.get_as_text()
			var public_pem = public_file.get_as_text()
			private_file.close()
			public_file.close()
			
			device_private_key = CryptoKey.new()
			device_public_key = CryptoKey.new()
			
			if device_private_key.load_from_string(private_pem) == OK and device_public_key.load_from_string(public_pem) == OK:
				print("✅ Device keys loaded successfully")
				return
			else:
				print("❌ Failed to load existing keys, generating new ones")
	
	# Generate new RSA keypair
	print("🔐 Generating new RSA keypair (2048-bit)...")
	device_private_key = crypto.generate_rsa(2048)
	device_public_key = device_private_key.get_public_key()
	
	# Save keys to persistent storage
	var private_pem = device_private_key.save_to_string()
	var public_pem = device_public_key.save_to_string()
	
	var private_file = FileAccess.open("user://device_private_key.pem", FileAccess.WRITE)
	var public_file = FileAccess.open("user://device_public_key.pem", FileAccess.WRITE)
	
	if private_file and public_file:
		private_file.store_string(private_pem)
		public_file.store_string(public_pem)
		private_file.close()
		public_file.close()
		print("💾 Device keys saved to persistent storage")
	else:
		print("⚠️ Warning: Could not save device keys to storage")
	
	print("✅ RSA keypair generated successfully")

func setup_http_request():
	"""Configure HTTPRequest with optimal settings for Godot 4.4+"""
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_http_response)
	
	# Optimal configuration for Godot 4.4+
	http_request.timeout = connection_timeout
	http_request.use_threads = true  # Enable threading for better performance
	http_request.accept_gzip = true  # Enable compression
	
	# Allow insecure connections for localhost development
	http_request.set_tls_options(TLSOptions.client_unsafe())
	
	print("📡 HTTPRequest configured:")
	print("  Timeout: ", http_request.timeout, "s")
	print("  Threading: ", http_request.use_threads)
	print("  Compression: ", http_request.accept_gzip)

func start_connection_process():
	"""Start the complete connection process"""
	print("🚀 Starting device connection process...")
	current_state = ConnectionState.TESTING_CONNECTION
	current_retry = 0
	test_server_connection()

func test_server_connection():
	"""Test basic connectivity to server"""
	print("🔍 Testing server connection...")
	
	# Try primary server URL first
	current_server_url = server_url
	
	var headers = [
		"Content-Type: application/json",
		"User-Agent: Deckport-Console/1.0 (Godot/" + Engine.get_version_info().string + ")",
		"X-Device-UID: " + device_uid
	]
	
	var url = current_server_url + "/health"
	print("📡 Testing: ", url)
	
	var error = http_request.request(url, headers, HTTPClient.METHOD_GET)
	if error != OK:
		_handle_connection_error("HTTP request failed", {"error_code": error, "url": url})

func register_device():
	"""Register device with server using public key"""
	print("📝 Registering device with server...")
	current_state = ConnectionState.REGISTERING_DEVICE
	
	var public_key_pem = device_public_key.save_to_string()
	
	var registration_data = {
		"device_uid": device_uid,
		"public_key": public_key_pem,
		"device_info": {
			"platform": OS.get_name(),
			"version": Engine.get_version_info().string,
			"processor_count": OS.get_processor_count()
		}
	}
	
	var headers = [
		"Content-Type: application/json",
		"User-Agent: Deckport-Console/1.0",
		"X-Device-UID: " + device_uid
	]
	
	var json_string = JSON.stringify(registration_data)
	var url = current_server_url + "/v1/auth/device/register"
	
	print("📡 Sending registration to: ", url)
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, json_string)
	if error != OK:
		_handle_connection_error("Device registration failed", {"error_code": error, "url": url})

func authenticate_device():
	"""Authenticate device using RSA signature"""
	print("🔐 Authenticating device with server...")
	current_state = ConnectionState.AUTHENTICATING_DEVICE
	
	# Generate nonce for signing
	var crypto = Crypto.new()
	var nonce_bytes = crypto.generate_random_bytes(32)
	var nonce = Marshalls.raw_to_base64(nonce_bytes)
	
	# Sign the nonce
	var signature_bytes = crypto.sign(HashingContext.HASH_SHA256, nonce.to_utf8_buffer(), device_private_key)
	var signature = Marshalls.raw_to_base64(signature_bytes)
	
	var auth_data = {
		"device_uid": device_uid,
		"nonce": nonce,
		"signature": signature
	}
	
	var headers = [
		"Content-Type: application/json",
		"User-Agent: Deckport-Console/1.0",
		"X-Device-UID: " + device_uid
	]
	
	var json_string = JSON.stringify(auth_data)
	var url = current_server_url + "/v1/auth/device/login"
	
	print("📡 Sending authentication to: ", url)
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, json_string)
	if error != OK:
		_handle_connection_error("Device authentication failed", {"error_code": error, "url": url})

func _on_http_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle all HTTP responses based on current state"""
	var response_text = body.get_string_from_utf8()
	
	print("📡 HTTP Response - State: ", ConnectionState.keys()[current_state])
	print("  Result: ", result, " Code: ", response_code)
	print("  Body: ", response_text)
	
	# Check for network errors
	if result != HTTPRequest.RESULT_SUCCESS:
		_handle_network_error(result, response_code)
		return
	
	# Parse JSON response
	var json = JSON.new()
	var parse_result = json.parse(response_text)
	var data = {}
	
	if parse_result == OK and json.data is Dictionary:
		data = json.data
	
	# Handle response based on current state
	match current_state:
		ConnectionState.TESTING_CONNECTION:
			_handle_connection_test_response(response_code, data)
		ConnectionState.REGISTERING_DEVICE:
			_handle_registration_response(response_code, data)
		ConnectionState.AUTHENTICATING_DEVICE:
			_handle_authentication_response(response_code, data)

func _handle_connection_test_response(response_code: int, data: Dictionary):
	"""Handle server connection test response"""
	if response_code == 200:
		print("✅ Server connection successful!")
		connection_tested.emit(true, data)
		
		# Check if we have a valid device token
		if device_token.is_empty() or Time.get_unix_time_from_system() > device_token_expires:
			# Need to register/authenticate device
			register_device()
		else:
			# Already authenticated
			current_state = ConnectionState.CONNECTED
			device_authenticated.emit(true, device_token)
	else:
		_handle_connection_error("Server health check failed", {"code": response_code, "data": data})

func _handle_registration_response(response_code: int, data: Dictionary):
	"""Handle device registration response"""
	if response_code == 201:
		var status = data.get("status", "unknown")
		if status == "pending":
			print("⏳ Device registration pending admin approval")
			device_registered.emit(true, "Registration pending admin approval")
			# For now, continue to authentication (in development)
			authenticate_device()
		else:
			print("✅ Device registered successfully")
			device_registered.emit(true, "Device registered successfully")
			authenticate_device()
	elif response_code == 409:
		print("ℹ️ Device already registered, proceeding to authentication")
		device_registered.emit(true, "Device already registered")
		authenticate_device()
	else:
		var error_msg = data.get("error", "Registration failed")
		_handle_connection_error("Device registration failed", {"code": response_code, "error": error_msg})

func _handle_authentication_response(response_code: int, data: Dictionary):
	"""Handle device authentication response"""
	if response_code == 200:
		device_token = data.get("access_token", "")
		var expires_in = data.get("expires_in", 86400)
		device_token_expires = Time.get_unix_time_from_system() + expires_in
		
		print("✅ Device authenticated successfully!")
		print("🎫 Device token expires in: ", expires_in, " seconds")
		
		current_state = ConnectionState.CONNECTED
		device_authenticated.emit(true, device_token)
	else:
		var error_msg = data.get("error", "Authentication failed")
		_handle_connection_error("Device authentication failed", {"code": response_code, "error": error_msg})

func _handle_network_error(result: int, response_code: int):
	"""Handle network-level errors with detailed logging"""
	var error_msg = "Network error: "
	match result:
		HTTPRequest.RESULT_CANT_CONNECT:
			error_msg += "Cannot connect to server"
		HTTPRequest.RESULT_CANT_RESOLVE:
			error_msg += "Cannot resolve hostname"
		HTTPRequest.RESULT_CONNECTION_ERROR:
			error_msg += "Connection error"
		HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:
			error_msg += "TLS handshake failed"
		HTTPRequest.RESULT_NO_RESPONSE:
			error_msg += "No response from server"
		HTTPRequest.RESULT_TIMEOUT:
			error_msg += "Request timeout"
		_:
			error_msg += "Unknown error (" + str(result) + ")"
	
	_handle_connection_error(error_msg, {"result": result, "response_code": response_code})

func _handle_connection_error(error_msg: String, details: Dictionary):
	"""Handle connection errors with retry logic"""
	print("❌ ", error_msg)
	print("🔍 Details: ", details)
	
	current_retry += 1
	
	if current_retry < max_retries:
		print("🔄 Retrying... (", current_retry, "/", max_retries, ")")
		await get_tree().create_timer(2.0).timeout
		
		# Try backup URL if available
		if current_retry == 2 and backup_urls.size() > 0:
			current_server_url = backup_urls[0]
			print("🔄 Switching to backup server: ", current_server_url)
		
		# Retry based on current state
		match current_state:
			ConnectionState.TESTING_CONNECTION:
				test_server_connection()
			ConnectionState.REGISTERING_DEVICE:
				register_device()
			ConnectionState.AUTHENTICATING_DEVICE:
				authenticate_device()
	else:
		# Max retries reached
		current_state = ConnectionState.ERROR
		error_occurred.emit("connection_failed", error_msg, details)
		print("💥 Max retries reached. Connection failed.")

# Public API
func is_connected() -> bool:
	"""Check if device is properly connected and authenticated"""
	return current_state == ConnectionState.CONNECTED and not device_token.is_empty()

func get_device_token() -> String:
	"""Get current device token for API requests"""
	return device_token

func get_authenticated_headers() -> Array[String]:
	"""Get headers with device authentication"""
	return [
		"Content-Type: application/json",
		"Authorization: Bearer " + device_token,
		"X-Device-UID: " + device_uid,
		"User-Agent: Deckport-Console/1.0"
	]

func force_reconnect():
	"""Force a reconnection process"""
	print("🔄 Forcing reconnection...")
	device_token = ""
	device_token_expires = 0
	current_retry = 0
	start_connection_process()
