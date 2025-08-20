extends Node

# Global state management for Deckport Console
# This script is auto-loaded and available throughout the game

# Console Information
var console_id: String = ""
var device_uid: String = ""
var server_url: String = "https://api.deckport.ai"
var server_url_dev: String = "http://127.0.0.1:8002"

# Authentication
var device_token: String = ""
var player_token: String = ""
var is_authenticated: bool = false

# Network Status
var server_connected: bool = false
var connection_status: String = "disconnected"

# Game State
var current_scene: String = ""
var game_version: String = "1.0.0"
var update_available: bool = false

# Player Information (when logged in)
var player_id: int = 0
var player_email: String = ""
var player_display_name: String = ""
var player_elo: int = 1000

# Match Information
var current_match_id: String = ""
var in_match: bool = false
var opponent_info: Dictionary = {}

# Game State
var selected_hero: Dictionary = {}
var current_arena: Dictionary = {}
var last_match_result: Dictionary = {}
var player_level: int = 1

# Shared Manager Instances (loaded dynamically)
var _nfc_manager
var _network_client

func _ready():
	print("🎮 Deckport Console Global initialized")
	load_settings()
	generate_device_uid()
	print("📡 Global state ready")

func get_nfc_manager():
	"""Get shared NFC manager instance (lazy loaded)"""
	if not _nfc_manager:
		var nfc_script = load("res://scripts/NFCManager.gd")
		if nfc_script:
			_nfc_manager = nfc_script.new()
			add_child(_nfc_manager)
			print("📡 NFCManager initialized")
		else:
			print("❌ Failed to load NFCManager script")
	return _nfc_manager

func get_network_client():
	"""Get shared network client instance (lazy loaded)"""
	if not _network_client:
		var network_script = load("res://scripts/NetworkClient.gd")
		if network_script:
			_network_client = network_script.new()
			add_child(_network_client)
			print("📡 NetworkClient initialized")
		else:
			print("❌ Failed to load NetworkClient script")
	return _network_client

func get_api_url(endpoint: String = "") -> String:
	"""Get API URL for the given endpoint"""
	var base_url = server_url_dev if OS.is_debug_build() else server_url
	return base_url + endpoint

func is_development_mode() -> bool:
	"""Check if running in development mode"""
	return OS.is_debug_build()

func is_development() -> bool:
	"""Check if running in development mode (alias for compatibility)"""
	return is_development_mode()

func load_settings():
	"""Load console settings from file"""
	var config = ConfigFile.new()
	var err = config.load("user://console_settings.cfg")
	
	if err == OK:
		console_id = config.get_value("device", "console_id", "")
		device_uid = config.get_value("device", "device_uid", "")
		server_url = config.get_value("network", "server_url", server_url)
	else:
		print("⚠️ No settings file found, using defaults")

func save_settings():
	"""Save console settings to file"""
	var config = ConfigFile.new()
	config.set_value("device", "console_id", console_id)
	config.set_value("device", "device_uid", device_uid)
	config.set_value("network", "server_url", server_url)
	config.save("user://console_settings.cfg")

func generate_device_uid():
	"""Generate unique device identifier if not exists"""
	if device_uid == "":
		device_uid = "DECK_" + str(Time.get_unix_time_from_system()) + "_" + str(randi() % 10000)
		save_settings()
		print("🆔 Generated new device UID: ", device_uid)

func set_server_environment(use_dev: bool = false):
	"""Switch between development and production server"""
	server_url = server_url_dev if use_dev else "https://api.deckport.ai"
	save_settings()
	print("🌐 Server URL set to: ", server_url)

func log_event(event: String, data: Dictionary = {}):
	"""Log events for debugging and analytics"""
	var log_data = {
		"timestamp": Time.get_datetime_string_from_system(),
		"event": event,
		"device_uid": device_uid,
		"scene": current_scene,
		"data": data
	}
	print("📊 Event: ", log_data)
	# TODO: Send to server analytics endpoint
