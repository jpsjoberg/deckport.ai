extends Control

# Minimal test console - just shows "Game Loaded" to verify framebuffer works

@onready var label = $CenterContainer/VBoxContainer/Label

func _ready():
	print("🎮 TEST CONSOLE LOADED - Framebuffer working!")
	
	# Set up the display
	label.text = "🎮 DECKPORT CONSOLE\n\nGAME LOADED SUCCESSFULLY!\n\nFramebuffer Mode Working ✅"
	
	# Log to console
	print("✅ Framebuffer display initialized")
	print("✅ Game rendering active")
	print("✅ Console test successful")
	
	# Keep running
	while true:
		await get_tree().process_frame
		# Simple animation to show it's working
		label.modulate = Color(1, 1, 1, 0.8 + 0.2 * sin(Time.get_time_dict_from_system()["second"]))
