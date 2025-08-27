extends Control

# Arena Reveal Scene - Shows arena information before match

var server_logger

func _ready():
	print("🏟️ Arena Reveal scene loaded")
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("arena_reveal_loaded", {})

func show_arena(arena_data: Dictionary):
	"""Display arena information"""
	server_logger.log_system_event("arena_revealed", arena_data)
	print("🏟️ Showing arena: ", arena_data.get("name", "Unknown"))
