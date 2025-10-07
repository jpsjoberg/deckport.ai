extends Control

# Simple Boot Screen - No dependencies, just works

@onready var logo_container = $CenterContainer/VBoxContainer/LogoContainer
@onready var logo_image = $CenterContainer/VBoxContainer/LogoContainer/LogoImage
@onready var logo_label = $CenterContainer/VBoxContainer/LogoLabel
@onready var status_label = $CenterContainer/VBoxContainer/StatusLabel
@onready var progress_bar = $CenterContainer/VBoxContainer/ProgressBar
@onready var background_video = $BackgroundVideo

var server_logger
var device_connection_manager
var boot_start_time: float

var boot_steps = [
	"Initializing console...",
	"Loading systems...",
	"Registering device...",
	"Authenticating device...",
	"Ready!"
]
var current_step = 0
var connection_established = false

func _ready():
	boot_start_time = Time.get_ticks_msec() / 1000.0
	print("🎮 Simple Boot Screen loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get device connection manager autoload singleton
	if has_node("/root/DeviceConnectionManager"):
		device_connection_manager = get_node("/root/DeviceConnectionManager")
		print("✅ DeviceConnectionManager autoload found")
	else:
		print("⚠️ DeviceConnectionManager not found - creating fallback")
		device_connection_manager = preload("res://device_connection_manager.gd").new()
		add_child(device_connection_manager)
	
	# Update server logger with device UID once it's available
	await get_tree().process_frame  # Wait for device connection manager to initialize
	if device_connection_manager.get_device_uid() != "":
		server_logger.set_device_id(device_connection_manager.get_device_uid())
	
	# Connect signals for device connection events
	device_connection_manager.device_registered.connect(_on_device_registered)
	device_connection_manager.device_authenticated.connect(_on_device_authenticated)
	device_connection_manager.connection_verified.connect(_on_connection_verified)
	device_connection_manager.error_occurred.connect(_on_connection_error)
	
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
	"""Enhanced boot sequence with device connection"""
	logo_label.text = "DECKPORT CONSOLE"
	progress_bar.value = 0
	
	# Initial steps (system initialization)
	for i in range(2):  # First 2 steps: Initialize and Load systems
		status_label.text = boot_steps[i]
		progress_bar.value = (i + 1) * 20
		print("Boot step: ", boot_steps[i])
		
		# Log each boot step
		server_logger.log_system_event("boot_step", {
			"step": i + 1,
			"message": boot_steps[i],
			"progress": (i + 1) * 20
		})
		
		await get_tree().create_timer(1.0).timeout
	
	# Device connection steps will be handled by signal callbacks
	# The connection manager will automatically start when initialized
	
	# Wait for device connection to complete or timeout
	var timeout_counter = 0
	while not connection_established and timeout_counter < 30:  # 30 second timeout
		await get_tree().create_timer(1.0).timeout
		timeout_counter += 1
	
	if not connection_established:
		# Connection failed, but allow continue with limited functionality
		status_label.text = "⚠️ Connection failed - Limited functionality"
		progress_bar.value = 80
		server_logger.log_system_event("boot_connection_failed", {"timeout": timeout_counter})
		await get_tree().create_timer(2.0).timeout
	
	# Final step
	current_step = boot_steps.size() - 1
	status_label.text = boot_steps[current_step]
	progress_bar.value = 100
	
	# Log boot completion
	var boot_time = (Time.get_ticks_msec() / 1000.0) - boot_start_time
	server_logger.log_console_boot(boot_time)
	
	await get_tree().create_timer(1.0).timeout
	
	# Boot complete - show simple menu
	show_simple_menu()

func show_simple_menu():
	"""Auto-transition to QR Login after boot complete"""
	status_label.text = "Boot Complete!\n\nLoading QR Login..."
	
	# Keep logo as is (image or text)
	if logo_label.visible:
		logo_label.text = "DECKPORT CONSOLE"
	
	progress_bar.visible = false
	
	# Auto-transition to QR login after brief delay
	await get_tree().create_timer(1.0).timeout
	load_qr_login_directly()

func _input(event):
	"""Handle input - minimal controls during boot"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_R:
			print("🔄 Retrying device connection...")
			connection_established = false
			progress_bar.value = 0
			device_connection_manager.force_reconnect()

func load_qr_login_directly():
	"""Load QR login scene directly after boot (no menu in between)"""
	print("📱 Auto-transitioning to QR login after boot")
	server_logger.log_scene_change("boot", "qr_login")
	get_tree().change_scene_to_file("res://qr_login_scene.tscn")

func show_connection_status():
	"""Show detailed connection status to help debug issues"""
	var status_text = "❌ DEVICE CONNECTION FAILED\n\n"
	status_text += "Troubleshooting:\n"
	status_text += "• Check if API server is running on port 8002\n"
	status_text += "• Verify network connectivity\n"
	status_text += "• Check server logs for errors\n\n"
	status_text += "Press R to retry connection\n"
	status_text += "Press ESC to exit"
	
	status_label.text = status_text

func _show_pending_approval_screen():
	"""Show screen indicating device is pending admin approval"""
	print("📋 Showing pending approval screen")
	
	# Update the status display
	status_label.text = """⏳ Device Registration Complete
	
🔄 Waiting for Admin Approval

Your console has been registered successfully but requires admin approval before it can be used.

🆔 Device ID: """ + device_connection_manager.device_uid + """

💡 An administrator can approve this device in the admin panel.

Press ESC to exit"""
	
	# Set progress to show partial completion
	progress_bar.value = 60
	
	# The console will stay in this state until manually restarted after approval

# Device Connection Signal Handlers
func _on_connection_verified(success: bool, response: Dictionary):
	"""Handle server connection verification result"""
	if success:
		print("✅ Server connection established")
		status_label.text = "✅ Server connected - Registering device..."
		progress_bar.value = 40
		server_logger.log_system_event("server_connected", response)
	else:
		print("❌ Server connection failed")
		server_logger.log_system_event("server_connection_failed", response)

func _on_device_registered(success: bool, message: String):
	"""Handle device registration result"""
	if success:
		print("✅ Device registration: ", message)
		status_label.text = "📝 Device registered - Authenticating..."
		progress_bar.value = 60
		server_logger.log_system_event("device_registered", {"message": message})
	else:
		print("❌ Device registration failed: ", message)
		server_logger.log_system_event("device_registration_failed", {"message": message})

func _on_device_authenticated(success: bool, token: String):
	"""Handle device authentication result"""
	if success:
		print("✅ Device authenticated successfully")
		status_label.text = "🔐 Device authenticated - Ready!"
		progress_bar.value = 80
		connection_established = true
		server_logger.log_system_event("device_authenticated", {"token_length": token.length()})
	elif token == "pending_approval":
		print("⏳ Device pending admin approval")
		status_label.text = "⏳ Pending Admin Approval"
		progress_bar.value = 60
		# Show pending approval message but don't exit
		server_logger.log_system_event("device_pending_approval", {"device_uid": device_connection_manager.device_uid})
		_show_pending_approval_screen()
	else:
		print("❌ Device authentication failed")
		server_logger.log_system_event("device_authentication_failed", {})

func _on_connection_error(error_type: String, message: String, details: Dictionary):
	"""Handle connection errors with detailed logging"""
	print("💥 Connection error (", error_type, "): ", message)
	status_label.text = "❌ Connection Error: " + message
	server_logger.log_error("DeviceConnection", error_type + ": " + message, details)
	
	# Update progress bar to show error state
	progress_bar.value = 30
