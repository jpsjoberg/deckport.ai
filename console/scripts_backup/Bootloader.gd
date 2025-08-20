extends Control

# Deckport Console Bootloader
# First scene that loads when console starts
# Handles logo display, updates, and server connection

@onready var logo_container = $LogoContainer
@onready var logo_image = $LogoContainer/LogoImage
@onready var loading_label = $LoadingContainer/LoadingLabel
@onready var progress_bar = $LoadingContainer/ProgressBar
@onready var version_label = $VersionLabel

var boot_steps = [
	"Initializing console...",
	"Checking for updates...",
	"Connecting to server...",
	"Loading game data...",
	"Starting Deckport..."
]

var current_step = 0
var step_duration = 1.5  # seconds per step

func _ready():
	Logger.log_info("Bootloader", "Console bootloader started")
	Global.current_scene = "Bootloader"
	
	setup_ui()
	start_boot_sequence()

func setup_ui():
	"""Initialize the bootloader UI"""
	# Set version label
	version_label.text = "v" + Global.game_version
	
	# Set initial loading state
	loading_label.text = "Starting up..."
	progress_bar.value = 0
	
	Logger.log_info("Bootloader", "UI initialized")

func start_boot_sequence():
	"""Start the boot sequence with logo and loading steps"""
	Logger.log_info("Bootloader", "Starting boot sequence")
	
	# Show logo animation
	show_logo()
	
	# Wait a bit then start loading steps
	await get_tree().create_timer(2.0).timeout
	execute_boot_steps()

func show_logo():
	"""Display the Deckport logo with fade-in animation"""
	logo_container.modulate.a = 0.0
	
	var tween = create_tween()
	tween.tween_property(logo_container, "modulate:a", 1.0, 1.0)
	
	Logger.log_info("Bootloader", "Logo displayed")

func execute_boot_steps():
	"""Execute each boot step with progress updates"""
	for i in range(boot_steps.size()):
		current_step = i
		update_loading_display()
		
		# Execute the actual step
		await execute_step(i)
		
		# Update progress
		progress_bar.value = float(i + 1) / float(boot_steps.size()) * 100.0
		
		# Wait before next step
		await get_tree().create_timer(step_duration).timeout
	
	# Boot sequence complete
	complete_boot_sequence()

func execute_step(step_index: int):
	"""Execute a specific boot step"""
	match step_index:
		0:  # Initialize console
			await initialize_console()
		1:  # Check for updates  
			await check_for_updates()
		2:  # Connect to server
			await connect_to_server()
		3:  # Load game data
			await load_game_data()
		4:  # Start Deckport
			await prepare_main_menu()

func update_loading_display():
	"""Update the loading text and progress"""
	if current_step < boot_steps.size():
		loading_label.text = boot_steps[current_step]
		Logger.log_info("Bootloader", "Boot step: " + boot_steps[current_step])

func initialize_console():
	"""Initialize console systems"""
	Logger.log_info("Bootloader", "Initializing console systems")
	
	# Load settings
	Settings.load_settings()
	Settings.apply_settings()
	
	# Initialize Global state
	Global.load_settings()
	
	# Check if this is development mode
	if OS.has_environment("DECKPORT_DEV"):
		Global.set_server_environment(true)
		Logger.log_info("Bootloader", "Development mode enabled")

func check_for_updates():
	"""Check server for available updates"""
	Logger.log_info("Bootloader", "Checking for updates")
	
	if not Settings.auto_update:
		Logger.log_info("Bootloader", "Auto-update disabled, skipping")
		return
	
	# TODO: Implement actual update checking
	# For now, simulate the check
	await get_tree().create_timer(0.5).timeout
	
	Logger.log_info("Bootloader", "Update check complete")

func connect_to_server():
	"""Establish connection to game server and authenticate device"""
	Logger.log_info("Bootloader", "Connecting to server: " + Global.server_url)
	
	# Note: Device authentication is separate from player authentication
	# Device auth happens here, player auth happens via QR code later
	
	# Create AuthManager if not exists
	if not has_node("AuthManager"):
		var new_auth_manager = preload("res://scripts/AuthManager.gd").new()
		new_auth_manager.name = "AuthManager"
		add_child(new_auth_manager)
		
		# Connect signals
		new_auth_manager.device_authenticated.connect(_on_device_authenticated)
		new_auth_manager.authentication_error.connect(_on_auth_error)
	
	var auth_manager = get_node("AuthManager")
	
	# Try device authentication
	if auth_manager.is_device_authenticated():
		Logger.log_info("Bootloader", "Device already authenticated")
		Global.server_connected = true
		Global.connection_status = "connected"
	else:
		Logger.log_info("Bootloader", "Authenticating device...")
		auth_manager.authenticate_device()
		
		# Wait for authentication result
		await auth_manager.device_authenticated
		
		if Global.server_connected:
			Logger.log_info("Bootloader", "Device authentication successful")
		else:
			Logger.log_warning("Bootloader", "Device authentication failed - may need registration")

func load_game_data():
	"""Load necessary game data"""
	Logger.log_info("Bootloader", "Loading game data")
	
	# TODO: Load card data, player data, etc.
	# For now, simulate loading
	await get_tree().create_timer(0.8).timeout
	
	Logger.log_info("Bootloader", "Game data loaded")

func prepare_main_menu():
	"""Prepare to transition to main menu"""
	Logger.log_info("Bootloader", "Preparing main menu")
	
	# Final preparations
	await get_tree().create_timer(0.5).timeout
	
	Logger.log_info("Bootloader", "Ready to start game")

func complete_boot_sequence():
	"""Complete the boot sequence and transition to main menu"""
	Logger.log_info("Bootloader", "Boot sequence complete")
	
	loading_label.text = "Welcome to Deckport!"
	progress_bar.value = 100.0
	
	# Wait a moment then transition
	await get_tree().create_timer(1.0).timeout
	transition_to_main_menu()

func transition_to_main_menu():
	"""Transition to the main menu scene"""
	Logger.log_info("Bootloader", "Transitioning to main menu")
	
	# Fade out
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	await tween.finished
	
	# Change scene to QR Login for player authentication
	Logger.log_info("Bootloader", "Loading QR Login scene")
	get_tree().change_scene_to_file("res://scenes/QRLogin.tscn")
	
	print("🎮 Boot complete! Ready for player login.")
	Logger.log_info("Bootloader", "Boot sequence finished - QR Login loaded")

func _on_device_authenticated(success: bool):
	"""Handle device authentication result"""
	if success:
		Global.server_connected = true
		Global.connection_status = "connected"
		Logger.log_info("Bootloader", "Device authenticated successfully")
	else:
		Global.server_connected = false
		Global.connection_status = "auth_failed"
		Logger.log_error("Bootloader", "Device authentication failed")

func _on_auth_error(error: String):
	"""Handle authentication errors"""
	Logger.log_error("Bootloader", "Authentication error: " + error)
	Global.server_connected = false
	Global.connection_status = "error"
	
	# In production, might want to show error screen
	# For now, continue with limited functionality
	if not Global.is_development():
		loading_label.text = "Connection failed - limited mode"

func _input(event):
	"""Handle input during boot sequence"""
	# Allow skipping boot sequence in development mode
	if Global.is_development() and event.is_pressed():
		if event is InputEventKey and event.keycode == KEY_SPACE:
			Logger.log_info("Bootloader", "Boot sequence skipped (dev mode)")
			transition_to_main_menu()
