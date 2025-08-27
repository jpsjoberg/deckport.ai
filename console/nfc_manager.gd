extends Node
class_name NFCManager

# Production NFC Card Scanner Manager
# Handles physical NFC card scanning and validation with real hardware

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
var api_base_url: String = "http://127.0.0.1:8002"
var device_uid: String = ""

func _ready():
	print("🔧 Production NFC Manager initialized")
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get device UID from connection manager
	var device_connection_manager = get_node("/root/DeviceConnectionManager")
	if device_connection_manager:
		device_uid = device_connection_manager.get_device_uid()
	
	# Initialize NFC reader hardware
	initialize_nfc_reader()
	
	# Start monitoring if auto-scan is enabled
	if auto_scan:
		start_monitoring()

func initialize_nfc_reader():
	"""Initialize real NFC reader hardware"""
	print("🔌 Initializing NFC reader hardware...")
	server_logger.log_system_event("nfc_init", {"action": "initialize_reader"})
	
	# Check for NFC reader using nfc-list command
	var output = []
	var exit_code = OS.execute("nfc-list", [], output)
	
	if exit_code == 0 and output.size() > 0:
		var reader_info = output[0]
		if "NFC reader" in reader_info or "ACR122U" in reader_info or "PN532" in reader_info:
			current_status = NFCStatus.CONNECTED
			reader_status_changed.emit("Connected: " + reader_info.strip_edges())
			print("✅ NFC reader detected: ", reader_info.strip_edges())
			server_logger.log_system_event("nfc_reader_connected", {"reader": reader_info.strip_edges()})
		else:
			_handle_reader_error("NFC reader found but not recognized")
	else:
		_handle_reader_error("No NFC reader detected")

func _handle_reader_error(error_msg: String):
	"""Handle NFC reader initialization errors"""
	current_status = NFCStatus.ERROR
	reader_status_changed.emit("Error: " + error_msg)
	print("❌ NFC Reader Error: ", error_msg)
	server_logger.log_system_event("nfc_reader_error", {"error": error_msg})
	
	print("💡 Troubleshooting:")
	print("   - Check NFC reader is connected via USB")
	print("   - Install libnfc: sudo apt install libnfc-bin")
	print("   - Check permissions: sudo usermod -a -G dialout $USER")
	print("   - Restart after driver installation")

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
	"""Scan for NFC cards using real hardware"""
	if not is_monitoring or current_status != NFCStatus.SCANNING:
		return
	
	# Use nfc-poll to detect cards
	var output = []
	var exit_code = OS.execute("timeout", ["2", "nfc-poll", "-1"], output)
	
	if exit_code == 0 and output.size() > 0:
		var scan_result = output.join("\n")
		var uid = _extract_uid_from_scan(scan_result)
		
		if uid != "":
			print("📱 NFC card detected: ", uid)
			server_logger.log_system_event("nfc_card_detected", {"uid": uid})
			_process_card_scan(uid)

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
		api_base_url + "/v1/nfc/console/authenticate",
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
