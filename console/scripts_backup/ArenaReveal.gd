extends Control

# Arena Reveal Scene
# Shows arena introduction with video, storytelling, and advantages

@onready var arena_video_player = $ArenaVideoPlayer
@onready var arena_info_panel = $ArenaInfoPanel
@onready var arena_name_label = $ArenaInfoPanel/ArenaName
@onready var arena_story_label = $ArenaInfoPanel/ArenaStory
@onready var mana_color_display = $ArenaInfoPanel/ManaColorDisplay

@onready var advantage_panel = $AdvantagePanel
@onready var advantage_label = $AdvantagePanel/AdvantageLabel
@onready var advantage_video = $AdvantagePanel/AdvantageVideo

@onready var objective_panel = $ObjectivePanel
@onready var objective_label = $ObjectivePanel/ObjectiveLabel
@onready var hazard_panel = $HazardPanel
@onready var hazard_label = $HazardPanel/HazardLabel

@onready var countdown_panel = $CountdownPanel
@onready var countdown_label = $CountdownPanel/CountdownLabel

@onready var skip_button = $SkipButton
@onready var ready_button = $ReadyButton

var arena_data: Dictionary = {}
var has_arena_advantage: bool = false
var intro_video_playing: bool = false
var network_client

func _ready():
	Logger.log_info("ArenaReveal", "Arena reveal scene loaded")
	Global.current_scene = "ArenaReveal"
	
	# Get network client from Global
	network_client = Global.get_network_client()
	
	# Get arena data from Global
	arena_data = Global.current_arena
	
	if arena_data.is_empty():
		Logger.log_error("ArenaReveal", "No arena data available")
		return_to_hero_selection()
		return
	
	setup_ui()
	start_arena_reveal_sequence()

func setup_ui():
	"""Initialize arena reveal UI"""
	# Connect button signals
	skip_button.pressed.connect(_on_skip_pressed)
	ready_button.pressed.connect(_on_ready_pressed)
	
	# Hide panels initially
	advantage_panel.visible = false
	objective_panel.visible = false
	hazard_panel.visible = false
	countdown_panel.visible = false
	ready_button.visible = false
	
	# Enable skip button
	skip_button.visible = Global.is_development()  # Only show skip in dev mode

func start_arena_reveal_sequence():
	"""Start the complete arena reveal sequence"""
	Logger.log_info("ArenaReveal", "Starting arena reveal sequence", {"arena": arena_data.get("name")})
	
	# Sequence:
	# 1. Play arena introduction video (30-45 seconds)
	# 2. Show arena information and story
	# 3. Check and display arena advantage
	# 4. Show objective and hazard
	# 5. Countdown to match start
	
	await play_arena_intro_video()
	await show_arena_information()
	await check_arena_advantage()
	await show_arena_mechanics()
	await start_match_countdown()

func play_arena_intro_video():
	"""Play arena introduction video"""
	var arena_name = arena_data.get("name", "").to_lower().replace(" ", "_")
	var video_path = "res://assets/videos/arenas/" + arena_name + "/intro.mp4"
	
	Logger.log_info("ArenaReveal", "Playing arena intro video: " + video_path)
	
	# Check if video exists
	if ResourceLoader.exists(video_path):
		arena_video_player.stream = load(video_path)
	else:
		# Use generic arena video
		arena_video_player.stream = load("res://assets/videos/arenas/generic_arena_intro.mp4")
		Logger.log_warning("ArenaReveal", "Arena video not found, using generic: " + video_path)
	
	intro_video_playing = true
	arena_video_player.play()
	
	# Wait for video to finish or skip
	arena_video_player.finished.connect(_on_intro_video_finished, CONNECT_ONE_SHOT)
	
	# Also wait for skip or video duration
	var video_duration = 45.0  # Default duration
	await get_tree().create_timer(video_duration).timeout
	
	if intro_video_playing:
		_on_intro_video_finished()

func _on_intro_video_finished():
	"""Handle intro video completion"""
	intro_video_playing = false
	Logger.log_info("ArenaReveal", "Arena intro video finished")

func show_arena_information():
	"""Display arena information and story"""
	Logger.log_info("ArenaReveal", "Showing arena information")
	
	# Show arena info panel
	arena_info_panel.visible = true
	
	# Set arena name and story
	arena_name_label.text = arena_data.get("name", "Unknown Arena")
	
	var story_text = arena_data.get("story_text", "")
	var flavor_text = arena_data.get("flavor_text", "")
	
	# Combine story and flavor text
	var full_story = flavor_text + "\n\n" + story_text
	arena_story_label.text = full_story
	
	# Show mana color
	var mana_color = arena_data.get("mana_color", "")
	mana_color_display.text = "Arena Mana: " + mana_color
	mana_color_display.modulate = _get_mana_color(mana_color)
	
	# Animate text appearance
	var tween = create_tween()
	arena_info_panel.modulate.a = 0.0
	tween.tween_property(arena_info_panel, "modulate:a", 1.0, 1.0)
	await tween.finished
	
	# Wait for player to read
	await get_tree().create_timer(3.0).timeout

func check_arena_advantage():
	"""Check and display arena advantage"""
	var arena_color = arena_data.get("mana_color", "")
	var hero_colors = Global.selected_hero.get("colors", [])
	
	has_arena_advantage = arena_color in hero_colors
	
	if has_arena_advantage:
		Logger.log_info("ArenaReveal", "Player has arena advantage", {"arena_color": arena_color})
		await show_arena_advantage()
	else:
		Logger.log_info("ArenaReveal", "No arena advantage", {"arena_color": arena_color, "hero_colors": hero_colors})

func show_arena_advantage():
	"""Display arena advantage with video"""
	advantage_panel.visible = true
	advantage_label.text = "ARENA ADVANTAGE!\n+1 Energy per turn\nFirst " + arena_data.get("mana_color", "") + " card costs 1 less Mana"
	
	# Play advantage video
	var arena_name = arena_data.get("name", "").to_lower().replace(" ", "_")
	var advantage_video_path = "res://assets/videos/arenas/" + arena_name + "/advantage.mp4"
	
	if ResourceLoader.exists(advantage_video_path):
		advantage_video.stream = load(advantage_video_path)
		advantage_video.play()
	
	# Animate advantage panel
	var tween = create_tween()
	advantage_panel.scale = Vector2.ZERO
	tween.tween_property(advantage_panel, "scale", Vector2.ONE, 0.5)
	tween.tween_property(advantage_panel, "modulate", Color.GOLD, 0.3)
	await tween.finished
	
	# Wait for emphasis
	await get_tree().create_timer(2.0).timeout

func show_arena_mechanics():
	"""Display arena objective and hazard"""
	Logger.log_info("ArenaReveal", "Showing arena mechanics")
	
	# Show objective
	var objective = arena_data.get("objective")
	if objective:
		objective_panel.visible = true
		objective_label.text = "🎯 " + objective.get("name", "") + "\n" + objective.get("description", "")
	
	# Show hazard
	var hazard = arena_data.get("hazard")
	if hazard:
		hazard_panel.visible = true
		hazard_label.text = "⚠️ " + hazard.get("name", "") + "\n" + hazard.get("description", "")
	
	# Animate panels
	var tween = create_tween()
	if objective_panel.visible:
		objective_panel.modulate.a = 0.0
		tween.parallel().tween_property(objective_panel, "modulate:a", 1.0, 0.8)
	
	if hazard_panel.visible:
		hazard_panel.modulate.a = 0.0
		tween.parallel().tween_property(hazard_panel, "modulate:a", 1.0, 0.8)
	
	await tween.finished
	await get_tree().create_timer(2.0).timeout

func start_match_countdown():
	"""Start countdown to match beginning"""
	Logger.log_info("ArenaReveal", "Starting match countdown")
	
	countdown_panel.visible = true
	ready_button.visible = true
	
	# Countdown from 10 to 1
	for i in range(10, 0, -1):
		countdown_label.text = "Match starts in " + str(i)
		
		# Animate countdown number
		var tween = create_tween()
		countdown_label.scale = Vector2(1.5, 1.5)
		tween.tween_property(countdown_label, "scale", Vector2.ONE, 0.5)
		
		await get_tree().create_timer(1.0).timeout
	
	# Transition to game board
	transition_to_game_board()

func transition_to_game_board():
	"""Transition to the main game board"""
	Logger.log_info("ArenaReveal", "Transitioning to game board")
	
	countdown_label.text = "FIGHT!"
	
	# Final dramatic pause
	await get_tree().create_timer(1.0).timeout
	
	# Fade out and change scene
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.5)
	await tween.finished
	
	get_tree().change_scene_to_file("res://scenes/GameBoard.tscn")

func _on_skip_pressed():
	"""Handle skip button press (development only)"""
	if Global.is_development():
		Logger.log_info("ArenaReveal", "Arena reveal skipped (dev mode)")
		transition_to_game_board()

func _on_ready_pressed():
	"""Handle ready button press"""
	Logger.log_info("ArenaReveal", "Player ready for match")
	
	# Send ready signal to server
	if network_client:
		var message = {
			"type": "match.ready",
			"timestamp": Time.get_datetime_string_from_system()
		}
		network_client.send_message(message)
	
	# Disable button and show waiting
	ready_button.disabled = true
	countdown_label.text = "Waiting for opponent..."

func return_to_hero_selection():
	"""Return to hero selection if there's an error"""
	Logger.log_warning("ArenaReveal", "Returning to hero selection")
	get_tree().change_scene_to_file("res://scenes/HeroSelection.tscn")

func _get_mana_color(color: String) -> Color:
	"""Get visual color for mana type"""
	match color:
		"RADIANT":
			return Color.GOLD
		"AZURE":
			return Color.CYAN
		"VERDANT":
			return Color.GREEN
		"OBSIDIAN":
			return Color.PURPLE
		"CRIMSON":
			return Color.RED
		"AETHER":
			return Color.WHITE
		_:
			return Color.GRAY

func _exit_tree():
	"""Cleanup when leaving arena reveal"""
	Logger.log_info("ArenaReveal", "Arena reveal scene exiting")
	
	# Stop videos
	if arena_video_player.is_playing():
		arena_video_player.stop()
	if advantage_video.is_playing():
		advantage_video.stop()
