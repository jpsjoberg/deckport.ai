extends Node

# Turn Timer Manager - Handles turn timing and card type timers
# Manages the 60-second turn timer and 10-second card decision windows

signal turn_timer_updated(time_left: float, state: TimerState)
signal turn_timer_expired()
signal card_timer_started(card_data: Dictionary, time_left: float)
signal card_timer_updated(card_data: Dictionary, time_left: float)
signal card_timer_expired(card_data: Dictionary)

enum TimerState {
	NORMAL,    # 30-60 seconds (green)
	WARNING,   # 15-30 seconds (yellow)
	URGENT,    # 5-15 seconds (orange)
	CRITICAL   # 0-5 seconds (red)
}

# Turn timer settings
const TURN_TIME_TOTAL: float = 60.0
const WARNING_THRESHOLD: float = 30.0
const URGENT_THRESHOLD: float = 15.0
const CRITICAL_THRESHOLD: float = 5.0

# Card timer settings
const CARD_DECISION_TIME: float = 10.0
const CARD_VALIDATION_TIME: float = 3.0

# Timer state
var turn_timer: Timer
var turn_time_left: float = 0.0
var current_timer_state: TimerState = TimerState.NORMAL
var is_my_turn: bool = false

# Card timers (multiple cards can be scanned)
var card_timers: Dictionary = {}  # card_id -> Timer
var pending_cards: Dictionary = {}  # card_id -> card_data

var server_logger

func _ready():
	print("⏰ Turn Timer Manager initialized")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Setup turn timer
	setup_turn_timer()

func setup_turn_timer():
	"""Setup the main turn timer"""
	turn_timer = Timer.new()
	add_child(turn_timer)
	turn_timer.wait_time = 0.1  # Update every 100ms for smooth countdown
	turn_timer.timeout.connect(_update_turn_timer)
	
	print("⏰ Turn timer configured")

# === TURN TIMER MANAGEMENT ===

func start_turn():
	"""Start a new turn with full timer"""
	print("🔄 Starting new turn")
	
	turn_time_left = TURN_TIME_TOTAL
	current_timer_state = TimerState.NORMAL
	is_my_turn = true
	
	# Start the timer
	turn_timer.start()
	
	# Clear any pending card timers
	clear_all_card_timers()
	
	server_logger.log_system_event("turn_started", {
		"turn_time": TURN_TIME_TOTAL,
		"timestamp": Time.get_unix_time_from_system()
	})
	
	# Emit initial timer update
	turn_timer_updated.emit(turn_time_left, current_timer_state)

func end_turn():
	"""End the current turn"""
	print("⏹️ Ending turn")
	
	is_my_turn = false
	turn_timer.stop()
	
	# Clear all pending card timers
	clear_all_card_timers()
	
	server_logger.log_system_event("turn_ended", {
		"time_remaining": turn_time_left,
		"manual_end": true
	})

func _update_turn_timer():
	"""Update the turn timer every tick"""
	if not is_my_turn:
		return
	
	turn_time_left -= 0.1
	
	# Check for state changes
	var new_state = get_timer_state(turn_time_left)
	if new_state != current_timer_state:
		current_timer_state = new_state
		print("⏰ Timer state changed to: ", TimerState.keys()[current_timer_state])
		
		# Log state changes
		server_logger.log_system_event("turn_timer_state_change", {
			"new_state": TimerState.keys()[current_timer_state],
			"time_left": turn_time_left
		})
	
	# Emit timer update
	turn_timer_updated.emit(turn_time_left, current_timer_state)
	
	# Check for timer expiration
	if turn_time_left <= 0:
		turn_time_left = 0
		turn_timer.stop()
		
		print("⏰ Turn timer expired!")
		server_logger.log_system_event("turn_timer_expired", {})
		
		turn_timer_expired.emit()

func get_timer_state(time_left: float) -> TimerState:
	"""Get the timer state based on time remaining"""
	if time_left > WARNING_THRESHOLD:
		return TimerState.NORMAL
	elif time_left > URGENT_THRESHOLD:
		return TimerState.WARNING
	elif time_left > CRITICAL_THRESHOLD:
		return TimerState.URGENT
	else:
		return TimerState.CRITICAL

func get_turn_time_left() -> float:
	"""Get remaining turn time"""
	return turn_time_left

func get_timer_state_color() -> Color:
	"""Get color for current timer state"""
	match current_timer_state:
		TimerState.NORMAL:
			return Color.GREEN
		TimerState.WARNING:
			return Color.YELLOW
		TimerState.URGENT:
			return Color.ORANGE
		TimerState.CRITICAL:
			return Color.RED
		_:
			return Color.WHITE

func get_timer_state_text() -> String:
	"""Get descriptive text for timer state"""
	match current_timer_state:
		TimerState.NORMAL:
			return "Take your time"
		TimerState.WARNING:
			return "Time running low"
		TimerState.URGENT:
			return "Hurry up!"
		TimerState.CRITICAL:
			return "Turn ending soon!"
		_:
			return "Unknown"

# === CARD TYPE TIMER MANAGEMENT ===

func start_card_timer(card_data: Dictionary):
	"""Start a timer for a scanned card"""
	var card_id = card_data.get("sku", "") + "_" + str(Time.get_unix_time_from_system())
	
	print("🃏 Starting card timer for: ", card_data.get("name", "Unknown"))
	
	# Create timer for this card
	var card_timer = Timer.new()
	add_child(card_timer)
	card_timer.wait_time = 0.1  # Update every 100ms
	card_timer.timeout.connect(_update_card_timer.bind(card_id))
	
	# Store timer and card data
	card_timers[card_id] = {
		"timer": card_timer,
		"time_left": CARD_DECISION_TIME,
		"card_data": card_data,
		"is_validating": true  # First 3 seconds are validation
	}
	
	pending_cards[card_id] = card_data
	
	# Start the timer
	card_timer.start()
	
	server_logger.log_system_event("card_timer_started", {
		"card_sku": card_data.get("sku", ""),
		"card_name": card_data.get("name", ""),
		"decision_time": CARD_DECISION_TIME
	})
	
	card_timer_started.emit(card_data, CARD_DECISION_TIME)

func _update_card_timer(card_id: String):
	"""Update a specific card timer"""
	if not card_timers.has(card_id):
		return
	
	var timer_data = card_timers[card_id]
	timer_data.time_left -= 0.1
	
	var card_data = timer_data.card_data
	
	# Check if validation period is over
	if timer_data.is_validating and timer_data.time_left <= (CARD_DECISION_TIME - CARD_VALIDATION_TIME):
		timer_data.is_validating = false
		print("✅ Card validation complete: ", card_data.get("name", "Unknown"))
	
	# Emit timer update
	card_timer_updated.emit(card_data, timer_data.time_left)
	
	# Check for expiration
	if timer_data.time_left <= 0:
		print("⏰ Card timer expired: ", card_data.get("name", "Unknown"))
		
		# Stop and clean up timer
		timer_data.timer.stop()
		timer_data.timer.queue_free()
		card_timers.erase(card_id)
		pending_cards.erase(card_id)
		
		server_logger.log_system_event("card_timer_expired", {
			"card_sku": card_data.get("sku", ""),
			"card_name": card_data.get("name", "")
		})
		
		card_timer_expired.emit(card_data)

func play_card(card_data: Dictionary) -> bool:
	"""Play a card and stop its timer"""
	var card_sku = card_data.get("sku", "")
	
	# Find the card timer
	for card_id in card_timers.keys():
		var timer_data = card_timers[card_id]
		if timer_data.card_data.get("sku", "") == card_sku:
			print("✅ Playing card: ", card_data.get("name", "Unknown"))
			
			# Stop and clean up timer
			timer_data.timer.stop()
			timer_data.timer.queue_free()
			card_timers.erase(card_id)
			pending_cards.erase(card_id)
			
			server_logger.log_system_event("card_played_from_timer", {
				"card_sku": card_sku,
				"card_name": card_data.get("name", ""),
				"time_remaining": timer_data.time_left
			})
			
			return true
	
	return false

func discard_card(card_data: Dictionary):
	"""Manually discard a pending card"""
	var card_sku = card_data.get("sku", "")
	
	# Find and remove the card timer
	for card_id in card_timers.keys():
		var timer_data = card_timers[card_id]
		if timer_data.card_data.get("sku", "") == card_sku:
			print("🗑️ Discarding card: ", card_data.get("name", "Unknown"))
			
			# Stop and clean up timer
			timer_data.timer.stop()
			timer_data.timer.queue_free()
			card_timers.erase(card_id)
			pending_cards.erase(card_id)
			
			server_logger.log_system_event("card_discarded", {
				"card_sku": card_sku,
				"card_name": card_data.get("name", ""),
				"manual_discard": true
			})
			
			break

func clear_all_card_timers():
	"""Clear all pending card timers"""
	print("🧹 Clearing all card timers")
	
	for card_id in card_timers.keys():
		var timer_data = card_timers[card_id]
		timer_data.timer.stop()
		timer_data.timer.queue_free()
	
	card_timers.clear()
	pending_cards.clear()

func get_pending_cards() -> Array[Dictionary]:
	"""Get all cards with active timers"""
	var cards = []
	for card_data in pending_cards.values():
		cards.append(card_data)
	return cards

func get_card_time_left(card_sku: String) -> float:
	"""Get time remaining for a specific card"""
	for card_id in card_timers.keys():
		var timer_data = card_timers[card_id]
		if timer_data.card_data.get("sku", "") == card_sku:
			return timer_data.time_left
	return 0.0

func is_card_validating(card_sku: String) -> bool:
	"""Check if a card is still in validation phase"""
	for card_id in card_timers.keys():
		var timer_data = card_timers[card_id]
		if timer_data.card_data.get("sku", "") == card_sku:
			return timer_data.is_validating
	return false

# === UTILITY METHODS ===

func is_turn_active() -> bool:
	"""Check if it's currently the player's turn"""
	return is_my_turn

func get_turn_progress() -> float:
	"""Get turn progress as percentage (0.0 to 1.0)"""
	return (TURN_TIME_TOTAL - turn_time_left) / TURN_TIME_TOTAL

func format_time(seconds: float) -> String:
	"""Format time as MM:SS"""
	var minutes = int(seconds) / 60
	var secs = int(seconds) % 60
	return "%02d:%02d" % [minutes, secs]
