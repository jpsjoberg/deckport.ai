extends Node
# class_name CardDisplayManager  # Commented out to avoid autoload conflict

signal card_animation_started(card_data: Dictionary)
signal card_animation_finished(card_data: Dictionary)
signal ability_video_started(ability_name: String)
signal ability_video_finished(ability_name: String)

# Card display components (will be set by battle scene)
var card_frame_container: Control
var card_info_panel: Control
var card_video_player: VideoStreamPlayer
var card_name_label: Label
var card_stats_label: Label
var card_abilities_label: Label
var card_cost_label: Label

# Animation settings
var card_slide_duration: float = 0.5
var card_display_duration: float = 3.0
var ability_video_duration: float = 2.0

# Current card being displayed
var current_card: Dictionary = {}
var is_displaying_card: bool = false

func _ready():
	print("🎴 Card Display Manager initialized")

func setup_display_components(components: Dictionary):
	"""Setup the UI components for card display"""
	card_frame_container = components.get("frame_container")
	card_info_panel = components.get("info_panel")
	card_video_player = components.get("video_player")
	card_name_label = components.get("name_label")
	card_stats_label = components.get("stats_label")
	card_abilities_label = components.get("abilities_label")
	card_cost_label = components.get("cost_label")
	
	# Initially hide the card display
	if card_frame_container:
		card_frame_container.visible = false
		card_frame_container.modulate.a = 0.0

func display_played_card(card_data: Dictionary, ability_videos: Array = []):
	"""Display a card that was just played with full animation"""
	if is_displaying_card:
		print("⚠️ Card already being displayed, queuing...")
		# TODO: Implement card display queue
		return
	
	current_card = card_data
	is_displaying_card = true
	
	print("🎴 Displaying card: ", card_data.get("name", "Unknown"))
	
	# Update card information
	_update_card_info(card_data)
	
	# Start card animation sequence
	_animate_card_entrance()
	
	# Emit signal
	card_animation_started.emit(card_data)
	
	# Play ability videos if provided
	if not ability_videos.is_empty():
		await _play_ability_videos(ability_videos)
	
	# Hold display for a moment
	await get_tree().create_timer(card_display_duration).timeout
	
	# Animate card exit
	_animate_card_exit()

func _update_card_info(card_data: Dictionary):
	"""Update all card information displays"""
	if not card_name_label or not card_stats_label:
		print("⚠️ Card display components not setup")
		return
	
	# Card name
	var card_name = card_data.get("name", "Unknown Card")
	card_name_label.text = card_name
	
	# Card costs
	var energy_cost = card_data.get("energy_cost", 1)
	var mana_costs = card_data.get("mana_cost", {})
	var cost_text = "⚡ " + str(energy_cost)
	
	if not mana_costs.is_empty():
		cost_text += " | 🔮 "
		var mana_parts = []
		for color in mana_costs:
			mana_parts.append(color + ":" + str(mana_costs[color]))
		cost_text += " ".join(mana_parts)
	
	card_cost_label.text = cost_text
	
	# Card stats (if creature/hero)
	var stats_text = ""
	if card_data.has("attack") or card_data.has("defense") or card_data.has("health"):
		var attack = card_data.get("attack", 0)
		var defense = card_data.get("defense", 0) 
		var health = card_data.get("health", 0)
		
		if attack > 0:
			stats_text += "⚔️ " + str(attack) + " "
		if defense > 0:
			stats_text += "🛡️ " + str(defense) + " "
		if health > 0:
			stats_text += "❤️ " + str(health)
	
	card_stats_label.text = stats_text
	
	# Card abilities
	var abilities = card_data.get("abilities", [])
	var abilities_text = ""
	
	if not abilities.is_empty():
		var ability_catalog = get_node("/root/CardAbilitiesCatalog") as CardAbilitiesCatalog
		var ability_names = []
		
		for ability in abilities:
			var ability_name = ""
			if ability is String:
				ability_name = ability
			elif ability is Dictionary:
				ability_name = ability.get("name", "")
			
			if ability_catalog and ability_catalog.is_valid_ability(ability_name):
				var definition = ability_catalog.get_ability_definition(ability_name)
				ability_names.append(definition.get("name", ability_name))
			else:
				ability_names.append(ability_name)
		
		abilities_text = "🎯 " + " • ".join(ability_names)
	
	card_abilities_label.text = abilities_text

func _animate_card_entrance():
	"""Animate card sliding in from the side"""
	if not card_frame_container:
		return
	
	# Start position (off-screen right)
	var start_pos = card_frame_container.position
	var target_pos = start_pos
	start_pos.x += 400  # Off screen
	
	card_frame_container.position = start_pos
	card_frame_container.visible = true
	card_frame_container.modulate.a = 0.0
	
	# Create tween for smooth animation
	var tween = create_tween()
	tween.set_parallel(true)
	
	# Slide in position
	tween.tween_property(card_frame_container, "position", target_pos, card_slide_duration)
	tween.tween_property(card_frame_container, "modulate:a", 1.0, card_slide_duration * 0.7)
	
	# Add some bounce effect
	tween.tween_property(card_frame_container, "scale", Vector2(1.1, 1.1), card_slide_duration * 0.3)
	tween.tween_property(card_frame_container, "scale", Vector2(1.0, 1.0), card_slide_duration * 0.2)

func _animate_card_exit():
	"""Animate card sliding out"""
	if not card_frame_container:
		is_displaying_card = false
		card_animation_finished.emit(current_card)
		return
	
	var tween = create_tween()
	tween.set_parallel(true)
	
	# Slide out to left
	var exit_pos = card_frame_container.position
	exit_pos.x -= 400
	
	tween.tween_property(card_frame_container, "position", exit_pos, card_slide_duration)
	tween.tween_property(card_frame_container, "modulate:a", 0.0, card_slide_duration)
	
	# Wait for animation to complete
	await tween.finished
	
	# Hide and reset
	card_frame_container.visible = false
	is_displaying_card = false
	
	card_animation_finished.emit(current_card)
	current_card = {}

func _play_ability_videos(ability_videos: Array):
	"""Play video clips for card abilities in the transparent center"""
	if not card_video_player:
		print("⚠️ No video player available for ability videos")
		return
	
	for video_path in ability_videos:
		if video_path == "":
			continue
		
		print("🎬 Playing ability video: ", video_path)
		ability_video_started.emit(video_path)
		
		# Load and play video
		var video_stream = VideoStreamTheora.new()
		var video_file = FileAccess.open("res://assets/videos/" + video_path, FileAccess.READ)
		
		if video_file:
			video_stream.file = "res://assets/videos/" + video_path
			card_video_player.stream = video_stream
			card_video_player.visible = true
			card_video_player.play()
			
			# Wait for video duration
			await get_tree().create_timer(ability_video_duration).timeout
			
			card_video_player.stop()
			card_video_player.visible = false
			
			ability_video_finished.emit(video_path)
		else:
			print("❌ Could not load video: ", video_path)
		
		# Small pause between videos
		await get_tree().create_timer(0.3).timeout

func display_card_preview(card_data: Dictionary, duration: float = 2.0):
	"""Show a quick preview of a card (for scanning feedback)"""
	if is_displaying_card:
		return
	
	print("👁️ Showing card preview: ", card_data.get("name", "Unknown"))
	
	_update_card_info(card_data)
	
	# Quick fade in
	if card_frame_container:
		card_frame_container.visible = true
		card_frame_container.modulate.a = 0.0
		
		var tween = create_tween()
		tween.tween_property(card_frame_container, "modulate:a", 0.8, 0.2)
		
		# Hold for duration
		await get_tree().create_timer(duration).timeout
		
		# Quick fade out
		tween = create_tween()
		tween.tween_property(card_frame_container, "modulate:a", 0.0, 0.2)
		await tween.finished
		
		card_frame_container.visible = false

func get_ability_videos_for_card(card_data: Dictionary) -> Array:
	"""Get all video clips needed for a card's abilities"""
	var video_clips = []
	var abilities = card_data.get("abilities", [])
	var ability_catalog = get_node("/root/CardAbilitiesCatalog") as CardAbilitiesCatalog
	
	if not ability_catalog:
		return video_clips
	
	for ability in abilities:
		var ability_name = ""
		if ability is String:
			ability_name = ability
		elif ability is Dictionary:
			ability_name = ability.get("name", "")
		
		var video_clip = ability_catalog.get_ability_video_clip(ability_name)
		if video_clip != "":
			video_clips.append(video_clip)
	
	return video_clips

func is_card_currently_displaying() -> bool:
	"""Check if a card is currently being displayed"""
	return is_displaying_card

func get_current_card() -> Dictionary:
	"""Get the currently displayed card data"""
	return current_card

# Debug functions
func debug_display_test_card():
	"""Display a test card for debugging"""
	var test_card = {
		"name": "Test Fire Bolt",
		"energy_cost": 2,
		"mana_cost": {"CRIMSON": 1},
		"abilities": ["fire_damage", "burn"],
		"description": "A test card for debugging display"
	}
	
	var ability_videos = get_ability_videos_for_card(test_card)
	display_played_card(test_card, ability_videos)











