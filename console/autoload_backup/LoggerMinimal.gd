extends Node

# Minimal Logger for testing autoload functionality

func _ready():
	print("📝 Minimal Logger initialized")

func log_info(component: String, message: String, data: Dictionary = {}):
	"""Log info message"""
	print("[INFO] ", component, ": ", message, " ", data)

func log_warning(component: String, message: String, data: Dictionary = {}):
	"""Log warning message"""
	print("[WARNING] ", component, ": ", message, " ", data)

func log_error(component: String, message: String, data: Dictionary = {}):
	"""Log error message"""
	print("[ERROR] ", component, ": ", message, " ", data)

func log_debug(component: String, message: String, data: Dictionary = {}):
	"""Log debug message"""
	print("[DEBUG] ", component, ": ", message, " ", data)
