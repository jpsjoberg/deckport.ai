extends Node

# Minimal Global state for testing autoload functionality

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

# Player Information
var player_id: int = 0
var player_email: String = ""
var player_display_name: String = ""
var player_elo: int = 1000

func _ready():
	print("🎮 Minimal Global initialized")
	device_uid = _generate_device_uid()
	print("Device UID: ", device_uid)

func _generate_device_uid() -> String:
	"""Generate unique device identifier"""
	var timestamp = str(Time.get_unix_time_from_system())
	var random = str(randi() % 10000)
	return "DECK_" + timestamp + "_" + random

func get_api_url(endpoint: String = "") -> String:
	"""Get API URL for the given endpoint"""
	var base_url = server_url_dev if OS.is_debug_build() else server_url
	return base_url + endpoint

func is_development() -> bool:
	"""Check if running in development mode"""
	return OS.is_debug_build()

func is_development_mode() -> bool:
	"""Check if running in development mode (alias)"""
	return is_development()

func log_event(event: String, data: Dictionary = {}):
	"""Simple event logging"""
	print("📊 Event: ", event, " Data: ", data)
