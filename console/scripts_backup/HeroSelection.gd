extends Control

# Hero Selection Scene
# Player scans a Creature or Structure card to be their starting hero

signal hero_confirmed(hero_data: Dictionary)

@onready var instruction_panel = $InstructionPanel
@onready var instruction_label = $InstructionPanel/InstructionLabel
@onready var scan_animation = $InstructionPanel/ScanAnimation

@onready var hero_preview_panel = $HeroPreviewPanel
@onready var hero_card_display = $HeroPreviewPanel/HeroCardDisplay
@onready var hero_name_label = $HeroPreviewPanel/HeroName
@onready var hero_stats_panel = $HeroPreviewPanel/StatsPanel
@onready var confirm_button = $HeroPreviewPanel/ConfirmButton
@onready var cancel_button = $HeroPreviewPanel/CancelButton

@onready var opponent_status_panel = $OpponentStatusPanel
@onready var opponent_status_label = $OpponentStatusPanel/StatusLabel

@onready var background_video = $BackgroundVideo
@onready var hero_reveal_video = $HeroRevealVideo

var nfc_manager
var network_client
var scanned_hero_data: Dictionary = {}
var waiting_for_opponent: bool = false

func _ready():
	Logger.log_info("HeroSelection", "Hero selection scene loaded")
	Global.current_scene = "HeroSelection"
	
	setup_ui()
	setup_nfc()
	setup_networking()
	start_background_ambiance()

func setup_ui():
	"""Initialize hero selection UI"""
	instruction_label.text = "Scan your starting Hero\n(Creature or Structure card)"
	
	# Hide preview panel initially
	hero_preview_panel.visible = false
	
	# Connect button signals
	confirm_button.pressed.connect(_on_confirm_pressed)
	cancel_button.pressed.connect(_on_cancel_pressed)
	
	# Show scanning animation
	start_scan_animation()

func setup_nfc():
	"""Setup NFC scanning for hero selection"""
	nfc_manager = Global.get_nfc_manager()
	if nfc_manager:
		# Connect NFC signals
		if nfc_manager.has_signal("card_scanned"):
			nfc_manager.card_scanned.connect(_on_card_scanned)
		if nfc_manager.has_signal("scan_error"):
			nfc_manager.scan_error.connect(_on_scan_error)
		
		# Start NFC monitoring
		nfc_manager.start_monitoring()

func setup_networking():
	"""Setup network client for real-time updates"""
	network_client = Global.get_network_client()
	if network_client:
		# Connect network signals for opponent updates
		if network_client.has_signal("message_received"):
			network_client.message_received.connect(_on_network_message)

func start_background_ambiance():
	"""Start background video for hero selection"""
	background_video.stream = load("res://assets/videos/ui/hero_selection_background.mp4")
	background_video.loop = true
	background_video.play()

func start_scan_animation():
	"""Start NFC scan animation"""
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property(scan_animation, "modulate:a", 0.3, 1.0)
	tween.tween_property(scan_animation, "modulate:a", 1.0, 1.0)

func _on_card_scanned(card_data: Dictionary):
	"""Handle NFC card scan"""
	Logger.log_info("HeroSelection", "Card scanned", {"name": card_data.get("name")})
	
	# Check if card is valid hero
	if not _is_valid_hero_card(card_data):
		show_invalid_card_feedback(card_data)
		return
	
	# Store scanned hero data
	scanned_hero_data = card_data
	
	# Show hero preview
	show_hero_preview(card_data)
	
	# Play hero reveal video
	play_hero_reveal_video(card_data)

func _is_valid_hero_card(card_data: Dictionary) -> bool:
	"""Check if scanned card is a valid hero (Creature or Structure)"""
	var category = card_data.get("category", "")
	var status = card_data.get("status", "")
	var owner_id = card_data.get("owner_id", 0)
	
	# Must be creature or structure
	if category not in ["CREATURE", "STRUCTURE"]:
		return false
	
	# Must be activated
	if status != "activated":
		return false
	
	# Must be owned by current player
	if owner_id != Global.player_id:
		return false
	
	return true

func show_invalid_card_feedback(card_data: Dictionary):
	"""Show feedback for invalid card scans"""
	var category = card_data.get("category", "")
	var status = card_data.get("status", "")
	var owner_id = card_data.get("owner_id", 0)
	
	var error_message = ""
	
	if category not in ["CREATURE", "STRUCTURE"]:
		error_message = "Please scan a Creature or Structure card"
	elif status != "activated":
		error_message = "Card needs activation. Use your phone to activate."
	elif owner_id != Global.player_id:
		error_message = "This card belongs to another player"
	else:
		error_message = "Invalid card for hero selection"
	
	# Show error feedback
	_show_error_popup(error_message)
	
	# Play error sound
	var error_audio = AudioStreamPlayer.new()
	error_audio.stream = load("res://assets/sounds/nfc/scan_error.ogg")
	add_child(error_audio)
	error_audio.play()
	error_audio.finished.connect(func(): error_audio.queue_free())

func show_hero_preview(card_data: Dictionary):
	"""Display hero card preview"""
	Logger.log_info("HeroSelection", "Showing hero preview")
	
	# Show preview panel
	hero_preview_panel.visible = true
	
	# Update hero information
	hero_name_label.text = card_data.get("name", "Unknown Hero")
	
	# Display stats
	var stats = card_data.get("base_stats", {})
	var stats_text = ""
	
	if card_data.get("category") == "CREATURE":
		stats_text += "Attack: " + str(stats.get("attack", 0)) + "\n"
		stats_text += "Defense: " + str(stats.get("defense", 0)) + "\n"
		stats_text += "Health: " + str(stats.get("health", 0)) + "\n"
		stats_text += "Energy/Turn: " + str(stats.get("energy_per_turn", 1))
	else:  # STRUCTURE
		stats_text += "Health: " + str(stats.get("health", 0)) + "\n"
		stats_text += "Energy/Turn: " + str(stats.get("energy_per_turn", 1)) + "\n"
		stats_text += "Special: " + str(stats.get("special_ability", "None"))
	
	hero_stats_panel.get_node("StatsLabel").text = stats_text
	
	# TODO: Load and display card artwork
	# hero_card_display.texture = load("res://assets/cards/" + card_data.product_sku + ".png")
	
	# Enable confirm button
	confirm_button.disabled = false

func play_hero_reveal_video(card_data: Dictionary):
	"""Play hero reveal video"""
	var video_path = "res://assets/videos/cards/reveals/" + card_data.get("product_sku", "") + "_reveal.mp4"
	
	# Check if video exists
	if ResourceLoader.exists(video_path):
		hero_reveal_video.stream = load(video_path)
		hero_reveal_video.play()
		Logger.log_info("HeroSelection", "Playing hero reveal video: " + video_path)
	else:
		# Use generic hero reveal video
		hero_reveal_video.stream = load("res://assets/videos/cards/generic_hero_reveal.mp4")
		hero_reveal_video.play()
		Logger.log_info("HeroSelection", "Playing generic hero reveal video")

func _on_confirm_pressed():
	"""Handle hero confirmation"""
	if scanned_hero_data.is_empty():
		Logger.log_warning("HeroSelection", "No hero selected for confirmation")
		return
	
	Logger.log_info("HeroSelection", "Hero confirmed", {"hero": scanned_hero_data.get("name")})
	
	# Disable UI
	confirm_button.disabled = true
	cancel_button.disabled = true
	nfc_manager.stop_monitoring()
	
	# Send hero selection to server
	await _send_hero_selection_to_server()
	
	# Wait for opponent
	show_waiting_for_opponent()

func _on_cancel_pressed():
	"""Handle hero selection cancellation"""
	Logger.log_info("HeroSelection", "Hero selection cancelled")
	
	# Clear selection
	scanned_hero_data = {}
	hero_preview_panel.visible = false
	confirm_button.disabled = true
	
	# Resume scanning
	instruction_label.text = "Scan your starting Hero\n(Creature or Structure card)"

func _send_hero_selection_to_server():
	"""Send hero selection to server via WebSocket"""
	if not network_client:
		Logger.log_error("HeroSelection", "No network client available")
		return
	
	var message = {
		"type": "match.hero_selected",
		"hero_card_id": scanned_hero_data.get("id"),
		"hero_data": scanned_hero_data,
		"timestamp": Time.get_datetime_string_from_system()
	}
	
	network_client.send_message(message)
	Logger.log_info("HeroSelection", "Hero selection sent to server")

func show_waiting_for_opponent():
	"""Show waiting for opponent UI"""
	waiting_for_opponent = true
	
	instruction_label.text = "Hero Selected!\nWaiting for opponent..."
	opponent_status_label.text = "Opponent selecting hero..."
	opponent_status_panel.visible = true
	
	# Start waiting animation
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property(opponent_status_panel, "modulate:a", 0.5, 1.0)
	tween.tween_property(opponent_status_panel, "modulate:a", 1.0, 1.0)

func _on_network_message(message: Dictionary):
	"""Handle network messages during hero selection"""
	var msg_type = message.get("type", "")
	
	match msg_type:
		"match.opponent_hero_selected":
			_on_opponent_hero_selected(message)
		"match.both_heroes_ready":
			_on_both_heroes_ready(message)
		"match.arena_assigned":
			_on_arena_assigned(message)

func _on_opponent_hero_selected(message: Dictionary):
	"""Handle opponent hero selection"""
	var opponent_hero = message.get("hero_data", {})
	Logger.log_info("HeroSelection", "Opponent selected hero", {"hero": opponent_hero.get("name")})
	
	opponent_status_label.text = "Opponent selected: " + opponent_hero.get("name", "Unknown")

func _on_both_heroes_ready(message: Dictionary):
	"""Handle when both players have selected heroes"""
	Logger.log_info("HeroSelection", "Both heroes selected, waiting for arena assignment")
	opponent_status_label.text = "Generating arena..."

func _on_arena_assigned(message: Dictionary):
	"""Handle arena assignment and transition to arena reveal"""
	var arena_data = message.get("arena", {})
	Logger.log_info("HeroSelection", "Arena assigned", {"arena": arena_data.get("name")})
	
	# Transition to arena reveal
	transition_to_arena_reveal(arena_data)

func transition_to_arena_reveal(arena_data: Dictionary):
	"""Transition to arena reveal scene"""
	Logger.log_info("HeroSelection", "Transitioning to arena reveal")
	
	# Store arena data globally
	Global.current_arena = arena_data
	Global.selected_hero = scanned_hero_data
	
	# Fade out and change scene
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	await tween.finished
	
	get_tree().change_scene_to_file("res://scenes/ArenaReveal.tscn")

func _show_error_popup(message: String):
	"""Show error popup dialog"""
	var dialog = AcceptDialog.new()
	dialog.dialog_text = message
	dialog.title = "Invalid Card"
	add_child(dialog)
	dialog.popup_centered()
	dialog.confirmed.connect(func(): dialog.queue_free())

func _on_scan_error(error_message: String):
	"""Handle NFC scan errors"""
	Logger.log_error("HeroSelection", "NFC scan error: " + error_message)
	_show_error_popup("NFC Error: " + error_message)

func _input(event):
	"""Handle input during hero selection"""
	if Global.is_development() and event.is_pressed():
		if event is InputEventKey:
			match event.keycode:
				KEY_F1:
					# Simulate scanning Solar Vanguard
					nfc_manager.force_scan_card("RADIANT-001")
				KEY_F2:
					# Simulate scanning another hero
					nfc_manager.force_scan_card("VERDANT-007")
				KEY_ESCAPE:
					# Return to main menu
					get_tree().change_scene_to_file("res://scenes/MainMenu.tscn")

func _exit_tree():
	"""Cleanup when leaving hero selection"""
	Logger.log_info("HeroSelection", "Hero selection scene exiting")
	
	# Stop NFC monitoring
	if nfc_manager:
		nfc_manager.stop_monitoring()
	
	# Stop background video
	if background_video.is_playing():
		background_video.stop()
