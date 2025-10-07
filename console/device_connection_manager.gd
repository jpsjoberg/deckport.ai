extends Node

# Device Connection Manager - Handles secure console registration and authentication
# This is the missing piece that ensures the console is properly authenticated before player login

signal device_registered(success: bool, message: String)
signal device_authenticated(success: bool, token: String)
signal connection_verified(success: bool, response: Dictionary)
signal error_occurred(error_type: String, message: String, details: Dictionary)

# Device Identity
var device_uid: String = ""
var device_private_key: CryptoKey
var device_public_key: CryptoKey
var device_token: String = ""
var device_token_expires: float = 0

# Network Configuration
var server_url: String = "https://deckport.ai"
var backup_urls: Array[String] = ["https://deckport.ai"]
var current_server_url: String = ""

# HTTP Management
var http_request: HTTPRequest
var connection_timeout: float = 15.0
var max_retries: int = 3
var current_retry: int = 0

# Connection State
enum ConnectionState {
	DISCONNECTED,
	VERIFYING_CONNECTION,
	REGISTERING_DEVICE,
	AUTHENTICATING_DEVICE,
	PENDING_APPROVAL,
	CHECKING_STATUS,
	CONNECTED,
	ERROR
}
var current_state: ConnectionState = ConnectionState.DISCONNECTED
var approval_check_timer: Timer

func _ready():
	print("🔐 Device Connection Manager initialized")
	
	# Create approval check timer
	approval_check_timer = Timer.new()
	approval_check_timer.wait_time = 10.0  # Check every 10 seconds
	approval_check_timer.timeout.connect(_check_approval_status)
	add_child(approval_check_timer)
	
	# Generate or load device identity
	setup_device_identity()
	
	# Setup HTTP request with proper configuration
	setup_http_request()
	
	# Start connection process
	start_connection_process()

func setup_device_identity():
	"""Generate or load device keys and UID"""
	# Load or generate persistent device UID
	load_or_generate_device_uid()
	
	print("🆔 Device UID: ", device_uid)
	
	# Load or generate RSA keys
	load_or_generate_keys()

func load_or_generate_device_uid():
	"""Load existing device UID or generate new one (persistent across restarts)"""
	var uid_file_handle  # Declare at function level to avoid scope warning
	
	# Try to load existing device UID from persistent storage
	if FileAccess.file_exists("user://device_uid.txt"):
		print("🆔 Loading existing device UID...")
		uid_file_handle = FileAccess.open("user://device_uid.txt", FileAccess.READ)
		if uid_file_handle:
			device_uid = uid_file_handle.get_as_text().strip_edges()
			uid_file_handle.close()
			
			# Validate the loaded UID format
			if device_uid.begins_with("DECK_") and device_uid.length() > 5:
				print("✅ Device UID loaded successfully: ", device_uid)
				return
			else:
				print("⚠️ Invalid device UID format, generating new one")
	
	# Generate new device UID (only happens once per console)
	print("🔐 Generating new persistent device UID...")
	
	# Use system info without timestamp for consistent generation
	var system_info = OS.get_name() + "_" + str(OS.get_processor_count()) + "_" + OS.get_unique_id()
	var hash_ctx = HashingContext.new()
	hash_ctx.start(HashingContext.HASH_SHA256)
	hash_ctx.update(system_info.to_utf8_buffer())
	var hash_result = hash_ctx.finish()
	device_uid = "DECK_" + Marshalls.raw_to_base64(hash_result).substr(0, 16).replace("/", "").replace("+", "")
	
	# Save device UID to persistent storage
	uid_file_handle = FileAccess.open("user://device_uid.txt", FileAccess.WRITE)
	if uid_file_handle:
		uid_file_handle.store_string(device_uid)
		uid_file_handle.close()
		print("💾 Device UID saved to persistent storage")
	else:
		print("⚠️ Warning: Could not save device UID to storage")
	
	print("✅ New device UID generated: ", device_uid)

func load_or_generate_keys():
	"""Load existing device keys or generate new RSA keypair"""
	var crypto = Crypto.new()
	
	# Try to load existing keys
	if FileAccess.file_exists("user://device_private_key.pem") and FileAccess.file_exists("user://device_public_key.pem"):
		print("🔑 Loading existing device keys...")
		
		var private_file_handle = FileAccess.open("user://device_private_key.pem", FileAccess.READ)
		var public_file_handle = FileAccess.open("user://device_public_key.pem", FileAccess.READ)
		
		if private_file_handle and public_file_handle:
			var private_pem_content = private_file_handle.get_as_text()
			var public_pem_content = public_file_handle.get_as_text()
			private_file_handle.close()
			public_file_handle.close()
			
			device_private_key = CryptoKey.new()
			device_public_key = CryptoKey.new()
			
			if device_private_key.load_from_string(private_pem_content) == OK and device_public_key.load_from_string(public_pem_content) == OK:
				print("✅ Device keys loaded successfully")
				return
			else:
				print("❌ Failed to load existing keys, generating new ones")
	
	# Generate new RSA keypair
	print("🔐 Generating new RSA keypair (2048-bit)...")
	device_private_key = crypto.generate_rsa(2048)
	
	# For Godot 4.4+, we need to create a separate public key
	# by loading the private key and using it for public operations
	device_public_key = CryptoKey.new()
	var private_pem_data = device_private_key.save_to_string()
	
	# Load the private key data into the public key object
	# This allows us to use it for verification operations
	if device_public_key.load_from_string(private_pem_data) != OK:
		print("❌ Failed to create public key from private key")
		return
	
	# Save keys to persistent storage
	var public_pem_data = private_pem_data  # Same data, different usage
	
	var private_file_save = FileAccess.open("user://device_private_key.pem", FileAccess.WRITE)
	var public_file_save = FileAccess.open("user://device_public_key.pem", FileAccess.WRITE)
	
	if private_file_save and public_file_save:
		private_file_save.store_string(private_pem_data)
		public_file_save.store_string(public_pem_data)
		private_file_save.close()
		public_file_save.close()
		print("💾 Device keys saved to persistent storage")
	else:
		print("⚠️ Warning: Could not save device keys to storage")
	
	print("✅ RSA keypair generated successfully")

# Public key extraction function removed - server handles this

func _show_pending_approval_message():
	"""Show message that device is pending admin approval"""
	print("📋 Device registration complete - waiting for admin approval")
	print("💡 Admin can approve this device in the admin panel")
	print("🆔 Device UID: ", device_uid)
	
	# Emit a signal that can be used by the UI to show appropriate message
	device_authenticated.emit(false, "pending_approval")

func get_device_uid() -> String:
	"""Get the device UID"""
	return device_uid

func get_auth_headers() -> Array[String]:
	"""Get headers with device authentication"""
	var headers = [
		"Content-Type: application/json",
		"User-Agent: Deckport-Console/1.0",
		"X-Device-UID: " + device_uid
	]
	
	if not device_token.is_empty():
		headers.append("Authorization: Bearer " + device_token)
	
	return headers

func is_authenticated() -> bool:
	"""Check if device is authenticated and token is valid"""
	return current_state == ConnectionState.CONNECTED and not device_token.is_empty() and Time.get_unix_time_from_system() < device_token_expires

func _check_approval_status():
	"""Check if device has been approved by admin"""
	if current_state != ConnectionState.PENDING_APPROVAL:
		approval_check_timer.stop()
		return
	
	print("🔍 Checking approval status...")
	
	# Use the status endpoint to check current device status
	var headers = [
		"Content-Type: application/json",
		"User-Agent: Deckport-Console/1.0 (Godot/" + Engine.get_version_info().string + ")",
		"X-Device-UID: " + device_uid
	]
	
	var url = current_server_url + "/v1/auth/device/status?device_uid=" + device_uid
	print("📡 Checking status at: ", url)
	
	# Set state to checking status
	current_state = ConnectionState.CHECKING_STATUS
	
	var error = http_request.request(url, headers, HTTPClient.METHOD_GET)
	if error != OK:
		print("❌ Status check request failed: ", error)
		# Return to pending approval state to try again
		current_state = ConnectionState.PENDING_APPROVAL

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
	current_state = ConnectionState.VERIFYING_CONNECTION
	current_retry = 0
	verify_server_connection()

func verify_server_connection():
	"""Verify basic connectivity to server"""
	print("🔍 Verifying server connection...")
	
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
	
	# Send private key to server (server will extract public key)
	# This is necessary because Godot 4.4+ doesn't have easy public key extraction
	var public_key_pem = device_private_key.save_to_string()
	
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
	
	# Create hash of the nonce (required for RSA signing)
	var hash_context = HashingContext.new()
	hash_context.start(HashingContext.HASH_SHA256)
	hash_context.update(nonce.to_utf8_buffer())
	var nonce_hash = hash_context.finish()
	
	# Sign the hash
	var signature_bytes = crypto.sign(HashingContext.HASH_SHA256, nonce_hash, device_private_key)
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

func _on_http_response(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray):
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
		ConnectionState.VERIFYING_CONNECTION:
			_handle_connection_verification_response(response_code, data)
		ConnectionState.REGISTERING_DEVICE:
			_handle_registration_response(response_code, data)
		ConnectionState.AUTHENTICATING_DEVICE:
			_handle_authentication_response(response_code, data)
		ConnectionState.CHECKING_STATUS:
			_handle_status_check_response(response_code, data)

func _handle_connection_verification_response(response_code: int, data: Dictionary):
	"""Handle server connection verification response"""
	if response_code == 200:
		print("✅ Server connection successful!")
		connection_verified.emit(true, data)
		
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
	if response_code == 201 or response_code == 200:  # Accept both new registration (201) and existing pending (200)
		var status = data.get("status", "unknown")
		if status == "pending":
			print("⏳ Device registration pending admin approval")
			print("🔄 Console will wait for admin approval before proceeding")
			device_registered.emit(true, "Registration pending admin approval")
			current_state = ConnectionState.PENDING_APPROVAL  # Set to pending approval state
			# Start checking for approval
			approval_check_timer.start()
			_show_pending_approval_message()
		elif status == "approved" or status == "active":
			print("✅ Device approved! Proceeding with authentication...")
			approval_check_timer.stop()  # Stop checking
			device_registered.emit(true, "Device approved")
			authenticate_device()
		else:
			print("✅ Device registered successfully")
			device_registered.emit(true, "Device registered successfully")
			authenticate_device()
	elif response_code == 409:
		print("✅ Device already registered and active! Proceeding with authentication...")
		approval_check_timer.stop()  # Stop checking if we were in pending state
		device_registered.emit(true, "Device already registered and active")
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

func _handle_status_check_response(response_code: int, data: Dictionary):
	"""Handle device status check response"""
	if response_code == 200:
		var status = data.get("status", "unknown")
		print("📋 Device status: ", status)
		
		if status == "active":
			print("✅ Device approved! Proceeding with authentication...")
			approval_check_timer.stop()
			current_state = ConnectionState.PENDING_APPROVAL  # Reset to trigger authentication
			authenticate_device()
		elif status == "pending":
			print("⏳ Still pending approval, will check again...")
			current_state = ConnectionState.PENDING_APPROVAL  # Continue checking
		else:
			print("❌ Device status: ", status)
			approval_check_timer.stop()
			_handle_connection_error("Device not approved", {"status": status})
	else:
		print("❌ Status check failed: ", response_code)
		current_state = ConnectionState.PENDING_APPROVAL  # Continue checking

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
			ConnectionState.VERIFYING_CONNECTION:
				verify_server_connection()
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
func is_device_connected() -> bool:
	"""Check if device is properly connected and authenticated"""
	return current_state == ConnectionState.CONNECTED and not device_token.is_empty()

func get_device_token() -> String:
	"""Get current device token for API requests"""
	return device_token

func get_device_headers() -> Array[String]:
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
