extends Control

##
## Battery Indicator UI Component
##
## Displays battery status in the console UI with visual indicators,
## charging animations, and low battery warnings.
##
## Features:
## - Real-time battery percentage display
## - Charging animation
## - Color-coded status (green/yellow/red)
## - Low battery warnings
## - Time remaining display
## - AC power indicator
##

@onready var battery_icon: Label = $BatteryIcon
@onready var battery_percent: Label = $BatteryPercent
@onready var battery_status: Label = $BatteryStatus
@onready var time_remaining: Label = $TimeRemaining
@onready var warning_panel: Panel = $WarningPanel
@onready var warning_label: Label = $WarningPanel/WarningLabel
@onready var charging_animation: AnimationPlayer = $ChargingAnimation

# Battery state
var current_status: Dictionary = {}
var is_warning_visible: bool = false

func _ready():
	print("🔋 Battery Indicator UI initialized")
	
	# Connect to battery manager signals
	if BatteryManager:
		var battery_manager = get_node("/root/BatteryManager")
		if battery_manager:
			battery_manager.battery_status_updated.connect(_on_battery_status_updated)
			battery_manager.battery_low_warning.connect(_on_battery_low_warning)
			battery_manager.battery_critical_alert.connect(_on_battery_critical_alert)
			battery_manager.battery_charging_changed.connect(_on_charging_changed)
		
		# Get initial status
		if battery_manager and battery_manager.has_method("get_battery_status"):
			_update_display(battery_manager.get_battery_status())
		else:
			_update_display({"level": 100, "charging": false})  # Fallback for testing
	
	# Hide warning panel initially
	if warning_panel:
		warning_panel.visible = false

func _on_battery_status_updated(status: Dictionary):
	"""Update display when battery status changes"""
	current_status = status
	_update_display(status)

func _update_display(status: Dictionary):
	"""Update all UI elements with current battery status"""
	if not status:
		return
	
	# Update battery icon
	if battery_icon:
		battery_icon.text = status.get("battery_icon", "🔋")
		battery_icon.modulate = status.get("battery_color", Color.WHITE)
	
	# Update battery percentage
	if battery_percent:
		battery_percent.text = "%d%%" % status.get("percent", 100)
		battery_percent.modulate = status.get("battery_color", Color.WHITE)
	
	# Update status text
	if battery_status:
		battery_status.text = status.get("status_text", "AC Power")
		battery_status.modulate = status.get("battery_color", Color.WHITE)
	
	# Update time remaining
	if time_remaining:
		var time_text = status.get("time_remaining_text", "")
		time_remaining.text = time_text
		time_remaining.visible = time_text != ""

func _on_charging_changed(charging: bool):
	"""Handle charging status changes"""
	if charging and charging_animation:
		# Start charging animation
		charging_animation.play("charging_pulse")
	else:
		# Stop charging animation
		if charging_animation:
			charging_animation.stop()

func _on_battery_low_warning(percent: int):
	"""Show low battery warning"""
	_show_warning("Low Battery", "Battery at %d%%. Please charge soon." % percent, Color.YELLOW)

func _on_battery_critical_alert(percent: int):
	"""Show critical battery alert"""
	_show_warning("CRITICAL BATTERY", "Battery at %d%%. Console will shut down soon!" % percent, Color.RED)

func _show_warning(title: String, message: String, color: Color):
	"""Show battery warning popup"""
	if not warning_panel or not warning_label:
		return
	
	warning_label.text = title + "\n" + message
	warning_panel.modulate = color
	warning_panel.visible = true
	is_warning_visible = true
	
	# Auto-hide warning after 5 seconds
	await get_tree().create_timer(5.0).timeout
	_hide_warning()

func _hide_warning():
	"""Hide battery warning popup"""
	if warning_panel:
		warning_panel.visible = false
	is_warning_visible = false

func get_battery_info_for_display() -> String:
	"""Get formatted battery info for display"""
	if BatteryManager:
		var battery_manager = get_node("/root/BatteryManager")
		if battery_manager and battery_manager.has_method("get_battery_display_text"):
			return battery_manager.get_battery_display_text()
		else:
			return "100% Battery"  # Fallback for testing
	return "Battery: Unknown"

# Public methods for other UI components
func is_battery_low() -> bool:
	"""Check if battery is currently low"""
	return current_status.get("is_low_battery", false)

func is_battery_critical() -> bool:
	"""Check if battery is critically low"""
	return current_status.get("is_critical_battery", false)

func should_show_battery_warning() -> bool:
	"""Check if battery warning should be shown"""
	return is_battery_low() and not is_warning_visible

func get_battery_percentage() -> int:
	"""Get current battery percentage"""
	return current_status.get("percent", 100)

func is_on_ac_power() -> bool:
	"""Check if console is on AC power"""
	return current_status.get("ac_connected", true) or not current_status.get("battery_present", false)

# Scene file structure for this component:
# BatteryIndicator (Control)
# ├── BatteryIcon (Label)
# ├── BatteryPercent (Label) 
# ├── BatteryStatus (Label)
# ├── TimeRemaining (Label)
# ├── ChargingAnimation (AnimationPlayer)
# └── WarningPanel (Panel)
#     └── WarningLabel (Label)
