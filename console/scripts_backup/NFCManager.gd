extends Node
class_name NFCManager

# NFC Card Scanner Manager
# Handles physical NFC card scanning and validation

signal card_scanned(card_data: Dictionary)
signal scan_error(error_message: String)
signal reader_status_changed(status: String)

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

# Mock NFC data for development (replace with real NFC integration)
var mock_cards = {
	"04:52:3A:B2:C1:80:00": {
		"id": "nfc_card_1",
		"product_sku": "RADIANT-001",
		"name": "Solar Vanguard",
		"category": "CREATURE",
		"rarity": "EPIC",
		"colors": ["RADIANT"],
		"status": "activated",
		"owner_id": Global.player_id,
		"base_stats": {
			"attack": 3,
			"defense": 2,
			"health": 5,
			"energy_per_turn": 2
		}
	},
	"04:A3:7F:C2:D1:90:01": {
		"id": "nfc_card_2", 
		"product_sku": "AZURE-014",
		"name": "Tidecaller Sigil",
		"category": "ENCHANTMENT",
		"rarity": "RARE",
		"colors": ["AZURE"],
		"status": "activated",
		"owner_id": Global.player_id,
		"base_stats": {
			"duration": 3,
			"energy_cost": 1
		}
	},
	"04:B1:8E:D3:F2:A1:02": {
		"id": "nfc_card_3",
		"product_sku": "VERDANT-007", 
		"name": "Forest Guardian",
		"category": "CREATURE",
		"rarity": "COMMON",
		"colors": ["VERDANT"],
		"status": "unactivated",  # Needs activation
		"owner_id": null,
		"base_stats": {
			"attack": 2,
			"defense": 3,
			"health": 4,
			"energy_per_turn": 1
		}
	}
}

func _ready():
	Logger.log_info("NFCManager", "NFC Manager initialized")
	
	# Initialize NFC reader
	initialize_nfc_reader()
	
	# Start monitoring if auto-scan is enabled
	if Settings.nfc_auto_scan:
		start_monitoring()

func initialize_nfc_reader():
	"""Initialize NFC reader hardware"""
	Logger.log_info("NFCManager", "Initializing NFC reader")
	
	# TODO: Initialize actual NFC reader hardware
	# For development, simulate connection
	if OS.is_debug_build():
		current_status = NFCStatus.CONNECTED
		reader_status_changed.emit("Connected (Mock)")
		Logger.log_info("NFCManager", "Mock NFC reader connected")
	else:
		# TODO: Real NFC reader initialization
		# Check for USB NFC reader, initialize driver
		current_status = NFCStatus.DISCONNECTED
		reader_status_changed.emit("Searching for NFC reader...")

func start_monitoring():
	"""Start NFC card monitoring"""
	if is_monitoring:
		Logger.log_warning("NFCManager", "NFC monitoring already active")
		return
	
	Logger.log_info("NFCManager", "Starting NFC monitoring")
	is_monitoring = true
	current_status = NFCStatus.SCANNING
	reader_status_changed.emit("Scanning for cards...")
	
	# Start scan loop
	_start_scan_loop()

func stop_monitoring():
	"""Stop NFC card monitoring"""
	Logger.log_info("NFCManager", "Stopping NFC monitoring")
	is_monitoring = false
	current_status = NFCStatus.CONNECTED
	reader_status_changed.emit("Connected")

func _start_scan_loop():
	"""Main NFC scanning loop"""
	while is_monitoring:
		await _scan_for_cards()
		await get_tree().create_timer(0.5).timeout  # Scan every 500ms

func _scan_for_cards():
	"""Scan for NFC cards"""
	if not is_monitoring:
		return
	
	# TODO: Implement actual NFC scanning
	# For development, simulate with keyboard input
	if OS.is_debug_build():
		_simulate_nfc_scan()
	else:
		_real_nfc_scan()

func _simulate_nfc_scan():
	"""Simulate NFC scanning for development"""
	# Check for keyboard input to simulate card scans
	if Input.is_action_just_pressed("nfc_scan_1"):
		_process_card_scan("04:52:3A:B2:C1:80:00")
	elif Input.is_action_just_pressed("nfc_scan_2"):
		_process_card_scan("04:A3:7F:C2:D1:90:01")
	elif Input.is_action_just_pressed("nfc_scan_3"):
		_process_card_scan("04:B1:8E:D3:F2:A1:02")

func _real_nfc_scan():
	"""Perform actual NFC hardware scanning"""
	# TODO: Implement real NFC scanning
	# This would interface with USB NFC reader
	# Example pseudocode:
	# var uid = nfc_reader.scan()
	# if uid:
	#     _process_card_scan(uid)
	pass

func _process_card_scan(nfc_uid: String):
	"""Process a detected NFC card"""
	Logger.log_info("NFCManager", "Processing NFC scan", {"uid": nfc_uid})
	
	# Look up card data (mock or from server)
	var card_data = mock_cards.get(nfc_uid)
	
	if card_data:
		# Validate card with server
		await _validate_card_with_server(nfc_uid, card_data)
	else:
		# Unknown card - try server lookup
		await _lookup_unknown_card(nfc_uid)

func _validate_card_with_server(nfc_uid: String, card_data: Dictionary):
	"""Validate scanned card with server"""
	Logger.log_info("NFCManager", "Validating card with server")
	
	# TODO: Call server NFC verification endpoint
	# For now, simulate validation
	await get_tree().create_timer(0.2).timeout  # Simulate network delay
	
	# Emit card scanned signal
	card_scanned.emit(card_data)
	Logger.log_info("NFCManager", "Card validated", {"uid": nfc_uid, "success": true})

func _lookup_unknown_card(nfc_uid: String):
	"""Look up unknown card on server"""
	Logger.log_info("NFCManager", "Looking up unknown card", {"uid": nfc_uid})
	
	# TODO: Call server to identify card
	# For now, emit error
	scan_error.emit("Unknown card: " + nfc_uid)
	Logger.log_info("NFCManager", "Card lookup failed", {"uid": nfc_uid, "success": false})

func force_scan_card(product_sku: String):
	"""Force scan a specific card (for testing)"""
	Logger.log_info("NFCManager", "Force scanning card: " + product_sku)
	
	# Find card by product SKU in mock data
	for uid in mock_cards:
		var card = mock_cards[uid]
		if card.product_sku == product_sku:
			_process_card_scan(uid)
			return
	
	scan_error.emit("Card not found: " + product_sku)

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

func is_card_valid_for_action(card_data: Dictionary, required_category: String = "") -> bool:
	"""Check if scanned card is valid for current action"""
	if not card_data:
		return false
	
	# Check if card is activated
	if card_data.get("status") != "activated":
		return false
	
	# Check if player owns the card
	if card_data.get("owner_id") != Global.player_id:
		return false
	
	# Check category if specified
	if required_category != "" and card_data.get("category") != required_category:
		return false
	
	return true

# Development input map (add to project input map)
# nfc_scan_1 = F1 key
# nfc_scan_2 = F2 key  
# nfc_scan_3 = F3 key
