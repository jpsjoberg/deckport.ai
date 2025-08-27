extends Control

# Bootloader Scene - System initialization

var server_logger

func _ready():
	print("🚀 Bootloader scene loaded")
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("bootloader_loaded", {})

func start_boot_sequence():
	"""Start the boot sequence"""
	server_logger.log_system_event("boot_sequence_started", {})
	print("🚀 Starting boot sequence...")
