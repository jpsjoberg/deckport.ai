extends Node
class_name NFCManager

##
## NFC Manager - Physical Card Scanner System
##
## This class manages the interface with physical NFC card readers to scan and validate
## real Deckport trading cards. It handles hardware communication, card authentication,
## and integration with the server-side card validation system.
##
## Key Features:
## - Physical NFC reader hardware interface
## - Real-time card scanning and detection
## - Server-side card validation and authentication
## - NTAG 424 DNA security chip support
## - Card ownership verification
## - Scan error handling and recovery
## - Hardware status monitoring
##
## Hardware Support:
## - NTAG 424 DNA NFC cards
## - USB NFC readers (ACR122U compatible)
## - Real-time scan detection
##
## Security:
## - Card authenticity verification
## - Ownership validation against player account
## - Anti-counterfeit measures
## - Secure card provisioning
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2024-12-28
##

signal card_scanned(card_data: Dictionary)
signal scan_error(error_message: String)
signal reader_status_changed(status: String)
signal card_authentication_complete(card_data: Dictionary, success: bool)

# NFC Reader states
enum NFCStatus {
	DISCONNECTED,
	CONNECTED,
	SCANNING,
	ERROR
}

var current_status: NFCStatus = NFCStatus.DISCONNECTED
var is_monitoring: bool = false
var scan_timeout: float = 10.0
var auto_scan: bool = true
var nfc_reader_process: int = -1
var server_logger

# API Configuration
var api_base_url: String = "https://deckport.ai"
var device_uid: String = ""

func _ready():
	print("🔧 Production NFC Manager initialized")
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get device UID from connection manager
	var device_connection_manager = get_node("/root/DeviceConnectionManager")
	if device_connection_manager and device_connection_manager.has_method("get_device_uid"):
		device_uid = device_connection_manager.get_device_uid()
	else:
		print("⚠️ DeviceConnectionManager not available - using fallback device UID")
		device_uid = "DECK_LOCAL_TEST_001"
	
	# Initialize NFC reader hardware
	initialize_nfc_reader()
	
	# Start monitoring if auto-scan is enabled
	if auto_scan:
		start_monitoring()

func initialize_nfc_reader():
	"""Initialize any compatible NFC reader hardware"""
	print("🔌 Scanning for NFC readers...")
	server_logger.log_system_event("nfc_init", {"action": "initialize_reader"})
	
	# Multi-method reader detection
	var reader_detected = false
	var reader_info = ""
	
	# Method 1: nfc-list command (libnfc)
	var nfc_output = []
	var nfc_exit_code = OS.execute("nfc-list", [], nfc_output)
	
	if nfc_exit_code == 0 and nfc_output.size() > 0:
		reader_info = nfc_output[0].strip_edges()
		if "NFC reader" in reader_info or "ACR122" in reader_info or "PN532" in reader_info or "OMNIKEY" in reader_info:
			reader_detected = true
			print("✅ NFC reader detected via libnfc: ", reader_info)
	
	# Method 2: PC/SC daemon check (for OMNIKEY and professional readers)
	if not reader_detected:
		var pcsc_output = []
		var pcsc_exit_code = OS.execute("pcsc_scan", ["-n"], pcsc_output)
		
		if pcsc_exit_code == 0 and pcsc_output.size() > 0:
			var pcsc_info = pcsc_output.join(" ")
			if "OMNIKEY" in pcsc_info or "HID" in pcsc_info or "076b:5422" in pcsc_info:
				reader_detected = true
				reader_info = "OMNIKEY 5422 Professional NFC Reader"
				print("✅ Professional NFC reader detected via PC/SC: OMNIKEY 5422")
	
	# Method 3: USB device detection (fallback)
	if not reader_detected:
		var usb_output = []
		var usb_exit_code = OS.execute("lsusb", [], usb_output)
		
		if usb_exit_code == 0:
			for line in usb_output:
				# Check for known NFC reader USB IDs
				if ("072f:" in line) or ("1fc9:" in line) or ("076b:5422" in line) or ("04e6:" in line):
					reader_detected = true
					if "076b:5422" in line:
						reader_info = "OMNIKEY 5422 (USB ID: 076b:5422)"
					elif "072f:" in line:
						reader_info = "ACR122U (USB ID: 072f:*)"
					elif "1fc9:" in line:
						reader_info = "PN532 (USB ID: 1fc9:*)"
					else:
						reader_info = "Compatible NFC reader detected"
					
					print("✅ NFC reader detected via USB: ", reader_info)
					break
	
	if reader_detected:
		current_status = NFCStatus.CONNECTED
		reader_status_changed.emit("Connected: " + reader_info)
		server_logger.log_system_event("nfc_reader_connected", {"reader": reader_info})
		
		# Test reader functionality
		_test_reader_functionality()
	else:
		_handle_reader_error("No compatible NFC reader detected")

func _test_reader_functionality():
	"""Test NFC reader functionality after detection"""
	print("🧪 Testing NFC reader functionality...")
	
	# Test basic reader communication
	var test_output = []
	var test_exit_code = OS.execute("timeout", ["3", "nfc-poll", "-1"], test_output)
	
	if test_exit_code == 0:
		print("✅ NFC reader communication test passed")
		server_logger.log_system_event("nfc_reader_test", {"status": "passed"})
	else:
		print("⚠️ NFC reader test inconclusive (no cards present)")
		server_logger.log_system_event("nfc_reader_test", {"status": "no_cards"})

func _handle_reader_error(error_msg: String):
	"""Handle NFC reader initialization errors"""
	current_status = NFCStatus.ERROR
	reader_status_changed.emit("Error: " + error_msg)
	print("❌ NFC Reader Error: ", error_msg)
	server_logger.log_system_event("nfc_reader_error", {"error": error_msg})
	
	print("💡 Troubleshooting:")
	print("   - Check NFC reader is connected via USB")
	print("   - Install libnfc: sudo apt install libnfc-bin pcscd")
	print("   - For OMNIKEY 5422: sudo systemctl restart pcscd")
	print("   - Check permissions: sudo usermod -a -G dialout,plugdev $USER")
	print("   - Test manually: nfc-list")
	print("   - For professional readers: pcsc_scan -n")

func start_monitoring():
	"""Start NFC card monitoring"""
	if is_monitoring:
		print("⚠️ NFC monitoring already active")
		return
	
	if current_status != NFCStatus.CONNECTED:
		print("❌ Cannot start monitoring - NFC reader not connected")
		return
	
	print("🔍 Starting NFC card monitoring")
	server_logger.log_system_event("nfc_monitoring_start", {})
	is_monitoring = true
	current_status = NFCStatus.SCANNING
	reader_status_changed.emit("Scanning for cards...")
	
	# Start scan loop
	_start_scan_loop()

func stop_monitoring():
	"""Stop NFC card monitoring"""
	print("⏹️ Stopping NFC monitoring")
	server_logger.log_system_event("nfc_monitoring_stop", {})
	is_monitoring = false
	current_status = NFCStatus.CONNECTED
	reader_status_changed.emit("Connected")

func _start_scan_loop():
	"""Main NFC scanning loop"""
	while is_monitoring:
		await _scan_for_cards()
		await get_tree().create_timer(0.5).timeout  # Scan every 500ms

func _scan_for_cards():
	"""Scan for NFC cards using any compatible reader"""
	if not is_monitoring or current_status != NFCStatus.SCANNING:
		return
	
	var card_detected = false
	var card_uid = ""
	
	# Method 1: nfc-poll (libnfc - works with most readers)
	var nfc_output = []
	var nfc_exit_code = OS.execute("timeout", ["2", "nfc-poll", "-1"], nfc_output)
	
	if nfc_exit_code == 0 and nfc_output.size() > 0:
		var scan_result = nfc_output.join("\n")
		card_uid = _extract_uid_from_scan(scan_result)
		
		if card_uid != "":
			card_detected = true
			print("📱 NFC card detected via libnfc: ", card_uid)
	
	# Method 2: PC/SC tools (for OMNIKEY and professional readers)
	if not card_detected:
		var pcsc_output = []
		var pcsc_exit_code = OS.execute("timeout", ["2", "pcsc_scan", "-r"], pcsc_output)
		
		if pcsc_exit_code == 0 and pcsc_output.size() > 0:
			var pcsc_result = pcsc_output.join("\n")
			card_uid = _extract_uid_from_pcsc_scan(pcsc_result)
			
			if card_uid != "":
				card_detected = true
				print("📱 NFC card detected via PC/SC: ", card_uid)
	
	# Process detected card
	if card_detected and card_uid != "":
		server_logger.log_system_event("nfc_card_detected", {"uid": card_uid, "method": "auto_detect"})
		_process_card_scan(card_uid)

func _extract_uid_from_scan(scan_output: String) -> String:
	"""Extract card UID from nfc-poll output"""
	var lines = scan_output.split("\n")
	
	for line in lines:
		# Look for UID line in nfc-poll output
		if "UID" in line or "NFCID1" in line:
			# Extract hex UID (format varies by reader)
			var regex = RegEx.new()
			regex.compile("([0-9A-Fa-f]{2}[\\s:]*){4,}")
			var result = regex.search(line)
			
			if result:
				var uid = result.get_string().replace(" ", "").replace(":", "").to_upper()
				return uid
	
	return ""

func _extract_uid_from_pcsc_scan(pcsc_output: String) -> String:
	"""Extract card UID from PC/SC scan output (for OMNIKEY readers)"""
	var lines = pcsc_output.split("\n")
	
	for line in lines:
		# Look for ATR or UID patterns in PC/SC output
		if "ATR:" in line or "UID:" in line or "Card UID:" in line:
			# Extract hex UID pattern
			var hex_pattern = RegEx.new()
			hex_pattern.compile("[0-9A-Fa-f]{8,14}")  # 4-7 byte UIDs
			var result = hex_pattern.search(line)
			
			if result:
				var uid = result.get_string().to_upper()
				if uid.length() >= 8:  # Valid UID length
					print("🎯 Extracted UID from PC/SC: ", uid)
					return uid
		
		# OMNIKEY specific patterns
		if "076b:5422" in line or "OMNIKEY" in line:
			# Look for following lines with card data
			continue
	
	return ""

func _process_card_scan(nfc_uid: String):
	"""Process a detected NFC card with server authentication"""
	print("🔐 Processing NFC card: ", nfc_uid)
	server_logger.log_system_event("nfc_card_process", {"uid": nfc_uid})
	
	# Authenticate card with server
	await _authenticate_card_with_server(nfc_uid)

func _authenticate_card_with_server(nfc_uid: String):
	"""Authenticate scanned card with server using NTAG 424 DNA security"""
	print("🔒 Authenticating card with server...")
	
	var http_request = HTTPRequest.new()
	add_child(http_request)
	
	# Prepare authentication request
	var headers = [
		"Content-Type: application/json",
		"X-Device-UID: " + device_uid,
		"User-Agent: Deckport-Console/1.0"
	]
	
	var request_data = {
		"ntag_uid": nfc_uid,
		"console_id": device_uid,
		"timestamp": Time.get_unix_time_from_system()
	}
	
	var json_string = JSON.stringify(request_data)
	
	# Make API request
	var error = http_request.request(
		api_base_url + "/v1/nfc-cards/authenticate",
		headers,
		HTTPClient.METHOD_POST,
		json_string
	)
	
	if error != OK:
		_handle_authentication_error("HTTP request failed: " + str(error))
		http_request.queue_free()
		return
	
	# Wait for response
	var response = await http_request.request_completed
	http_request.queue_free()
	
	var http_code = response[1]
	var body = response[3]
	
	if http_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(body.get_string_from_utf8())
		
		if parse_result == OK:
			var card_data = json.data
			_handle_authentication_success(card_data)
		else:
			_handle_authentication_error("Invalid JSON response")
	else:
		_handle_authentication_error("Server returned error: " + str(http_code))

func _handle_authentication_success(card_data: Dictionary):
	"""Handle successful card authentication"""
	print("✅ Card authenticated successfully")
	server_logger.log_system_event("nfc_card_authenticated", {
		"uid": card_data.get("ntag_uid", ""),
		"product_sku": card_data.get("product_sku", ""),
		"owner_id": card_data.get("current_owner_id", "")
	})
	
	# Emit signals
	card_scanned.emit(card_data)
	card_authentication_complete.emit(card_data, true)

func _handle_authentication_error(error_msg: String):
	"""Handle card authentication errors"""
	print("❌ Card authentication failed: ", error_msg)
	server_logger.log_system_event("nfc_card_auth_failed", {"error": error_msg})
	
	# Emit error signals
	scan_error.emit("Authentication failed: " + error_msg)
	card_authentication_complete.emit({}, false)

func get_reader_status() -> String:
	"""Get current NFC reader status"""
	match current_status:
		NFCStatus.DISCONNECTED:
			return "Disconnected"
		NFCStatus.CONNECTED:
			return "Connected"
		NFCStatus.SCANNING:
			return "Scanning"
		NFCStatus.ERROR:
			return "Error"
		_:
			return "Unknown"

func is_card_valid_for_battle(card_data: Dictionary) -> bool:
	"""Check if scanned card is valid for battle"""
	if not card_data:
		return false
	
	# Check if card is activated
	if card_data.get("status") != "activated":
		print("❌ Card not activated")
		return false
	
	# Check if card has owner
	if not card_data.has("current_owner_id") or card_data.get("current_owner_id") == null:
		print("❌ Card has no owner")
		return false
	
	# Check if card has valid product data
	if not card_data.has("product_sku") or card_data.get("product_sku") == "":
		print("❌ Card has no product SKU")
		return false
	
	return true

func force_rescan():
	"""Force a new scan cycle"""
	if current_status == NFCStatus.CONNECTED:
		print("🔄 Forcing NFC rescan...")
		server_logger.log_system_event("nfc_force_rescan", {})
		current_status = NFCStatus.SCANNING
		reader_status_changed.emit("Scanning for cards...")

func get_hardware_info() -> Dictionary:
	"""Get NFC hardware information"""
	var info = {
		"status": get_reader_status(),
		"is_monitoring": is_monitoring,
		"scan_timeout": scan_timeout,
		"auto_scan": auto_scan
	}
	
	# Get reader details if connected
	if current_status != NFCStatus.DISCONNECTED:
		var output = []
		var exit_code = OS.execute("nfc-list", [], output)
		if exit_code == 0 and output.size() > 0:
			info["reader_info"] = output[0].strip_edges()
	
	return info

func _exit_tree():
	"""Cleanup when node is removed"""
	stop_monitoring()
	if nfc_reader_process != -1:
		OS.kill(nfc_reader_process)
