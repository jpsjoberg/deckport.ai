extends Control

# Main Menu Scene - Post-login console interface
# Shows player info and main game options

# Removed unused signals - using direct button connections instead

@onready var player_info_panel = $PlayerInfoPanel
@onready var player_name_label = $PlayerInfoPanel/PlayerName
@onready var player_level_label = $PlayerInfoPanel/PlayerLevel
@onready var player_elo_label = $PlayerInfoPanel/PlayerELO
@onready var recent_matches_label = $PlayerInfoPanel/RecentMatches

@onready var match_game_button = $MenuButtons/MatchGameButton
@onready var collection_button = $MenuButtons/CollectionButton
@onready var settings_button = $MenuButtons/SettingsButton

@onready var nfc_status_panel = $NFCStatusPanel
@onready var nfc_status_label = $NFCStatusPanel/StatusLabel
@onready var last_scan_label = $NFCStatusPanel/LastScanLabel

@onready var background_video = $BackgroundVideo
@onready var ambient_audio = $AmbientAudio

var nfc_manager
var network_client

func _ready():
	Logger.log_info("MainMenu", "Main menu scene loaded")
	Global.current_scene = "MainMenu"
	
	setup_ui()
	setup_networking()
	setup_nfc()
	start_background_ambiance()

func setup_ui():
	"""Initialize the main menu UI with player information"""
	Logger.log_info("MainMenu", "Setting up UI")
	
	# Display player information
	player_name_label.text = Global.player_display_name if Global.player_display_name != "" else "Player"
	player_level_label.text = "Level " + str(Global.player_level if Global.player_level > 0 else 1)
	player_elo_label.text = "ELO: " + str(Global.player_elo)
	
	# Connect button signals
	match_game_button.pressed.connect(_on_match_game_pressed)
	collection_button.pressed.connect(_on_collection_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	
	# Update NFC status
	update_nfc_status("Ready")

func setup_networking():
	"""Initialize network client for real-time communication"""
	network_client = Global.get_network_client()
	if network_client:
		# Connect to server if not already connected
		if not Global.server_connected:
			network_client.connect_to_server()

func setup_nfc():
	"""Initialize NFC manager for card scanning"""
	nfc_manager = Global.get_nfc_manager()
	if nfc_manager:
		# Connect NFC signals
		if nfc_manager.has_signal("card_scanned"):
			nfc_manager.card_scanned.connect(_on_card_scanned)
		if nfc_manager.has_signal("scan_error"):
			nfc_manager.scan_error.connect(_on_nfc_error)
		nfc_manager.reader_status_changed.connect(_on_nfc_status_changed)
		
		# Start NFC monitoring
		nfc_manager.start_monitoring()

func start_background_ambiance():
	"""Start background video and audio for main menu"""
	# Play background video loop (optional)
	var video_path = "res://assets/videos/ui/main_menu_background.mp4"
	if ResourceLoader.exists(video_path):
		background_video.stream = load(video_path)
		background_video.loop = true
		background_video.play()
		Logger.log_info("MainMenu", "Background video loaded")
	else:
		Logger.log_info("MainMenu", "Background video not found - using solid background")
	
	# Play ambient audio (optional)
	var audio_path = "res://assets/sounds/ui/main_menu_ambient.ogg"
	if ResourceLoader.exists(audio_path):
		ambient_audio.stream = load(audio_path)
		ambient_audio.play()
		Logger.log_info("MainMenu", "Ambient audio loaded")
	else:
		Logger.log_info("MainMenu", "Ambient audio not found - silent mode")
	
	Logger.log_info("MainMenu", "Background ambiance started")

func _on_match_game_pressed():
	"""Handle Match Game button press"""
	Logger.log_info("MainMenu", "Match Game requested")
	Global.log_event("match_game_requested")
	
	# Check if player has any heroes (creatures/structures)
	if not has_available_heroes():
		show_no_heroes_dialog()
		return
	
	# Transition to hero selection
	transition_to_hero_selection()

func _on_collection_pressed():
	"""Handle Collection button press"""
	Logger.log_info("MainMenu", "Collection requested")
	Global.log_event("collection_requested")
	# TODO: Implement collection screen
	print("🃏 Collection screen would open here")

func _on_settings_pressed():
	"""Handle Settings button press"""
	Logger.log_info("MainMenu", "Settings requested")
	# Settings are managed on phone, show QR code for settings
	show_settings_qr()

func _on_card_scanned(card_data: Dictionary):
	"""Handle NFC card scan in main menu"""
	Logger.log_info("MainMenu", "Card scanned in main menu", {"card_id": card_data.get("id")})
	
	update_nfc_status("Card Detected: " + card_data.get("name", "Unknown"))
	last_scan_label.text = "Last: " + card_data.get("name", "Unknown")
	
	# Play scan feedback
	play_scan_feedback(card_data)
	
	# Check if card needs activation
	if card_data.get("status") == "unactivated":
		show_activation_dialog(card_data)
	else:
		show_card_preview(card_data)

func _on_nfc_error(error_message: String):
	"""Handle NFC scanning errors"""
	Logger.log_error("MainMenu", "NFC error: " + error_message)
	update_nfc_status("NFC Error: " + error_message)

func _on_nfc_status_changed(status: String):
	"""Handle NFC reader status changes"""
	Logger.log_info("MainMenu", "NFC status changed: " + status)
	update_nfc_status(status)

func update_nfc_status(status: String):
	"""Update NFC status display"""
	nfc_status_label.text = "NFC: " + status
	
	# Change color based on status
	if status.begins_with("Ready"):
		nfc_status_label.modulate = Color.GREEN
	elif status.begins_with("Error"):
		nfc_status_label.modulate = Color.RED
	else:
		nfc_status_label.modulate = Color.YELLOW

func has_available_heroes() -> bool:
	"""Check if player has any hero cards (creatures/structures)"""
	# TODO: Query player's card collection from server
	# For now, assume they have heroes
	return true

func show_no_heroes_dialog():
	"""Show dialog when player has no hero cards"""
	var dialog = AcceptDialog.new()
	dialog.dialog_text = "You need at least one Creature or Structure card to play.\nScan a hero card or visit the shop."
	dialog.title = "No Heroes Available"
	add_child(dialog)
	dialog.popup_centered()
	
	# Auto-remove dialog after it's closed
	dialog.confirmed.connect(func(): dialog.queue_free())

func show_activation_dialog(card_data: Dictionary):
	"""Show card activation dialog for unactivated cards"""
	Logger.log_info("MainMenu", "Showing activation dialog for card: " + card_data.get("name", ""))
	
	# TODO: Implement card activation scene
	# For now, show simple dialog
	var dialog = AcceptDialog.new()
	dialog.dialog_text = "Card '" + card_data.get("name", "Unknown") + "' needs activation.\nUse your phone to activate this card."
	dialog.title = "Card Activation Required"
	add_child(dialog)
	dialog.popup_centered()
	dialog.confirmed.connect(func(): dialog.queue_free())

func show_card_preview(card_data: Dictionary):
	"""Show preview of scanned card"""
	Logger.log_info("MainMenu", "Showing card preview: " + card_data.get("name", ""))
	
	# TODO: Implement card preview popup
	# For now, just log the card info
	print("📱 Card Preview: ", card_data)

func play_scan_feedback(_card_data: Dictionary):
	"""Play audio/visual feedback for card scan"""
	# Play scan sound
	var scan_audio = AudioStreamPlayer.new()
	scan_audio.stream = load("res://assets/sounds/nfc/card_scan_success.ogg")
	add_child(scan_audio)
	scan_audio.play()
	
	# Remove audio player when done
	scan_audio.finished.connect(func(): scan_audio.queue_free())
	
	# Visual feedback - brief flash or animation
	var tween = create_tween()
	nfc_status_panel.modulate = Color.CYAN
	tween.tween_property(nfc_status_panel, "modulate", Color.WHITE, 0.5)

func transition_to_hero_selection():
	"""Transition to hero selection scene"""
	Logger.log_info("MainMenu", "Transitioning to hero selection")
	
	# Fade out current scene
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	await tween.finished
	
	# Change to hero selection scene
	get_tree().change_scene_to_file("res://scenes/HeroSelection.tscn")

func show_settings_qr():
	"""Show QR code for phone-based settings"""
	Logger.log_info("MainMenu", "Showing settings QR code")
	
	# TODO: Generate settings QR code
	var dialog = AcceptDialog.new()
	dialog.dialog_text = "Scan this QR code with your phone to access settings and manage your account."
	dialog.title = "Settings"
	add_child(dialog)
	dialog.popup_centered()
	dialog.confirmed.connect(func(): dialog.queue_free())

func _input(event):
	"""Handle input in main menu"""
	if event.is_pressed():
		# Development shortcuts
		if Global.is_development():
			if event is InputEventKey:
				match event.keycode:
					KEY_1:
						_on_match_game_pressed()
					KEY_2:
						_on_collection_pressed()
					KEY_3:
						_on_settings_pressed()
					KEY_ESCAPE:
						# Logout and return to auth
						Global.player_token = ""
						get_tree().change_scene_to_file("res://scenes/AuthQR.tscn")

func _exit_tree():
	"""Cleanup when leaving main menu"""
	Logger.log_info("MainMenu", "Main menu scene exiting")
	
	# Stop background media
	if background_video.is_playing():
		background_video.stop()
	if ambient_audio.playing:
		ambient_audio.stop()
	
	# Stop NFC monitoring
	if nfc_manager:
		nfc_manager.stop_monitoring()
