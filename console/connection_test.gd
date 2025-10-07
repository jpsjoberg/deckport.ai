extends Node

##
## Console Connection Test Script
##
## This script verifies all network connections required for real-time gameplay
## and API data updates. Run this to ensure the console is properly configured.
##
## Tests:
## - HTTP API connectivity (Port 8002)
## - WebSocket real-time connectivity (Port 8003)
## - All required API endpoints
## - WebSocket message protocol
## - Authentication flow
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2024-12-28
##

signal test_completed(results: Dictionary)

var http_client: HTTPRequest
var websocket: WebSocketPeer
var test_results: Dictionary = {}

func _ready():
	print("🧪 Starting Console Connection Tests...")
	
	# Initialize HTTP client
	http_client = HTTPRequest.new()
	add_child(http_client)
	http_client.request_completed.connect(_on_http_response)
	
	# Initialize WebSocket
	websocket = WebSocketPeer.new()
	
	# Start tests
	run_connection_tests()

func run_connection_tests():
	"""Run comprehensive connection tests"""
	test_results = {
		"api_health": false,
		"api_console_logs": false,
		"api_gameplay_queue": false,
		"api_nfc_auth": false,
		"websocket_connection": false,
		"websocket_messages": false,
		"overall_status": "TESTING"
	}
	
	print("📡 Testing API Connections...")
	test_api_endpoints()

func test_api_endpoints():
	"""Test all required API endpoints"""
	
	# Test 1: Health Check
	print("  🔍 Testing API Health...")
	var error = http_client.request("https://deckport.ai/health")
	if error != OK:
		print("  ❌ Health check failed")
		test_results["api_health"] = false
	
	# Wait for response before continuing
	await http_client.request_completed
	
	# Test 2: Console Logs
	print("  📊 Testing Console Logs...")
	var headers = ["Content-Type: application/json"]
	var data = JSON.stringify({
		"device_id": "console_test",
		"logs": [{"level": "INFO", "message": "Connection test"}]
	})
	
	error = http_client.request(
		"https://deckport.ai/v1/console/logs",
		headers,
		HTTPClient.METHOD_POST,
		data
	)
	
	await http_client.request_completed
	
	# Test 3: Gameplay Queue
	print("  🎮 Testing Gameplay Queue...")
	error = http_client.request("https://deckport.ai/v1/gameplay/queue/status?player_id=1&mode=1v1")
	
	await http_client.request_completed
	
	# Test 4: NFC Authentication
	print("  🔧 Testing NFC Authentication...")
	var nfc_data = JSON.stringify({"test": "connection"})
	error = http_client.request(
		"https://deckport.ai/v1/nfc-cards/authenticate",
		headers,
		HTTPClient.METHOD_POST,
		nfc_data
	)
	
	await http_client.request_completed
	
	# Test WebSocket
	test_websocket_connection()

func test_websocket_connection():
	"""Test WebSocket real-time connection"""
	print("🌐 Testing WebSocket Connection...")
	
	var headers = []
	var error = websocket.connect_to_url("ws://127.0.0.1:8003/ws", headers)
	
	if error != OK:
		print("  ❌ WebSocket connection failed")
		test_results["websocket_connection"] = false
		complete_tests()
		return
	
	# Wait for connection
	var timer = Timer.new()
	add_child(timer)
	timer.wait_time = 2.0
	timer.one_shot = true
	timer.start()
	await timer.timeout
	timer.queue_free()
	
	# Check connection state
	var state = websocket.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		print("  ✅ WebSocket connected successfully")
		test_results["websocket_connection"] = true
		test_websocket_messages()
	else:
		print("  ❌ WebSocket failed to connect (state: ", state, ")")
		test_results["websocket_connection"] = false
		complete_tests()

func test_websocket_messages():
	"""Test WebSocket message protocol"""
	print("  📨 Testing WebSocket Messages...")
	
	# Send ping message
	var ping_message = {
		"type": "ping",
		"timestamp": Time.get_unix_time_from_system()
	}
	
	var json_string = JSON.stringify(ping_message)
	var error = websocket.send_text(json_string)
	
	if error != OK:
		print("  ❌ Failed to send WebSocket message")
		test_results["websocket_messages"] = false
	else:
		print("  ✅ WebSocket message sent successfully")
		test_results["websocket_messages"] = true
	
	# Close WebSocket
	websocket.close()
	
	complete_tests()

func complete_tests():
	"""Complete all tests and show results"""
	print("\n🎯 Connection Test Results:")
	print("========================================")  # Fixed string multiplication
	
	var all_passed = true
	
	for test_name in test_results:
		if test_name == "overall_status":
			continue
			
		var status = "✅ PASS" if test_results[test_name] else "❌ FAIL"
		print("  ", test_name, ": ", status)
		
		if not test_results[test_name]:
			all_passed = false
	
	test_results["overall_status"] = "PASS" if all_passed else "FAIL"
	
	print("========================================")  # Fixed string multiplication
	if all_passed:
		print("🎉 ALL TESTS PASSED - Console ready for real-time gameplay!")
	else:
		print("⚠️  SOME TESTS FAILED - Check network configuration")
	
	test_completed.emit(test_results)

func _on_http_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP response"""
	var response_text = body.get_string_from_utf8()
	
	if response_code == 200:
		print("  ✅ HTTP request successful")
		
		# Parse response to check specific endpoints
		if "status" in response_text and "ok" in response_text:
			test_results["api_health"] = true
		elif "logs_received" in response_text:
			test_results["api_console_logs"] = true
		elif "in_queue" in response_text:
			test_results["api_gameplay_queue"] = true
	else:
		# NFC auth endpoint returns 400 with auth error, which is expected
		if response_code == 400 and "authentication required" in response_text.to_lower():
			test_results["api_nfc_auth"] = true
			print("  ✅ NFC endpoint responding (auth required as expected)")
		else:
			print("  ❌ HTTP request failed: ", response_code, " - ", response_text)
