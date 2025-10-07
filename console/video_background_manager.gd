extends Node
# class_name VideoBackgroundManager  # Commented out to avoid autoload conflict

signal video_loaded(video_path: String)
signal video_failed(video_path: String, error: String)
signal video_loop_completed(video_path: String)

# Video player component (will be set by each scene)
var video_player: VideoStreamPlayer
var current_video_path: String = ""
var is_looping: bool = true
var default_volume: float = 0.3

# Video library for different scenes/contexts
var video_library = {
	# Main menu and UI scenes
	"main_menu": "backgrounds/main_menu_ambient.mp4",
	"matchmaking": "backgrounds/matchmaking_queue.mp4",
	"qr_login": "backgrounds/qr_login_ambient.mp4",
	
	# Arena backgrounds (loaded from ArenaManager)
	"arena_crimson_forge": "backgrounds/crimson_forge_ambient.mp4",
	"arena_azure_depths": "backgrounds/azure_depths_ambient.mp4", 
	"arena_verdant_grove": "backgrounds/verdant_grove_ambient.mp4",
	
	# Battle phases
	"battle_preparation": "backgrounds/battle_prep.mp4",
	"battle_active": "backgrounds/battle_active.mp4",
	"victory": "backgrounds/victory_celebration.mp4",
	"defeat": "backgrounds/defeat_aftermath.mp4",
	
	# Special events
	"card_scanning": "backgrounds/card_scan_effect.mp4",
	"hero_summoning": "backgrounds/hero_summon.mp4",
	"ultimate_ability": "backgrounds/ultimate_power.mp4",
	
	# Default fallbacks
	"default": "backgrounds/default_ambient.mp4",
	"loading": "backgrounds/loading_spiral.mp4"
}

func _ready():
	print("🎬 Video Background Manager initialized")

func setup_video_player(player: VideoStreamPlayer):
	"""Setup the video player component for this scene"""
	video_player = player
	if video_player:
		video_player.volume_db = linear_to_db(default_volume)
		video_player.finished.connect(_on_video_finished)
		print("🎬 Video player setup complete")

func play_background_video(video_key: String, loop: bool = true):
	"""Play a background video by key"""
	if not video_player:
		print("❌ No video player setup")
		return false
	
	var video_path = video_library.get(video_key, video_library.get("default", ""))
	if video_path == "":
		print("❌ No video found for key: ", video_key)
		return false
	
	return play_video_file(video_path, loop)

func play_video_file(video_path: String, loop: bool = true):
	"""Play a specific video file"""
	if not video_player:
		print("❌ No video player setup")
		return false
	
	print("🎬 Loading video: ", video_path)
	
	# Check if file exists
	var full_path = "res://assets/videos/" + video_path
	if not FileAccess.file_exists(full_path):
		print("❌ Video file not found: ", full_path)
		# Try to play default video instead
		var default_path = "res://assets/videos/" + video_library.get("default", "")
		if FileAccess.file_exists(default_path):
			video_path = video_library.get("default", "")
			full_path = default_path
		else:
			video_failed.emit(video_path, "File not found")
			return false
	
	# Load video stream
	var video_stream = VideoStreamTheora.new()
	video_stream.file = full_path
	
	# Setup player
	video_player.stream = video_stream
	current_video_path = video_path
	is_looping = loop
	
	# Start playback
	video_player.play()
	video_loaded.emit(video_path)
	
	print("✅ Video playing: ", video_path, " (loop: ", loop, ")")
	return true

func play_arena_background(arena_data: Dictionary):
	"""Play background video for a specific arena"""
	var arena_video = arena_data.get("background_video", "")
	if arena_video != "":
		return play_video_file(arena_video, true)
	else:
		# Fallback to arena type
		var arena_name = arena_data.get("name", "").to_lower().replace(" ", "_")
		var arena_key = "arena_" + arena_name
		return play_background_video(arena_key, true)

func stop_video():
	"""Stop current video playback"""
	if video_player and video_player.is_playing():
		video_player.stop()
		current_video_path = ""
		print("⏹️ Video stopped")

func pause_video():
	"""Pause current video"""
	if video_player and video_player.is_playing():
		video_player.paused = true
		print("⏸️ Video paused")

func resume_video():
	"""Resume paused video"""
	if video_player:
		video_player.paused = false
		print("▶️ Video resumed")

func set_video_volume(volume: float):
	"""Set video volume (0.0 to 1.0)"""
	if video_player:
		video_player.volume_db = linear_to_db(clamp(volume, 0.0, 1.0))
		default_volume = volume

func fade_video_volume(target_volume: float, duration: float = 1.0):
	"""Fade video volume over time"""
	if not video_player:
		return
	
	var tween = create_tween()
	var current_linear = db_to_linear(video_player.volume_db)
	var target_db = linear_to_db(clamp(target_volume, 0.0, 1.0))
	
	tween.tween_method(_set_volume_db, video_player.volume_db, target_db, duration)
	await tween.finished
	
	default_volume = target_volume

func _set_volume_db(volume_db: float):
	"""Helper for volume fading"""
	if video_player:
		video_player.volume_db = volume_db

func crossfade_to_video(new_video_key: String, fade_duration: float = 1.0):
	"""Crossfade from current video to new video"""
	# Fade out current video
	if video_player and video_player.is_playing():
		fade_video_volume(0.0, fade_duration * 0.5)
		await get_tree().create_timer(fade_duration * 0.5).timeout
	
	# Switch to new video
	play_background_video(new_video_key)
	
	# Fade in new video
	if video_player:
		video_player.volume_db = linear_to_db(0.0)
		fade_video_volume(default_volume, fade_duration * 0.5)

func _on_video_finished():
	"""Handle video finished event"""
	if is_looping and current_video_path != "":
		# Restart the video for looping
		video_player.play()
		video_loop_completed.emit(current_video_path)
	else:
		current_video_path = ""

func get_current_video() -> String:
	"""Get currently playing video path"""
	return current_video_path

func is_video_playing() -> bool:
	"""Check if video is currently playing"""
	return video_player != null and video_player.is_playing()

func add_custom_video(key: String, path: String):
	"""Add a custom video to the library"""
	video_library[key] = path
	print("🎬 Added custom video: ", key, " -> ", path)

func get_video_library() -> Dictionary:
	"""Get the complete video library"""
	return video_library.duplicate()

# Scene-specific helper functions
func setup_main_menu_background():
	"""Setup background for main menu"""
	play_background_video("main_menu")

func setup_matchmaking_background():
	"""Setup background for matchmaking scene"""
	play_background_video("matchmaking")

func setup_qr_login_background():
	"""Setup background for QR login scene"""
	play_background_video("qr_login")

func setup_battle_background(arena_data: Dictionary):
	"""Setup background for battle scene"""
	play_arena_background(arena_data)

func trigger_special_video(event_type: String, duration: float = 3.0):
	"""Play a special video for events, then return to background"""
	var original_video = current_video_path
	
	# Play special video
	if play_background_video(event_type, false):
		# Wait for duration or video to finish
		await get_tree().create_timer(duration).timeout
		
		# Return to original video
		if original_video != "":
			play_video_file(original_video, true)

# Debug functions
func debug_list_videos():
	"""Debug: Print all available videos"""
	print("🎬 Available videos:")
	for key in video_library:
		var path = video_library[key]
		var exists = FileAccess.file_exists("res://assets/videos/" + path)
		print("  ", key, " -> ", path, " (exists: ", exists, ")")

func debug_test_video(video_key: String):
	"""Debug: Test playing a specific video"""
	print("🎬 Testing video: ", video_key)
	play_background_video(video_key)











