extends Node
class_name TurnManager

# Turn Management System
# Handles turn phases, timing, and game flow according to Deckport rules

signal phase_changed(new_phase: String)
signal turn_changed(new_turn: int, new_player: int)
signal timer_updated(remaining_ms: int)
signal play_window_opened(card_types: Array)
signal play_window_closed()

# Turn phases as defined in game rules
enum Phase {
	START,    # Gain mana/energy, resolve start effects
	MAIN,     # Summon heroes, play actions, activate abilities
	ATTACK,   # Declare attacks, play reactions
	END       # Resolve end effects, pass turn
}

# Timing configuration
var turn_time_seconds: int = 60
var play_window_seconds: int = 10
var quickdraw_bonus_seconds: int = 3

# Current state
var current_turn: int = 1
var current_player: int = 0  # 0 or 1
var current_phase: Phase = Phase.START
var phase_start_time: float = 0
var remaining_phase_time_ms: int = 0

# Play window state
var play_window_active: bool = false
var play_window_start_time: float = 0
var play_window_card_types: Array = []

# Match state
var match_active: bool = false
var game_state: Dictionary = {}

func _ready():
	Logger.log_info("TurnManager", "Turn manager initialized")

func start_match(initial_state: Dictionary):
	"""Start match with initial game state"""
	Logger.log_info("TurnManager", "Starting match turn management")
	
	game_state = initial_state
	match_active = true
	
	# Extract initial turn info
	current_turn = game_state.get("turn", 1)
	current_player = game_state.get("current_player", 0)
	current_phase = _string_to_phase(game_state.get("phase", "start"))
	
	# Start phase timer
	start_phase_timer()
	
	# Emit initial state
	turn_changed.emit(current_turn, current_player)
	phase_changed.emit(_phase_to_string(current_phase))

func start_phase_timer():
	"""Start timer for current phase"""
	phase_start_time = Time.get_time_dict_from_system()["unix"]
	
	# Set phase duration based on phase type
	var phase_duration_seconds = _get_phase_duration(current_phase)
	remaining_phase_time_ms = phase_duration_seconds * 1000
	
	Logger.log_info("TurnManager", "Phase timer started", {
		"phase": _phase_to_string(current_phase),
		"duration_seconds": phase_duration_seconds
	})

func _get_phase_duration(phase: Phase) -> int:
	"""Get duration for specific phase"""
	match phase:
		Phase.START:
			return 10  # 10 seconds for start phase
		Phase.MAIN:
			return 40  # 40 seconds for main phase
		Phase.ATTACK:
			return 15  # 15 seconds for attack phase
		Phase.END:
			return 5   # 5 seconds for end phase
		_:
			return 10

func _process(delta):
	"""Update timers every frame"""
	if not match_active:
		return
	
	# Update phase timer
	remaining_phase_time_ms -= int(delta * 1000)
	
	# Emit timer update
	timer_updated.emit(remaining_phase_time_ms)
	
	# Check for phase timeout
	if remaining_phase_time_ms <= 0:
		_handle_phase_timeout()
	
	# Update play window timer if active
	if play_window_active:
		var play_window_elapsed = Time.get_time_dict_from_system()["unix"] - play_window_start_time
		if play_window_elapsed >= play_window_seconds:
			close_play_window()

func _handle_phase_timeout():
	"""Handle phase timer expiration"""
	Logger.log_info("TurnManager", "Phase timeout", {"phase": _phase_to_string(current_phase)})
	
	# Auto-advance to next phase
	advance_to_next_phase()

func advance_to_next_phase():
	"""Advance to the next phase"""
	var next_phase = _get_next_phase(current_phase)
	
	# If we're going back to start, advance turn
	if next_phase == Phase.START:
		advance_turn()
	else:
		change_phase(next_phase)

func change_phase(new_phase: Phase):
	"""Change to a new phase"""
	var old_phase = current_phase
	current_phase = new_phase
	
	Logger.log_info("TurnManager", "Phase changed", {
		"from": _phase_to_string(old_phase),
		"to": _phase_to_string(new_phase)
	})
	
	# Start new phase timer
	start_phase_timer()
	
	# Handle phase-specific logic
	_handle_phase_start(new_phase)
	
	# Emit phase change
	phase_changed.emit(_phase_to_string(new_phase))

func advance_turn():
	"""Advance to next turn"""
	current_turn += 1
	current_player = 1 - current_player  # Switch players (0 -> 1, 1 -> 0)
	current_phase = Phase.START
	
	Logger.log_info("TurnManager", "Turn advanced", {
		"turn": current_turn,
		"player": current_player
	})
	
	# Start new turn
	start_phase_timer()
	_handle_phase_start(Phase.START)
	
	# Emit turn change
	turn_changed.emit(current_turn, current_player)
	phase_changed.emit(_phase_to_string(current_phase))

func _handle_phase_start(phase: Phase):
	"""Handle phase-specific start logic"""
	match phase:
		Phase.START:
			_handle_start_phase()
		Phase.MAIN:
			_handle_main_phase()
		Phase.ATTACK:
			_handle_attack_phase()
		Phase.END:
			_handle_end_phase()

func _handle_start_phase():
	"""Handle start phase logic"""
	Logger.log_info("TurnManager", "Start phase - gaining resources")
	
	# TODO: Implement resource generation
	# - Gain mana (1 per color in play)
	# - Gain energy (hero base + arena bonus)
	# - Apply arena passive effects

func _handle_main_phase():
	"""Handle main phase logic"""
	Logger.log_info("TurnManager", "Main phase - cards can be played")
	
	# Open play window for main phase cards
	var playable_types = ["CREATURE", "STRUCTURE", "ACTION_SLOW", "EQUIPMENT", "ENCHANTMENT", "ARTIFACT", "RITUAL"]
	open_play_window(playable_types)

func _handle_attack_phase():
	"""Handle attack phase logic"""
	Logger.log_info("TurnManager", "Attack phase - attacks and reactions")
	
	# TODO: Handle attack declarations
	# Open play window for reactions
	var reaction_types = ["ACTION_FAST", "TRAP"]
	open_play_window(reaction_types)

func _handle_end_phase():
	"""Handle end phase logic"""
	Logger.log_info("TurnManager", "End phase - resolving effects")
	
	# TODO: Resolve end-of-turn effects
	# Handle Focus banking

func open_play_window(card_types: Array):
	"""Open play window for specific card types"""
	if play_window_active:
		Logger.log_warning("TurnManager", "Play window already active")
		return
	
	Logger.log_info("TurnManager", "Opening play window", {"card_types": card_types})
	
	play_window_active = true
	play_window_start_time = Time.get_time_dict_from_system()["unix"]
	play_window_card_types = card_types
	
	play_window_opened.emit(card_types)

func close_play_window():
	"""Close current play window"""
	if not play_window_active:
		return
	
	Logger.log_info("TurnManager", "Closing play window")
	
	play_window_active = false
	play_window_card_types = []
	
	play_window_closed.emit()

func is_card_playable_now(card_data: Dictionary) -> bool:
	"""Check if card can be played in current phase/window"""
	if not match_active:
		return false
	
	if not play_window_active:
		return false
	
	var card_category = card_data.get("category", "")
	return card_category in play_window_card_types

func get_quickdraw_bonus_available() -> bool:
	"""Check if quickdraw bonus is available"""
	if not play_window_active:
		return false
	
	var elapsed = Time.get_time_dict_from_system()["unix"] - play_window_start_time
	return elapsed <= quickdraw_bonus_seconds

func _get_next_phase(phase: Phase) -> Phase:
	"""Get the next phase in sequence"""
	match phase:
		Phase.START:
			return Phase.MAIN
		Phase.MAIN:
			return Phase.ATTACK
		Phase.ATTACK:
			return Phase.END
		Phase.END:
			return Phase.START
		_:
			return Phase.START

func _phase_to_string(phase: Phase) -> String:
	"""Convert phase enum to string"""
	match phase:
		Phase.START:
			return "start"
		Phase.MAIN:
			return "main"
		Phase.ATTACK:
			return "attack"
		Phase.END:
			return "end"
		_:
			return "unknown"

func _string_to_phase(phase_str: String) -> Phase:
	"""Convert string to phase enum"""
	match phase_str.to_lower():
		"start":
			return Phase.START
		"main":
			return Phase.MAIN
		"attack":
			return Phase.ATTACK
		"end":
			return Phase.END
		_:
			return Phase.START

func end_match():
	"""End the current match"""
	Logger.log_info("TurnManager", "Match ended")
	
	match_active = false
	play_window_active = false
	
	# Reset state
	current_turn = 1
	current_player = 0
	current_phase = Phase.START

func get_match_statistics() -> Dictionary:
	"""Get current match statistics"""
	return {
		"turn": current_turn,
		"phase": _phase_to_string(current_phase),
		"current_player": current_player,
		"play_window_active": play_window_active,
		"remaining_time_ms": remaining_phase_time_ms
	}
