extends Control

# Matchmaking Scene - Find opponent for battle
# Shows matchmaking progress and opponent information when found

@onready var title_label = $VBoxContainer/TitleLabel
@onready var status_label = $VBoxContainer/StatusLabel
@onready var hero_display = $VBoxContainer/HeroDisplay
@onready var matchmaking_progress = $VBoxContainer/MatchmakingProgress
@onready var opponent_info = $VBoxContainer/OpponentInfo
@onready var background_video = $BackgroundVideo

var game_state_manager
var server_logger
var selected_hero: Dictionary = {}
var matchmaking_timer: Timer
var search_animation_timer: Timer
var search_dots: int = 0

func _ready():
	print("🔍 Matchmaking Scene loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get game state manager
	game_state_manager = get_node("/root/GameStateManager")
	if game_state_manager:
		selected_hero = game_state_manager.get_selected_hero()
		game_state_manager.player_matched.connect(_on_opponent_found)
	
	# Setup UI
	setup_matchmaking_ui()
	
	# Setup background
	setup_background()
	
	# Start matchmaking process
	start_matchmaking()

func setup_matchmaking_ui():
	"""Setup the matchmaking interface"""
	title_label.text = "FINDING OPPONENT"
	status_label.text = "Searching for a worthy adversary..."
	
	# Show selected hero
	if selected_hero.has("name"):
		hero_display.text = "YOUR CHAMPION\n\n" + selected_hero.get("name", "Unknown Hero") + "\nAttack: " + str(selected_hero.get("attack", 1)) + " | Health: " + str(selected_hero.get("health", 20))
	else:
		hero_display.text = "YOUR CHAMPION\n\nNo hero selected"
	
	matchmaking_progress.text = "🔍 Searching for opponent"
	opponent_info.text = ""
	
	print("🔍 Matchmaking UI configured")

func setup_background():
	"""Setup background video for matchmaking"""
	var matchmaking_background_paths = [
		"res://assets/videos/matchmaking/portal_search_background.ogv",
		"res://assets/videos/matchmaking/portal_search_background.mp4",
		"res://assets/videos/matchmaking/matchmaking_background.ogv",
		"res://assets/videos/matchmaking/matchmaking_background.mp4",
		"res://assets/videos/ui/search_background.ogv",
		"res://assets/videos/ui/search_background.mp4"
	]
	
	var video_loaded = false
	
	for video_path in matchmaking_background_paths:
		if ResourceLoader.exists(video_path):
			print("📁 Found matchmaking video: ", video_path)
			background_video.stream = load(video_path)
			if background_video.stream != null:
				background_video.loop = true
				background_video.volume_db = -80.0  # Mute audio
				background_video.visible = true
				background_video.play()
				
				server_logger.log_system_event("matchmaking_background_loaded", {
					"path": video_path
				})
				
				print("🌟 Matchmaking video loaded")
				video_loaded = true
				break
	
	if not video_loaded:
		# Create animated background fallback
		$Background.visible = true
		create_search_animation()
	else:
		$Background.visible = false

func create_search_animation():
	"""Create animated background fallback for matchmaking"""
	var tween = create_tween()
	tween.set_loops()
	tween.tween_property($Background, "color", Color(0.1, 0.1, 0.3, 1), 2.0)
	tween.tween_property($Background, "color", Color(0.3, 0.1, 0.1, 1), 2.0)
	tween.tween_property($Background, "color", Color(0.1, 0.3, 0.1, 1), 2.0)
	
	server_logger.log_system_event("matchmaking_animation_fallback", {"type": "search_cycle"})
	print("🎨 Matchmaking background animation started")

func start_matchmaking():
	"""Start the matchmaking process"""
	print("🔍 Starting matchmaking process")
	
	# Setup search animation
	search_animation_timer = Timer.new()
	add_child(search_animation_timer)
	search_animation_timer.wait_time = 0.5
	search_animation_timer.timeout.connect(_update_search_animation)
	search_animation_timer.start()
	
	# Setup matchmaking timeout (2 minutes)
	matchmaking_timer = Timer.new()
	add_child(matchmaking_timer)
	matchmaking_timer.wait_time = 120.0
	matchmaking_timer.timeout.connect(_on_matchmaking_timeout)
	matchmaking_timer.start()
	
	# Tell game state manager to start matchmaking
	if game_state_manager:
		# Game state manager will handle the actual matchmaking API call
		pass
	else:
		# Simulate matchmaking for testing
		simulate_matchmaking()
	
	server_logger.log_system_event("matchmaking_started", {
		"hero_sku": selected_hero.get("sku", ""),
		"hero_name": selected_hero.get("name", "")
	})

func simulate_matchmaking():
	"""Simulate finding an opponent for testing"""
	print("🎮 Simulating matchmaking...")
	
	# Wait 3-8 seconds to simulate search time
	var wait_time = randf_range(3.0, 8.0)
	await get_tree().create_timer(wait_time).timeout
	
	# Create fake opponent data
	var fake_opponent = {
		"player_id": 999,
		"player_name": "Test Opponent",
		"player_elo": 1050,
		"hero_name": "Fire Dragon",
		"hero_attack": 3,
		"hero_health": 15,
		"console_id": 888
	}
	
	_on_opponent_found(fake_opponent)

func _update_search_animation():
	"""Update the search animation dots"""
	search_dots = (search_dots + 1) % 4
	var dots = ".".repeat(search_dots)
	matchmaking_progress.text = "🔍 Searching for opponent" + dots

func _on_opponent_found(opponent_data: Dictionary):
	"""Handle opponent found"""
	print("✅ Opponent found: ", opponent_data.get("player_name", "Unknown"))
	
	# Stop timers
	if search_animation_timer:
		search_animation_timer.stop()
	if matchmaking_timer:
		matchmaking_timer.stop()
	
	# Update UI
	status_label.text = "Opponent found! Preparing for battle..."
	matchmaking_progress.text = "✅ MATCH FOUND!"
	
	opponent_info.text = "OPPONENT FOUND\n\n" + opponent_data.get("player_name", "Unknown") + "\nELO: " + str(opponent_data.get("player_elo", 1000)) + "\n\nHero: " + opponent_data.get("hero_name", "Unknown") + "\nAttack: " + str(opponent_data.get("hero_attack", 1)) + " | Health: " + str(opponent_data.get("hero_health", 20))
	
	server_logger.log_system_event("opponent_found", {
		"opponent_id": opponent_data.get("player_id", 0),
		"opponent_name": opponent_data.get("player_name", ""),
		"opponent_elo": opponent_data.get("player_elo", 1000),
		"opponent_hero": opponent_data.get("hero_name", ""),
		"matchmaking_duration": 120.0 - matchmaking_timer.time_left
	})
	
	# Wait a moment to show opponent info, then proceed to battle
	await get_tree().create_timer(3.0).timeout
	
	print("⚔️ Proceeding to battle setup")
	
	# Move to battle setup
	if game_state_manager:
		game_state_manager.change_state(game_state_manager.GameState.BATTLE_SETUP)
	else:
		get_tree().change_scene_to_file("res://battle_scene.tscn")

func _on_matchmaking_timeout():
	"""Handle matchmaking timeout"""
	print("⏰ Matchmaking timed out")
	
	status_label.text = "No opponents found - try again later"
	matchmaking_progress.text = "⏰ SEARCH TIMEOUT"
	opponent_info.text = "No suitable opponents found.\nTry again in a few minutes."
	
	# Stop search animation
	if search_animation_timer:
		search_animation_timer.stop()
	
	server_logger.log_system_event("matchmaking_timeout", {
		"hero_sku": selected_hero.get("sku", ""),
		"search_duration": 120.0
	})
	
	# Wait then return to menu
	await get_tree().create_timer(3.0).timeout
	cancel_matchmaking()

func cancel_matchmaking():
	"""Cancel matchmaking and return to menu"""
	print("❌ Matchmaking cancelled")
	
	# Tell game state manager to cancel
	if game_state_manager:
		game_state_manager.cancel_matchmaking()
	
	server_logger.log_system_event("matchmaking_cancelled", {})
	
	# Return to player menu
	get_tree().change_scene_to_file("res://player_menu.tscn")

func _input(event):
	"""Handle input events"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			cancel_matchmaking()
		elif event.keycode == KEY_F:
			# Force find opponent for testing
			simulate_matchmaking()
