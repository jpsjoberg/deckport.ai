extends Node

# Console Logging System
# Handles structured logging for debugging and analytics

enum LogLevel {
	DEBUG,
	INFO,
	WARNING,
	ERROR,
	CRITICAL
}

var log_file: FileAccess
var log_buffer: Array = []
var max_buffer_size: int = 1000
var current_log_level: LogLevel = LogLevel.INFO

func _ready():
	print("📝 Logger initialized")
	open_log_file()
	log_info("Logger", "Console logging system started")

func open_log_file():
	"""Open log file for writing"""
	var log_dir = "user://logs/"
	if not DirAccess.dir_exists_absolute(log_dir):
		DirAccess.open("user://").make_dir("logs")
	
	var timestamp = Time.get_datetime_string_from_system().replace(":", "-").replace(" ", "_")
	var log_filename = "user://logs/console_" + timestamp + ".log"
	
	log_file = FileAccess.open(log_filename, FileAccess.WRITE)
	if log_file == null:
		print("❌ Failed to open log file: ", log_filename)
	else:
		print("📝 Log file opened: ", log_filename)

func _exit_tree():
	"""Close log file when exiting"""
	if log_file:
		flush_logs()
		log_file.close()

func log_debug(source: String, message: String, data: Dictionary = {}):
	"""Log debug message"""
	_log(LogLevel.DEBUG, source, message, data)

func log_info(source: String, message: String, data: Dictionary = {}):
	"""Log info message"""
	_log(LogLevel.INFO, source, message, data)

func log_warning(source: String, message: String, data: Dictionary = {}):
	"""Log warning message"""
	_log(LogLevel.WARNING, source, message, data)

func log_error(source: String, message: String, data: Dictionary = {}):
	"""Log error message"""
	_log(LogLevel.ERROR, source, message, data)

func log_critical(source: String, message: String, data: Dictionary = {}):
	"""Log critical message"""
	_log(LogLevel.CRITICAL, source, message, data)

func _log(level: LogLevel, source: String, message: String, data: Dictionary):
	"""Internal logging function"""
	if level < current_log_level:
		return
	
	var log_entry = {
		"timestamp": Time.get_datetime_string_from_system(),
		"level": _get_level_string(level),
		"source": source,
		"message": message,
		"device_uid": Global.device_uid,
		"scene": Global.current_scene,
		"data": data
	}
	
	# Add to buffer
	log_buffer.append(log_entry)
	
	# Console output
	var console_message = "[%s] %s: %s" % [_get_level_string(level), source, message]
	print(console_message)
	
	# Write to file
	if log_file:
		log_file.store_line(JSON.stringify(log_entry))
		log_file.flush()
	
	# Trim buffer if too large
	if log_buffer.size() > max_buffer_size:
		log_buffer = log_buffer.slice(int(max_buffer_size / 2))

func _get_level_string(level: LogLevel) -> String:
	"""Convert log level to string"""
	match level:
		LogLevel.DEBUG:
			return "DEBUG"
		LogLevel.INFO:
			return "INFO"
		LogLevel.WARNING:
			return "WARN"
		LogLevel.ERROR:
			return "ERROR"
		LogLevel.CRITICAL:
			return "CRIT"
		_:
			return "UNKNOWN"

func flush_logs():
	"""Flush log buffer to file"""
	if log_file:
		log_file.flush()

func get_recent_logs(count: int = 50) -> Array:
	"""Get recent log entries"""
	var start_index = max(0, log_buffer.size() - count)
	return log_buffer.slice(start_index)

func clear_logs():
	"""Clear log buffer"""
	log_buffer.clear()
	log_info("Logger", "Log buffer cleared")

func set_log_level(level: LogLevel):
	"""Set minimum log level"""
	current_log_level = level
	log_info("Logger", "Log level set to: " + _get_level_string(level))

func export_logs() -> String:
	"""Export all logs as JSON string"""
	return JSON.stringify(log_buffer)

# Convenience functions for common logging patterns
func log_network_request(url: String, method: String, status: int = 0):
	"""Log network request"""
	log_info("Network", "Request: %s %s" % [method, url], {"status": status})

func log_nfc_scan(card_uid: String, success: bool):
	"""Log NFC card scan"""
	var message = "NFC scan successful" if success else "NFC scan failed"
	log_info("NFC", message, {"card_uid": card_uid, "success": success})

func log_game_event(event: String, data: Dictionary = {}):
	"""Log game event"""
	log_info("Game", "Event: " + event, data)

func log_system_error(component: String, error: String, details: Dictionary = {}):
	"""Log system error"""
	log_error("System", "%s error: %s" % [component, error], details)
