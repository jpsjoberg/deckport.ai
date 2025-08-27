extends Control

# Hero Selection Scene - Player chooses their hero

var server_logger
var selected_hero = null

func _ready():
	print("🦸 Hero Selection scene loaded")
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("hero_selection_loaded", {})

func select_hero(hero_id: String):
	"""Select a hero"""
	selected_hero = hero_id
	server_logger.log_system_event("hero_selected", {"hero_id": hero_id})
	print("🦸 Hero selected: ", hero_id)
