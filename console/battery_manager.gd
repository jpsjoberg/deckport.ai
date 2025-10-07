extends Node

##
## Battery Manager - Console Battery Monitoring System
##
## This class handles battery monitoring for portable Deckport consoles.
## It reads battery status from the system and provides real-time information
## to the game UI, including charging status, remaining time, and low battery warnings.
##
## Features:
## - Real-time battery percentage monitoring
## - Charging status detection
## - Low battery warnings and critical alerts
## - Power consumption tracking
## - AC adapter detection
## - Battery health monitoring
##
## Usage:
## - Add as autoload singleton: BatteryManager
## - Connect to signals for battery events
## - Use get_battery_status() for current info
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2024-12-30
##

# Signals for battery events
signal battery_low_warning(percent: int)
signal battery_critical_alert(percent: int)
signal battery_charging_changed(is_charging: bool)
signal battery_status_updated(status: Dictionary)

# Battery status constants
enum BatteryStatus {
	UNKNOWN,
	CHARGING,
	DISCHARGING,
	NOT_CHARGING,
	FULL,
	AC_POWER
}

# Current battery state
var current_battery_percent: int = 100
var current_battery_status: BatteryStatus = BatteryStatus.AC_POWER
var is_battery_present: bool = false
var is_ac_connected: bool = true
var is_charging: bool = false
var time_remaining_minutes: int = 0
var power_consumption_watts: float = 0.0
var last_update_time: String = ""

# Warning thresholds
var low_battery_threshold: int = 20
var critical_battery_threshold: int = 10

# Monitoring settings
var battery_file_path: String = "/tmp/deckport_battery_status.json"
var update_interval: float = 5.0  # Check every 5 seconds
var last_warning_time: int = 0

func _ready():
	print("🔋 Battery Manager initialized")
	
	# Start battery monitoring
	_start_battery_monitoring()
	
	# Log system startup
	if has_node("/root/ServerLogger"):
		get_node("/root/ServerLogger").log_system_event("battery_manager_start", {
			"monitoring_enabled": true,
			"update_interval": update_interval
		})

func _start_battery_monitoring():
	"""Start periodic battery monitoring"""
	var timer = Timer.new()
	timer.wait_time = update_interval
	timer.timeout.connect(_update_battery_status)
	timer.autostart = true
	add_child(timer)
	
	# Initial battery check
	_update_battery_status()

func _update_battery_status():
	"""Read battery status from system file"""
	if not FileAccess.file_exists(battery_file_path):
		# No battery file - assume AC power
		_set_ac_power_mode()
		return
	
	var file = FileAccess.open(battery_file_path, FileAccess.READ)
	if not file:
		print("⚠️ Cannot read battery status file")
		return
	
	var json_text = file.get_as_text()
	file.close()
	
	var json = JSON.new()
	var parse_result = json.parse(json_text)
	
	if parse_result != OK:
		print("❌ Failed to parse battery status JSON")
		return
	
	var battery_data = json.get_data()
	_process_battery_data(battery_data)

func _process_battery_data(data: Dictionary):
	"""Process battery data and emit appropriate signals"""
	var old_percent = current_battery_percent
	var old_charging = is_charging
	var old_status = current_battery_status
	
	# Update current state
	current_battery_percent = data.get("battery_percent", 100)
	is_battery_present = data.get("battery_present", false)
	is_ac_connected = data.get("ac_connected", true)
	is_charging = data.get("is_charging", false)
	time_remaining_minutes = data.get("time_remaining_minutes", 0)
	power_consumption_watts = data.get("power_consumption_watts", 0.0)
	last_update_time = data.get("timestamp", "")
	
	# Parse battery status
	var status_string = data.get("battery_status", "AC_Power")
	match status_string:
		"Charging":
			current_battery_status = BatteryStatus.CHARGING
		"Discharging":
			current_battery_status = BatteryStatus.DISCHARGING
		"Not charging":
			current_battery_status = BatteryStatus.NOT_CHARGING
		"Full":
			current_battery_status = BatteryStatus.FULL
		"AC_Power":
			current_battery_status = BatteryStatus.AC_POWER
		_:
			current_battery_status = BatteryStatus.UNKNOWN
	
	# Emit status update signal
	battery_status_updated.emit({
		"percent": current_battery_percent,
		"status": current_battery_status,
		"is_charging": is_charging,
		"is_battery_present": is_battery_present,
		"is_ac_connected": is_ac_connected,
		"time_remaining": time_remaining_minutes,
		"power_consumption": power_consumption_watts,
		"timestamp": last_update_time
	})
	
	# Check for charging state changes
	if old_charging != is_charging:
		battery_charging_changed.emit(is_charging)
		print("🔋 Battery charging status changed: ", "Charging" if is_charging else "Discharging")
	
	# Check for low battery warnings
	if is_battery_present and not is_charging:
		var current_time = Time.get_unix_time_from_system()
		
		# Critical battery alert (every 60 seconds)
		if current_battery_percent <= critical_battery_threshold and current_time - last_warning_time > 60:
			battery_critical_alert.emit(current_battery_percent)
			last_warning_time = current_time
			print("🚨 CRITICAL BATTERY ALERT: ", current_battery_percent, "%")
			
			# Log critical battery event
			if has_node("/root/ServerLogger"):
				get_node("/root/ServerLogger").log_system_event("battery_critical", {
					"battery_percent": current_battery_percent,
					"time_remaining": time_remaining_minutes
				})
		
		# Low battery warning (every 5 minutes)
		elif current_battery_percent <= low_battery_threshold and current_time - last_warning_time > 300:
			battery_low_warning.emit(current_battery_percent)
			last_warning_time = current_time
			print("⚠️ Low battery warning: ", current_battery_percent, "%")
			
			# Log low battery event
			if has_node("/root/ServerLogger"):
				get_node("/root/ServerLogger").log_system_event("battery_low", {
					"battery_percent": current_battery_percent,
					"time_remaining": time_remaining_minutes
				})

func _set_ac_power_mode():
	"""Set console to AC power mode when no battery detected"""
	current_battery_percent = 100
	current_battery_status = BatteryStatus.AC_POWER
	is_battery_present = false
	is_ac_connected = true
	is_charging = false

func get_battery_status() -> Dictionary:
	"""Get current battery status for UI display"""
	return {
		"percent": current_battery_percent,
		"status": current_battery_status,
		"status_text": _get_status_text(),
		"is_charging": is_charging,
		"is_battery_present": is_battery_present,
		"is_ac_connected": is_ac_connected,
		"is_low_battery": current_battery_percent <= low_battery_threshold and is_battery_present,
		"is_critical_battery": current_battery_percent <= critical_battery_threshold and is_battery_present,
		"time_remaining_minutes": time_remaining_minutes,
		"time_remaining_text": _get_time_remaining_text(),
		"power_consumption_watts": power_consumption_watts,
		"battery_color": _get_battery_color(),
		"battery_icon": _get_battery_icon()
	}

func _get_status_text() -> String:
	"""Get human-readable battery status text"""
	if not is_battery_present:
		return "AC Power"
	
	match current_battery_status:
		BatteryStatus.CHARGING:
			return "Charging"
		BatteryStatus.DISCHARGING:
			return "On Battery"
		BatteryStatus.NOT_CHARGING:
			return "Plugged In"
		BatteryStatus.FULL:
			return "Full"
		BatteryStatus.AC_POWER:
			return "AC Power"
		_:
			return "Unknown"

func _get_time_remaining_text() -> String:
	"""Get formatted time remaining text"""
	if time_remaining_minutes <= 0:
		return ""
	
	var hours = time_remaining_minutes / 60
	var minutes = time_remaining_minutes % 60
	
	if hours > 0:
		return "%d:%02d remaining" % [hours, minutes]
	else:
		return "%d min remaining" % minutes

func _get_battery_color() -> Color:
	"""Get color for battery indicator based on status"""
	if not is_battery_present:
		return Color.CYAN  # AC power
	
	if is_charging:
		return Color.GREEN
	elif current_battery_percent <= critical_battery_threshold:
		return Color.RED
	elif current_battery_percent <= low_battery_threshold:
		return Color.YELLOW
	else:
		return Color.WHITE

func _get_battery_icon() -> String:
	"""Get appropriate battery icon based on status"""
	if not is_battery_present:
		return "🔌"  # AC power
	
	if is_charging:
		return "🔋⚡"  # Charging
	elif current_battery_percent <= critical_battery_threshold:
		return "🪫"  # Critical
	elif current_battery_percent <= low_battery_threshold:
		return "🔋⚠️"  # Low
	else:
		return "🔋"  # Normal

func get_battery_percent() -> int:
	"""Quick access to battery percentage"""
	return current_battery_percent

func is_low_battery() -> bool:
	"""Check if battery is low"""
	return is_battery_present and current_battery_percent <= low_battery_threshold

func is_critical_battery() -> bool:
	"""Check if battery is critically low"""
	return is_battery_present and current_battery_percent <= critical_battery_threshold

func get_time_remaining() -> int:
	"""Get estimated time remaining in minutes"""
	return time_remaining_minutes

func force_update():
	"""Force an immediate battery status update"""
	_update_battery_status()

# Utility function to format battery info for UI
func get_battery_display_text() -> String:
	"""Get formatted text for battery display in UI"""
	if not is_battery_present:
		return "AC Power"
	
	var status_text = _get_status_text()
	var time_text = _get_time_remaining_text()
	
	if time_text != "":
		return "%d%% - %s (%s)" % [current_battery_percent, status_text, time_text]
	else:
		return "%d%% - %s" % [current_battery_percent, status_text]
