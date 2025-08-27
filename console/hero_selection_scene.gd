extends Control

# Hero Selection Scene - Choose starting hero for battle
# Players scan their hero card to select their champion

@onready var title_label = $VBoxContainer/TitleLabel
@onready var status_label = $VBoxContainer/StatusLabel
@onready var hero_info_label = $VBoxContainer/HeroInfoLabel
@onready var scan_prompt_label = $VBoxContainer/ScanPromptLabel
@onready var background_video = $BackgroundVideo

var game_state_manager
var server_logger
var selected_hero: Dictionary = {}
var scan_timeout_timer: Timer

func _ready():
	print("🦸 Hero Selection Scene loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get game state manager
	game_state_manager = get_node("/root/GameStateManager")
	
	# Setup UI
	setup_hero_selection_ui()
	
	# Setup background
	setup_background()
	
	# Setup scan timeout
	setup_scan_timeout()

func setup_hero_selection_ui():
	"""Setup the hero selection interface"""
	title_label.text = "CHOOSE YOUR CHAMPION"
	status_label.text = "Select your hero to enter the arena"
	hero_info_label.text = ""
	scan_prompt_label.text = "🃏 SCAN YOUR HERO CARD\n\nPlace your hero card on the NFC reader\nto select your champion for battle"
	
	print("🦸 Hero selection UI configured")

func setup_background():
	"""Setup background video for hero selection"""
	var hero_background_paths = [
		"res://assets/videos/hero_selection/hero_portal_background.ogv",
		"res://assets/videos/hero_selection/hero_portal_background.mp4",
		"res://assets/videos/hero_selection/hero_selection_background.ogv",
		"res://assets/videos/hero_selection/hero_selection_background.mp4",
		"res://assets/videos/ui/hero_background.ogv",
		"res://assets/videos/ui/hero_background.mp4"
	]
	
	var video_loaded = false
	
	for video_path in hero_background_paths:
		if ResourceLoader.exists(video_path):
			print("📁 Found hero selection video: ", video_path)
			background_video.stream = load(video_path)
			if background_video.stream != null:
				background_video.loop = true
				background_video.volume_db = -80.0  # Mute audio
				background_video.visible = true
				background_video.play()
				
				server_logger.log_system_event("hero_background_loaded", {
					"path": video_path
				})
				
				print("🌟 Hero selection video loaded")
				video_loaded = true
				break
	
	if not video_loaded:
		# Create animated background fallback
		$Background.visible = true
		create_hero_animation()
	else:
		$Background.visible = false

func create_hero_animation():
	"""Create animated background fallback for hero selection"""
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property($Background, "color", Color(0.2, 0.1, 0.3, 1), 3.0)
	tween.tween_property($Background, "color", Color(0.3, 0.2, 0.1, 1), 3.0)
	tween.tween_property($Background, "color", Color(0.1, 0.3, 0.2, 1), 3.0)
	
	server_logger.log_system_event("hero_animation_fallback", {"type": "hero_cycle"})
	print("🎨 Hero selection background animation started")

func setup_scan_timeout():
	"""Setup timeout for hero selection"""
	scan_timeout_timer = Timer.new()
	add_child(scan_timeout_timer)
	scan_timeout_timer.wait_time = 60.0  # 60 seconds to select hero
	scan_timeout_timer.timeout.connect(_on_scan_timeout)
	scan_timeout_timer.start()
	
	print("⏰ Hero selection timeout set to 60 seconds")

func _input(event):
	"""Handle input events"""
	if event is InputEventKey and event.pressed:
		# Simulate card scanning for testing
		if event.keycode == KEY_H:
			simulate_hero_scan("HERO_WARRIOR_001", "Valiant Warrior")
		elif event.keycode == KEY_M:
			simulate_hero_scan("HERO_MAGE_001", "Arcane Mage")
		elif event.keycode == KEY_R:
			simulate_hero_scan("HERO_ROGUE_001", "Shadow Rogue")
		elif event.keycode == KEY_ESCAPE:
			cancel_hero_selection()

func simulate_hero_scan(hero_sku: String, hero_name: String):
	"""Simulate NFC hero card scanning for testing"""
	print("🦸 Hero card scanned: ", hero_name)
	
	var hero_data = {
		"sku": hero_sku,
		"name": hero_name,
		"type": "hero",
		"mana_cost": 0,
		"attack": 1,
		"health": 20,
		"abilities": ["Leadership", "Battle Cry"],
		"rarity": "common",
		"description": "A brave champion ready for battle"
	}
	
	select_hero(hero_data)

func select_hero(hero_data: Dictionary):
	"""Select a hero card"""
	selected_hero = hero_data
	
	print("✅ Hero selected: ", hero_data.get("name", "Unknown"))
	
	# Update UI
	hero_info_label.text = "SELECTED HERO\n\n" + hero_data.get("name", "Unknown") + "\nAttack: " + str(hero_data.get("attack", 1)) + " | Health: " + str(hero_data.get("health", 20))
	
	scan_prompt_label.text = "✅ HERO SELECTED!\n\nPreparing for matchmaking..."
	status_label.text = "Hero confirmed - entering matchmaking queue"
	
	# Stop timeout timer
	if scan_timeout_timer:
		scan_timeout_timer.stop()
	
	# Log hero selection
	server_logger.log_nfc_scan(hero_data.get("sku", ""), true, {
		"hero_name": hero_data.get("name", ""),
		"selection_type": "hero",
		"scene": "hero_selection"
	})
	
	server_logger.log_system_event("hero_selected", {
		"hero_sku": hero_data.get("sku", ""),
		"hero_name": hero_data.get("name", ""),
		"hero_stats": {
			"attack": hero_data.get("attack", 1),
			"health": hero_data.get("health", 20)
		}
	})
	
	# Wait a moment then proceed to matchmaking
	await get_tree().create_timer(2.0).timeout
	
	# Tell game state manager about hero selection
	if game_state_manager:
		game_state_manager.select_hero(hero_data)
	else:
		# Fallback - go directly to matchmaking scene
		get_tree().change_scene_to_file("res://matchmaking_scene.tscn")

func cancel_hero_selection():
	"""Cancel hero selection and return to menu"""
	print("❌ Hero selection cancelled")
	
	server_logger.log_system_event("hero_selection_cancelled", {})
	
	# Return to player menu
	get_tree().change_scene_to_file("res://player_menu.tscn")

func _on_scan_timeout():
	"""Handle hero selection timeout"""
	print("⏰ Hero selection timed out")
	
	status_label.text = "Selection timed out - returning to menu"
	scan_prompt_label.text = "⏰ TIME OUT\n\nReturning to main menu..."
	
	server_logger.log_system_event("hero_selection_timeout", {})
	
	# Wait a moment then return to menu
	await get_tree().create_timer(3.0).timeout
	cancel_hero_selection()

# === NFC CARD SCANNING ===

func _on_nfc_card_detected(card_data: Dictionary):
	"""Handle NFC card detection"""
	var card_type = card_data.get("type", "unknown")
	
	if card_type == "hero":
		select_hero(card_data)
	else:
		print("⚠️ Invalid card type for hero selection: ", card_type)
		
		# Show error message
		scan_prompt_label.text = "❌ INVALID CARD\n\nPlease scan a HERO card\nNot a " + card_type + " card"
		
		# Reset after a moment
		await get_tree().create_timer(2.0).timeout
		scan_prompt_label.text = "🃏 SCAN YOUR HERO CARD\n\nPlace your hero card on the NFC reader\nto select your champion for battle"
