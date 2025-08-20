extends Node

# Console Settings Management
# Handles all console configuration and preferences

# Display Settings
var fullscreen: bool = true
var resolution: Vector2i = Vector2i(1920, 1080)
var vsync_enabled: bool = true

# Audio Settings  
var master_volume: float = 1.0
var sfx_volume: float = 0.8
var music_volume: float = 0.6
var voice_volume: float = 1.0

# Network Settings
var auto_connect: bool = true
var connection_timeout: int = 30
var retry_attempts: int = 3

# Game Settings
var auto_update: bool = true
var debug_mode: bool = false
var show_fps: bool = false
var card_animation_speed: float = 1.0

# NFC Settings
var nfc_enabled: bool = true
var nfc_scan_timeout: int = 10
var nfc_auto_scan: bool = true

# Kiosk Settings
var kiosk_mode: bool = true
var idle_timeout: int = 300  # 5 minutes
var screensaver_enabled: bool = true

func _ready():
	print("⚙️ Console Settings initialized")
	load_settings()
	apply_settings()

func load_settings():
	"""Load settings from configuration file"""
	var config = ConfigFile.new()
	var err = config.load("user://settings.cfg")
	
	if err != OK:
		print("⚙️ Creating default settings file")
		save_settings()
		return
	
	# Display
	fullscreen = config.get_value("display", "fullscreen", fullscreen)
	resolution = config.get_value("display", "resolution", resolution)
	vsync_enabled = config.get_value("display", "vsync_enabled", vsync_enabled)
	
	# Audio
	master_volume = config.get_value("audio", "master_volume", master_volume)
	sfx_volume = config.get_value("audio", "sfx_volume", sfx_volume)
	music_volume = config.get_value("audio", "music_volume", music_volume)
	voice_volume = config.get_value("audio", "voice_volume", voice_volume)
	
	# Network
	auto_connect = config.get_value("network", "auto_connect", auto_connect)
	connection_timeout = config.get_value("network", "connection_timeout", connection_timeout)
	retry_attempts = config.get_value("network", "retry_attempts", retry_attempts)
	
	# Game
	auto_update = config.get_value("game", "auto_update", auto_update)
	debug_mode = config.get_value("game", "debug_mode", debug_mode)
	show_fps = config.get_value("game", "show_fps", show_fps)
	card_animation_speed = config.get_value("game", "card_animation_speed", card_animation_speed)
	
	# NFC
	nfc_enabled = config.get_value("nfc", "enabled", nfc_enabled)
	nfc_scan_timeout = config.get_value("nfc", "scan_timeout", nfc_scan_timeout)
	nfc_auto_scan = config.get_value("nfc", "auto_scan", nfc_auto_scan)
	
	# Kiosk
	kiosk_mode = config.get_value("kiosk", "mode", kiosk_mode)
	idle_timeout = config.get_value("kiosk", "idle_timeout", idle_timeout)
	screensaver_enabled = config.get_value("kiosk", "screensaver_enabled", screensaver_enabled)

func save_settings():
	"""Save settings to configuration file"""
	var config = ConfigFile.new()
	
	# Display
	config.set_value("display", "fullscreen", fullscreen)
	config.set_value("display", "resolution", resolution)
	config.set_value("display", "vsync_enabled", vsync_enabled)
	
	# Audio
	config.set_value("audio", "master_volume", master_volume)
	config.set_value("audio", "sfx_volume", sfx_volume)
	config.set_value("audio", "music_volume", music_volume)
	config.set_value("audio", "voice_volume", voice_volume)
	
	# Network
	config.set_value("network", "auto_connect", auto_connect)
	config.set_value("network", "connection_timeout", connection_timeout)
	config.set_value("network", "retry_attempts", retry_attempts)
	
	# Game
	config.set_value("game", "auto_update", auto_update)
	config.set_value("game", "debug_mode", debug_mode)
	config.set_value("game", "show_fps", show_fps)
	config.set_value("game", "card_animation_speed", card_animation_speed)
	
	# NFC
	config.set_value("nfc", "enabled", nfc_enabled)
	config.set_value("nfc", "scan_timeout", nfc_scan_timeout)
	config.set_value("nfc", "auto_scan", nfc_auto_scan)
	
	# Kiosk
	config.set_value("kiosk", "mode", kiosk_mode)
	config.set_value("kiosk", "idle_timeout", idle_timeout)
	config.set_value("kiosk", "screensaver_enabled", screensaver_enabled)
	
	config.save("user://settings.cfg")

func apply_settings():
	"""Apply settings to the game engine"""
	# Display
	if fullscreen:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(resolution)
	
	# VSync
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync_enabled else DisplayServer.VSYNC_DISABLED)
	
	# Audio
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Master"), linear_to_db(master_volume))
	
	print("⚙️ Settings applied successfully")

func reset_to_defaults():
	"""Reset all settings to default values"""
	fullscreen = true
	resolution = Vector2i(1920, 1080)
	vsync_enabled = true
	master_volume = 1.0
	sfx_volume = 0.8
	music_volume = 0.6
	voice_volume = 1.0
	auto_connect = true
	connection_timeout = 30
	retry_attempts = 3
	auto_update = true
	debug_mode = false
	show_fps = false
	card_animation_speed = 1.0
	nfc_enabled = true
	nfc_scan_timeout = 10
	nfc_auto_scan = true
	kiosk_mode = true
	idle_timeout = 300
	screensaver_enabled = true
	
	save_settings()
	apply_settings()
	print("⚙️ Settings reset to defaults")
