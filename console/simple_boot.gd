extends Control

# Simple Boot Screen - No dependencies, just works

@onready var logo_container = $CenterContainer/VBoxContainer/LogoContainer
@onready var logo_image = $CenterContainer/VBoxContainer/LogoContainer/LogoImage
@onready var logo_label = $CenterContainer/VBoxContainer/LogoLabel
@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var progress_bar = $CenterContainer/VBoxContainer/ProgressBar
@onready var background_video = $BackgroundVideo

var server_logger
var boot_start_time: float

var boot_steps = [
	"Initializing console...",
	"Loading systems...",
	"Connecting to server...",
	"Ready!"
]
var current_step = 0

func _ready():
	boot_start_time = Time.get_ticks_msec() / 1000.0
	print("🎮 Simple Boot Screen loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Enable fullscreen mode
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	print("🖥️ Fullscreen mode enabled")
	
	# Log boot start
	server_logger.log_system_event("console_boot_start", {
		"godot_version": Engine.get_version_info(),
		"platform": OS.get_name()
	})
	
	setup_background_video()
	setup_logo()
	start_boot_sequence()

func setup_background_video():
	"""Setup background video for boot screen portal presentation"""
	# Godot 4.2 supports .ogv (Ogg Theora) files for VideoStreamPlayer
	# Primary portal video path - try .ogv first (recommended)
	var portal_video_paths = [
		"res://assets/videos/boot/portal_background.ogv",
		"res://assets/videos/boot/portal_background.mp4"
	]
	# Alternative boot video paths
	var boot_video_paths = [
		"res://assets/videos/boot/boot_background.ogv",
		"res://assets/videos/boot/boot_background.mp4"
	]
	# UI video paths (fallback)
	var ui_video_paths = [
		"res://assets/videos/ui/boot_portal.ogv",
		"res://assets/videos/ui/boot_portal.mp4"
	]
	
	var video_loaded = false
	
	# Try portal video paths in priority order
	for portal_video_path in portal_video_paths:
		if ResourceLoader.exists(portal_video_path):
			print("📁 Found portal video: ", portal_video_path)
			background_video.stream = load(portal_video_path)
			if background_video.stream != null:
				background_video.loop = true
				background_video.volume_db = -80.0  # Mute audio
				background_video.visible = true
				background_video.play()
				server_logger.log_system_event("portal_video_loaded", {"path": portal_video_path})
				print("🌀 Portal background video loaded and playing")
				video_loaded = true
				break
			else:
				print("❌ Failed to load portal video: ", portal_video_path)
	
	# Try boot video if portal video not loaded
	if not video_loaded:
		for boot_video_path in boot_video_paths:
			if ResourceLoader.exists(boot_video_path):
				print("📁 Found boot video: ", boot_video_path)
				background_video.stream = load(boot_video_path)
				if background_video.stream != null:
					background_video.loop = true
					background_video.volume_db = -80.0  # Mute audio
					background_video.play()
					server_logger.log_system_event("background_video_loaded", {"path": boot_video_path})
					print("🎬 Boot background video loaded and playing")
					video_loaded = true
					break
				else:
					print("❌ Failed to load boot video: ", boot_video_path)
	
	# Try UI video fallback if still not loaded
	if not video_loaded:
		for ui_video_path in ui_video_paths:
			if ResourceLoader.exists(ui_video_path):
				print("📁 Found UI video: ", ui_video_path)
				background_video.stream = load(ui_video_path)
				if background_video.stream != null:
					background_video.loop = true
					background_video.volume_db = -80.0  # Mute audio
					background_video.play()
					server_logger.log_system_event("ui_video_loaded", {"path": ui_video_path})
					print("🎬 UI background video loaded and playing")
					video_loaded = true
					break
				else:
					print("❌ Failed to load UI video: ", ui_video_path)
	
	if not video_loaded:
		# Show background ColorRect and create portal-themed animated background
		$Background.visible = true
		create_portal_animation()
	else:
		# Hide background ColorRect so video is visible
		$Background.visible = false

func create_portal_animation():
	"""Create animated portal-like background when no video is available"""
	print("🌀 Creating portal animation fallback")
	
	# Animate background with portal-like colors
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property($Background, "color", Color(0.15, 0.05, 0.25, 1), 3.0)  # Deep purple
	tween.tween_property($Background, "color", Color(0.05, 0.15, 0.35, 1), 3.0)  # Deep blue
	tween.tween_property($Background, "color", Color(0.25, 0.05, 0.15, 1), 3.0)  # Deep red
	tween.tween_property($Background, "color", Color(0.05, 0.25, 0.15, 1), 3.0)  # Deep green
	
	server_logger.log_system_event("portal_animation", {"type": "color_cycle_portal"})
	print("🎨 Portal animation started")

func setup_logo():
	"""Setup logo image and text"""
	# Try to load logo image
	var logo_paths = [
		"res://assets/logos/deckport_logo.png",
		"res://assets/logos/deckport_logo.jpg",
		"res://assets/logos/deckport_logo.svg",
		"res://assets/logos/logo.png",
		"res://assets/logos/logo.jpg"
	]
	
	var logo_loaded = false
	for logo_path in logo_paths:
		if ResourceLoader.exists(logo_path):
			var texture = load(logo_path)
			logo_image.texture = texture
			logo_image.visible = true
			logo_label.visible = false  # Hide text when image is available
			server_logger.log_system_event("logo_loaded", {"path": logo_path})
			print("🏷️ Logo image loaded: ", logo_path)
			logo_loaded = true
			break
	
	if not logo_loaded:
		# Use text logo as fallback
		logo_image.visible = false
		logo_label.visible = true
		logo_label.text = "DECKPORT CONSOLE"
		print("🏷️ Using text logo fallback")
		server_logger.log_system_event("logo_fallback", {"type": "text"})

func start_boot_sequence():
	"""Simple boot sequence with progress"""
	logo_label.text = "DECKPORT CONSOLE"
	progress_bar.value = 0
	
	for i in range(boot_steps.size()):
		status_label.text = boot_steps[i]
		progress_bar.value = (i + 1) * 25
		print("Boot step: ", boot_steps[i])
		
		# Log each boot step
		server_logger.log_system_event("boot_step", {
			"step": i + 1,
			"message": boot_steps[i],
			"progress": (i + 1) * 25
		})
		
		await get_tree().create_timer(1.0).timeout
	
	# Log boot completion
	var boot_time = (Time.get_ticks_msec() / 1000.0) - boot_start_time
	server_logger.log_console_boot(boot_time)
	
	# Boot complete - show simple menu
	show_simple_menu()

func show_simple_menu():
	"""Show boot complete message"""
	status_label.text = "Boot Complete!\n\nPress SPACE for QR Login\nPress ESC to quit"
	
	# Keep logo as is (image or text)
	if logo_label.visible:
		logo_label.text = "DECKPORT CONSOLE"
	
	progress_bar.visible = false

func _input(event):
	"""Handle input"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE:
			print("📱 Loading QR login...")
			load_main_menu()
		elif event.keycode == KEY_ESCAPE:
			print("👋 Exiting console")
			get_tree().quit()

func load_main_menu():
	"""Load QR login scene directly after boot"""
	print("📱 Transitioning to QR login")
	server_logger.log_scene_change("boot", "qr_login")
	get_tree().change_scene_to_file("res://qr_login_scene.tscn")
