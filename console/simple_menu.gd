extends Control

# Simple Main Menu - No autoload dependencies

@onready var title_label = $CenterContainer/VBoxContainer/TitleLabel
@onready var menu_container = $CenterContainer/VBoxContainer/MenuContainer
@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var background_video = $BackgroundVideo

# Simple state variables (no autoload needed)
var player_logged_in = false
var device_id = "DECK_DEV_CONSOLE_01"  # Fixed device ID for development
var server_logger

func _ready():
	print("🎮 Simple Menu loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_scene_change("boot", "main_menu")
	
	setup_background_video()
	setup_menu()

func setup_background_video():
	"""Setup background video for main menu"""
	var video_path = "res://assets/videos/ui/main_menu_background.mp4"
	if ResourceLoader.exists(video_path):
		background_video.stream = load(video_path)
		background_video.loop = true
		background_video.play()
		server_logger.log_system_event("menu_video_loaded", {"path": video_path})
		print("🎬 Menu background video loaded")
	else:
		# Animated background fallback
		var tween = create_tween()
		tween.set_loops()
		tween.tween_property($Background, "color", Color(0.15, 0.1, 0.2, 1), 3.0)
		tween.tween_property($Background, "color", Color(0.05, 0.1, 0.15, 1), 3.0)
		server_logger.log_system_event("menu_animation", {"type": "color_cycle"})
		print("🎨 Menu background animation started")

func setup_menu():
	"""Setup the main menu"""
	title_label.text = "DECKPORT CONSOLE"
	
	if player_logged_in:
		show_game_menu()
	else:
		show_login_menu()

func show_login_menu():
	"""Show login options"""
	status_label.text = "Press 1 for QR Login\nPress 2 for Guest Mode\nPress ESC to exit"
	
func show_game_menu():
	"""Show game options"""
	status_label.text = "Press 1 for Match Game\nPress 2 for Collection\nPress ESC to logout"

func _input(event):
	"""Handle menu input"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			if player_logged_in:
				logout()
			else:
				print("👋 Exiting console")
				get_tree().quit()

		elif event.keycode == KEY_1:
			if player_logged_in:
				server_logger.log_button_press("match_game", "main_menu")
				start_match_game()
			else:
				server_logger.log_button_press("qr_login", "main_menu")
				start_qr_login()
		elif event.keycode == KEY_2:
			if player_logged_in:
				server_logger.log_button_press("collection", "main_menu")
				show_collection()
			else:
				server_logger.log_button_press("guest_mode", "main_menu")
				guest_mode()

func start_qr_login():
	"""Start real QR code login process"""
	print("📱 Starting real QR login...")
	server_logger.log_user_action("qr_login_start", {})
	
	# Transition to dedicated QR login scene
	server_logger.log_scene_change("main_menu", "qr_login")
	get_tree().change_scene_to_file("res://qr_login_scene.tscn")

func guest_mode():
	"""Start guest mode"""
	print("👤 Starting guest mode...")
	server_logger.log_login_attempt("guest", true, {"mode": "guest"})
	player_logged_in = true
	status_label.text = "Guest mode activated!"
	await get_tree().create_timer(1.0).timeout
	show_game_menu()

func start_match_game():
	"""Start match game"""
	print("🎮 Starting match game...")
	status_label.text = "Match Game starting...\n\nQ/W/E - Simulate card scans\nTap screen areas for touch\nESC - Back to menu"

func show_collection():
	"""Show collection"""
	print("🃏 Showing collection...")
	status_label.text = "Card Collection\n\nQ/W/E - View cards\nTap screen areas for touch\nESC - Back to menu"

func logout():
	"""Logout player"""
	print("👋 Player logged out")
	player_logged_in = false
	show_login_menu()
