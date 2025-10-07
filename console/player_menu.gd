extends Control

# Player Menu - After successful login

@onready var title_label = $CenterContainer/VBoxContainer/TitleLabel
@onready var player_info = $CenterContainer/VBoxContainer/PlayerInfo
@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var background_video = $BackgroundVideo

# Touch control buttons (if they exist in scene)
@onready var portal_button = $CenterContainer/VBoxContainer/MainMenuButtons/PortalButton
@onready var keys_button = $CenterContainer/VBoxContainer/MainMenuButtons/KeysButton
@onready var stats_button = $CenterContainer/VBoxContainer/MainMenuButtons/StatsButton
@onready var travel_button = $CenterContainer/VBoxContainer/MainMenuButtons/TravelButton
@onready var scan_card1_button = $CenterContainer/VBoxContainer/CardScanButtons/ScanCard1
@onready var scan_card2_button = $CenterContainer/VBoxContainer/CardScanButtons/ScanCard2
@onready var scan_card3_button = $CenterContainer/VBoxContainer/CardScanButtons/ScanCard3

var server_logger
var device_id = "DECK_DEV_CONSOLE_01"  # Fixed device ID for development

# Player data (passed from QR login)
var player_name = "Player"
var player_id = 0
var player_elo = 1000

func _ready():
	print("🎮 Player Menu loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_scene_change("qr_login", "player_menu")
	
	setup_background()
	setup_menu()
	setup_touch_controls()

func setup_background():
	"""Setup background video for player dashboard"""
	# Priority order for player dashboard background videos
	var portal_dashboard_paths = [
		"res://assets/videos/player_dashboard/portal_dashboard_background.ogv",
		"res://assets/videos/player_dashboard/portal_dashboard_background.mp4"
	]
	var player_menu_paths = [
		"res://assets/videos/player_dashboard/player_menu_background.ogv",
		"res://assets/videos/player_dashboard/player_menu_background.mp4"
	]
	var ui_fallback_paths = [
		"res://assets/videos/ui/dashboard_background.ogv",
		"res://assets/videos/ui/dashboard_background.mp4"
	]
	
	var video_loaded = false
	
	# Try portal dashboard video paths first
	for video_path in portal_dashboard_paths:
		if ResourceLoader.exists(video_path):
			print("📁 Found portal dashboard video: ", video_path)
			background_video.stream = load(video_path)
			if background_video.stream != null:
				background_video.loop = true
				background_video.volume_db = -80.0  # Mute audio
				background_video.visible = true
				background_video.play()
				server_logger.log_system_event("portal_dashboard_video_loaded", {"path": video_path})
				print("🌀 Portal dashboard background video loaded and playing")
				video_loaded = true
				break
			else:
				print("❌ Failed to load portal dashboard video: ", video_path)
	
	# Try general player menu videos if portal video not loaded
	if not video_loaded:
		for video_path in player_menu_paths:
			if ResourceLoader.exists(video_path):
				print("📁 Found player menu video: ", video_path)
				background_video.stream = load(video_path)
				if background_video.stream != null:
					background_video.loop = true
					background_video.volume_db = -80.0  # Mute audio
					background_video.visible = true
					background_video.play()
					server_logger.log_system_event("player_menu_video_loaded", {"path": video_path})
					print("🎯 Player menu background video loaded and playing")
					video_loaded = true
					break
				else:
					print("❌ Failed to load player menu video: ", video_path)
	
	# Try UI fallback videos if still not loaded
	if not video_loaded:
		for video_path in ui_fallback_paths:
			if ResourceLoader.exists(video_path):
				print("📁 Found UI fallback video: ", video_path)
				background_video.stream = load(video_path)
				if background_video.stream != null:
					background_video.loop = true
					background_video.volume_db = -80.0  # Mute audio
					background_video.visible = true
					background_video.play()
					server_logger.log_system_event("dashboard_ui_video_loaded", {"path": video_path})
					print("🎬 Dashboard UI fallback video loaded and playing")
					video_loaded = true
					break
				else:
					print("❌ Failed to load UI fallback video: ", video_path)
	
	if not video_loaded:
		# Show background ColorRect and create portal-themed animated background
		$Background.visible = true
		create_portal_animation()
	else:
		# Hide background ColorRect so video is visible
		$Background.visible = false

func create_portal_animation():
	"""Create animated background fallback for player dashboard"""
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property($Background, "color", Color(0.1, 0.2, 0.3, 1), 3.0)
	tween.tween_property($Background, "color", Color(0.3, 0.1, 0.4, 1), 3.0)
	tween.tween_property($Background, "color", Color(0.2, 0.3, 0.1, 1), 3.0)
	server_logger.log_system_event("portal_animation_fallback", {"type": "portal_cycle"})
	print("🌀 Portal dashboard background animation started")

func setup_menu():
	"""Setup player dashboard"""
	title_label.text = "WELCOME TO THE PORTAL"
	player_info.text = "Level: 1 | ELO: " + str(player_elo) + " | ID: " + str(player_id)
	status_label.text = "1 - Open Portal (Hero Selection & Battle)\n2 - Portal Keys (Card Collection)\n3 - Statistics (Player Analytics)\n4 - Travel (Through Dimensions)"

func _input(event):
	"""Handle input"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_1:
			open_portal()
		elif event.keycode == KEY_2:
			portal_keys()
		elif event.keycode == KEY_3:
			show_statistics()
		elif event.keycode == KEY_4:
			travel_dimensions()

func simulate_card_scan(card_sku: String, card_name: String):
	"""Simulate NFC card scanning"""
	print("🃏 Card scanned: " + card_name)
	server_logger.log_nfc_scan(card_sku, true, {
		"card_name": card_name,
		"scan_method": "keyboard_simulation"
	})
	
	# Show card preview
	status_label.text = "🃏 CARD SCANNED\n\n" + card_name + "\n(" + card_sku + ")\n\nPress 1/2 for menu or Q/W/E for more cards"
	
	# Play scan feedback
	await get_tree().create_timer(0.5).timeout

func open_portal():
	"""Open Portal - Hero Selection & Battle"""
	print("🌀 Opening Portal...")
	server_logger.log_user_action("open_portal", {})
	status_label.text = "🌀 PORTAL OPENING\n\nChoose your champion..."
	
	# Initialize game state manager with player data
	var game_state_manager = get_node("/root/GameStateManager")
	if not game_state_manager:
		print("⚠️ GameStateManager not found - creating fallback")
		game_state_manager = preload("res://game_state_manager.gd").new()
		add_child(game_state_manager)
	if game_state_manager:
		game_state_manager.set_player_data(player_id, player_name, player_elo)
		game_state_manager.change_state(game_state_manager.GameState.HERO_SELECTION)
	else:
		# Fallback - check if hero selection scene exists
		await get_tree().create_timer(1.5).timeout
		print("🦸 Checking for hero selection scene...")
		
		if ResourceLoader.exists("res://hero_selection_scene.tscn"):
			print("📁 Hero selection scene found - loading...")
			server_logger.log_scene_change("player_menu", "hero_selection")
			get_tree().change_scene_to_file("res://hero_selection_scene.tscn")
		else:
			print("⚠️ Hero selection scene not found - staying in player menu")
			status_label.text = "🦸 HERO SELECTION\n\nHero selection coming soon!\nPress 2 for Portal Keys or 3 for Stats"

func portal_keys():
	"""Portal Keys - Card Collection & Stats"""
	print("🗝️ Accessing Portal Keys...")
	server_logger.log_user_action("portal_keys", {})
	status_label.text = "🗝️ PORTAL KEYS\n\nCard collection and stats\nComing soon!"
	# TODO: Transition to card collection scene

func show_statistics():
	"""Statistics - Player Analytics"""
	print("📊 Showing Statistics...")
	server_logger.log_user_action("show_statistics", {})
	status_label.text = "📊 STATISTICS\n\nPlayer analytics dashboard\nComing soon!"
	# TODO: Transition to statistics scene

func travel_dimensions():
	"""Travel Through Dimensions - Dynamic Story Mode"""
	print("🌌 Traveling Through Dimensions...")
	server_logger.log_user_action("travel_dimensions", {})
	status_label.text = "🌌 DIMENSIONAL TRAVEL\n\nDynamic story mode with LLM\nComing soon!"
	# TODO: Transition to dynamic story scene

func setup_touch_controls():
	"""Setup touch controls for console interface"""
	# Connect main menu buttons (if they exist)
	if has_node("CenterContainer/VBoxContainer/MainMenuButtons/PortalButton"):
		var portal_btn = get_node("CenterContainer/VBoxContainer/MainMenuButtons/PortalButton")
		portal_btn.pressed.connect(open_portal)
	
	if has_node("CenterContainer/VBoxContainer/MainMenuButtons/KeysButton"):
		var keys_btn = get_node("CenterContainer/VBoxContainer/MainMenuButtons/KeysButton")
		keys_btn.pressed.connect(portal_keys)
	
	if has_node("CenterContainer/VBoxContainer/MainMenuButtons/StatsButton"):
		var stats_btn = get_node("CenterContainer/VBoxContainer/MainMenuButtons/StatsButton")
		stats_btn.pressed.connect(show_statistics)
	
	if has_node("CenterContainer/VBoxContainer/MainMenuButtons/TravelButton"):
		var travel_btn = get_node("CenterContainer/VBoxContainer/MainMenuButtons/TravelButton")
		travel_btn.pressed.connect(travel_dimensions)
	
	# Connect card scanning buttons (if they exist)
	if has_node("CenterContainer/VBoxContainer/CardScanButtons/ScanCard1"):
		var scan1_btn = get_node("CenterContainer/VBoxContainer/CardScanButtons/ScanCard1")
		scan1_btn.pressed.connect(func(): simulate_card_scan("RADIANT-001", "Solar Vanguard"))
	
	if has_node("CenterContainer/VBoxContainer/CardScanButtons/ScanCard2"):
		var scan2_btn = get_node("CenterContainer/VBoxContainer/CardScanButtons/ScanCard2")
		scan2_btn.pressed.connect(func(): simulate_card_scan("AZURE-014", "Tidecaller Sigil"))
	
	if has_node("CenterContainer/VBoxContainer/CardScanButtons/ScanCard3"):
		var scan3_btn = get_node("CenterContainer/VBoxContainer/CardScanButtons/ScanCard3")
		scan3_btn.pressed.connect(func(): simulate_card_scan("VERDANT-007", "Nature's Blessing"))
	
	print("✅ Touch controls configured for player menu")
