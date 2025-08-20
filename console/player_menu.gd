extends Control

# Player Menu - After successful login

@onready var title_label = $CenterContainer/VBoxContainer/TitleLabel
@onready var player_info = $CenterContainer/VBoxContainer/PlayerInfo
@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var background_video = $BackgroundVideo

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

func setup_background():
	"""Setup background video"""
	var video_path = "res://assets/videos/ui/player_menu_background.mp4"
	if ResourceLoader.exists(video_path):
		background_video.stream = load(video_path)
		background_video.loop = true
		background_video.play()
		print("🎬 Player menu background video loaded")
	else:
		# Animated background
		var tween = create_tween()
		tween.set_loops()
		tween.tween_property($Background, "color", Color(0.1, 0.2, 0.1, 1), 3.0)
		tween.tween_property($Background, "color", Color(0.2, 0.1, 0.2, 1), 3.0)
		print("🎨 Player menu background animation started")

func setup_menu():
	"""Setup player menu"""
	title_label.text = "WELCOME " + player_name.to_upper()
	player_info.text = "Level: 1 | ELO: " + str(player_elo) + " | ID: " + str(player_id)
	status_label.text = "Press 1 for Match Game\nPress 2 for Collection\nPress Q/W/E to scan cards\nPress ESC to logout"

func _input(event):
	"""Handle input"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			logout()
		elif event.keycode == KEY_F11:
			# Toggle fullscreen
			if DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
			else:
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		elif event.keycode == KEY_1:
			start_match_game()
		elif event.keycode == KEY_2:
			show_collection()
		elif event.keycode == KEY_Q:
			simulate_card_scan("RADIANT-001", "Solar Vanguard")
		elif event.keycode == KEY_W:
			simulate_card_scan("AZURE-014", "Tidecaller Sigil")
		elif event.keycode == KEY_E:
			simulate_card_scan("VERDANT-007", "Forest Guardian")

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

func start_match_game():
	"""Start match game"""
	print("🎮 Starting match game...")
	server_logger.log_user_action("match_game_start", {})
	status_label.text = "🎮 MATCH GAME\n\nQ/W/E - Scan hero cards\nESC - Back to menu"

func show_collection():
	"""Show collection"""
	print("🃏 Showing collection...")
	server_logger.log_user_action("collection_view", {})
	status_label.text = "🃏 CARD COLLECTION\n\nQ/W/E - View cards\nESC - Back to menu"

func logout():
	"""Logout and return to main menu"""
	print("👋 Player logged out")
	server_logger.log_user_action("logout", {})
	server_logger.log_scene_change("player_menu", "main_menu")
	get_tree().change_scene_to_file("res://simple_menu.tscn")
