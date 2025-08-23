extends Node

# Test script for device connection system
# Run this to verify the console can properly connect to the server

var device_connection_manager
var test_results = []

func _ready():
	print("🧪 Starting Device Connection Test Suite")
	print("=" * 50)
	
	# Initialize device connection manager
	device_connection_manager = preload("res://device_connection_manager.gd").new()
	add_child(device_connection_manager)
	
	# Connect to all signals for testing
	device_connection_manager.device_registered.connect(_on_device_registered)
	device_connection_manager.device_authenticated.connect(_on_device_authenticated)
	device_connection_manager.connection_tested.connect(_on_connection_tested)
	device_connection_manager.error_occurred.connect(_on_connection_error)
	
	# Start comprehensive test
	run_connection_tests()

func run_connection_tests():
	"""Run comprehensive connection tests"""
	print("🔍 Test 1: Server Connectivity")
	
	# Wait for connection process to complete
	await wait_for_connection_complete()
	
	# Test results
	print("\n📊 TEST RESULTS:")
	print("=" * 30)
	
	for result in test_results:
		var status = "✅" if result.success else "❌"
		print(status + " " + result.test_name + ": " + result.message)
	
	print("\n🏁 Test Suite Complete")
	
	# Quit after tests
	await get_tree().create_timer(2.0).timeout
	get_tree().quit()

func wait_for_connection_complete():
	"""Wait for connection process to complete or timeout"""
	var timeout = 30
	var elapsed = 0
	
	while elapsed < timeout:
		if device_connection_manager.is_connected():
			add_test_result("Device Connection", true, "Successfully connected and authenticated")
			return
		
		await get_tree().create_timer(1.0).timeout
		elapsed += 1
	
	add_test_result("Device Connection", false, "Connection timeout after " + str(timeout) + " seconds")

func add_test_result(test_name: String, success: bool, message: String):
	"""Add a test result to the results list"""
	test_results.append({
		"test_name": test_name,
		"success": success,
		"message": message
	})

# Signal handlers for detailed test results
func _on_connection_tested(success: bool, response: Dictionary):
	"""Handle connection test result"""
	add_test_result("Server Health Check", success, 
		"Server responded with: " + str(response) if success else "Server unreachable")

func _on_device_registered(success: bool, message: String):
	"""Handle device registration result"""
	add_test_result("Device Registration", success, message)

func _on_device_authenticated(success: bool, token: String):
	"""Handle device authentication result"""
	var msg = "Token received (length: " + str(token.length()) + ")" if success else "Authentication failed"
	add_test_result("Device Authentication", success, msg)
	
	if success:
		# Test authenticated API call
		test_authenticated_request()

func _on_connection_error(error_type: String, message: String, details: Dictionary):
	"""Handle connection errors"""
	add_test_result("Connection Error", false, error_type + ": " + message)

func test_authenticated_request():
	"""Test an authenticated API request"""
	print("🔐 Testing authenticated API request...")
	
	var http_test = HTTPRequest.new()
	add_child(http_test)
	http_test.request_completed.connect(_on_auth_test_response)
	
	var headers = device_connection_manager.get_authenticated_headers()
	var url = "http://127.0.0.1:8002/v1/auth/device/status?device_uid=" + device_connection_manager.device_uid
	
	http_test.request(url, headers, HTTPClient.METHOD_GET)

func _on_auth_test_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle authenticated request test response"""
	var success = result == HTTPRequest.RESULT_SUCCESS and response_code == 200
	var message = "Status endpoint returned HTTP " + str(response_code)
	
	if success:
		var response_text = body.get_string_from_utf8()
		message += " with valid device status data"
	
	add_test_result("Authenticated API Request", success, message)
