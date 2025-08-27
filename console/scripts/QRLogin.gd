extends Control

# QR Login Scene - Player authentication via QR code

var server_logger

func _ready():
	print("📱 QR Login scene loaded")
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_system_event("qr_login_loaded", {})

func start_qr_login():
	"""Start QR login process"""
	server_logger.log_system_event("qr_login_started", {})
	print("📱 Starting QR login...")
