extends Node

##
## Game State Manager - Central Coordination System
##
## This singleton manages the complete game state across all scenes and systems.
## It coordinates matchmaking, battle progression, NFC card scanning, and maintains
## synchronization between the console interface and server-side game logic.
##
## Key Responsibilities:
## - Game state transitions (Menu → Hero Selection → Matchmaking → Battle → Results)
## - Player session management and authentication
## - Match data coordination with server
## - Physical card scanning integration
## - Battle state synchronization
## - Video streaming session management
##
## State Flow:
## MENU → HERO_SELECTION → MATCHMAKING → BATTLE_SETUP → BATTLE_ACTIVE → BATTLE_RESULTS
##
## Dependencies:
## - DeviceConnectionManager: Console authentication
## - ArenaVideoManager: Arena background videos
## - VideoStreamManager: Live opponent video streaming
## - ServerLogger: Real-time event logging
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2024-12-28
##

#region Signals
## Emitted when the game state changes between scenes/phases
signal game_state_changed(old_state: GameState, new_state: GameState)
## Emitted when matchmaking finds an opponent
signal player_matched(opponent_data: Dictionary)
## Emitted when a battle begins
signal battle_started(battle_data: Dictionary)
## Emitted when a physical card is scanned via NFC
signal card_scanned(card_data: Dictionary)
## Emitted when a battle concludes with results
signal battle_ended(results: Dictionary)
#endregion

#region Game State Enumeration
## Defines all possible game states and scene transitions
enum GameState {
	MENU,           ## Player dashboard and main menu
	HERO_SELECTION, ## Choosing starting hero for battle
	MATCHMAKING,    ## Finding opponent via matchmaking queue
	BATTLE_SETUP,   ## Setting up battle arena and video streams
	BATTLE_ACTIVE,  ## Active battle with card scanning and gameplay
	BATTLE_RESULTS, ## Displaying battle results and statistics
	DISCONNECTED    ## Network connection issues or errors
}
#endregion

#region State Variables
## Current and previous game states for transition management
var current_state: GameState = GameState.MENU
var previous_state: GameState = GameState.MENU
#endregion

#region Player Data
## Player identification and profile information
var player_id: int = 0                    ## Unique player identifier from server
var player_name: String = ""              ## Display name for this player
var player_elo: int = 1000                ## Current ELO rating for matchmaking
var selected_hero_card: Dictionary = {}   ## Hero card chosen for current battle
#endregion

#region Battle Data
## Current battle and match state information
var current_battle: Dictionary = {}       ## Active battle session data
var current_match: Dictionary = {}        ## Real match data from matchmaking system
var opponent_data: Dictionary = {}        ## Opponent player information and stats
var battle_arena: Dictionary = {}         ## Selected arena with effects and bonuses
var is_my_turn: bool = false             ## Whether it's currently this player's turn
var battle_timer: float = 0.0           ## Current turn or battle timer value
#endregion

#region Physical Card System
## NFC card scanning and gameplay state
var scanned_cards: Array[Dictionary] = []  ## Cards scanned this session
var played_cards: Array[Dictionary] = []   ## Cards played in current battle
var mana_available: int = 0               ## Current mana available for card play
var mana_per_turn: int = 1               ## Mana generated each turn
#endregion

#region Manager References
## References to core system managers
var device_connection_manager   ## Console device authentication
var arena_video_manager        ## Arena background video management
var video_stream_manager       ## Live opponent video streaming
var server_logger             ## Real-time event logging to server
#endregion

# HTTP for game API calls
var http_request: HTTPRequest
var server_url: String = "https://deckport.ai"

func _ready():
	print("🎮 Game State Manager initialized")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Get manager references with fallbacks
	device_connection_manager = get_node("/root/DeviceConnectionManager")
	if not device_connection_manager:
		print("⚠️ DeviceConnectionManager not found in GameStateManager")
	
	arena_video_manager = get_node("/root/ArenaVideoManager")
	if not arena_video_manager:
		print("⚠️ ArenaVideoManager not found in GameStateManager")
	
	video_stream_manager = get_node("/root/VideoStreamManager")
	if not video_stream_manager:
		print("⚠️ VideoStreamManager not found in GameStateManager")
	
	# Setup HTTP request
	setup_http_request()
	
	# Connect to video streaming events
	if video_stream_manager:
		video_stream_manager.stream_started.connect(_on_video_stream_started)
		video_stream_manager.participant_joined.connect(_on_opponent_joined)

func setup_http_request():
	"""Setup HTTP request for game API calls"""
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_http_response)
	http_request.timeout = 30.0

# === GAME STATE MANAGEMENT ===

func change_state(new_state: GameState):
	"""Change the current game state"""
	if new_state == current_state:
		return
	
	previous_state = current_state
	current_state = new_state
	
	print("🎮 Game state changed: ", GameState.keys()[previous_state], " -> ", GameState.keys()[current_state])
	
	server_logger.log_system_event("game_state_change", {
		"from": GameState.keys()[previous_state],
		"to": GameState.keys()[current_state],
		"player_id": player_id
	})
	
	game_state_changed.emit(previous_state, current_state)
	
	# Handle state-specific logic
	match current_state:
		GameState.HERO_SELECTION:
			start_hero_selection()
		GameState.MATCHMAKING:
			start_matchmaking()
		GameState.BATTLE_SETUP:
			setup_battle()
		GameState.BATTLE_ACTIVE:
			start_battle()
		GameState.BATTLE_RESULTS:
			show_battle_results()

func get_current_state() -> GameState:
	"""Get the current game state"""
	return current_state

func is_in_battle() -> bool:
	"""Check if currently in a battle"""
	return current_state in [GameState.BATTLE_SETUP, GameState.BATTLE_ACTIVE]

# === HERO SELECTION ===

func start_hero_selection():
	"""Start hero selection phase"""
	print("🦸 Starting hero selection")
	
	server_logger.log_system_event("hero_selection_start", {"player_id": player_id})
	
	# Load hero selection scene
	get_tree().change_scene_to_file("res://hero_selection_scene.tscn")

func select_hero(hero_card: Dictionary):
	"""Select a hero card for battle"""
	selected_hero_card = hero_card
	
	print("🦸 Hero selected: ", hero_card.get("name", "Unknown"))
	
	server_logger.log_system_event("hero_selected", {
		"player_id": player_id,
		"hero_card": hero_card.get("sku", ""),
		"hero_name": hero_card.get("name", "")
	})
	
	# Move to matchmaking
	change_state(GameState.MATCHMAKING)

# === MATCHMAKING ===

func start_matchmaking():
	"""Start looking for an opponent"""
	print("🔍 Starting matchmaking")
	
	var matchmaking_data = {
		"player_id": player_id,
		"player_elo": player_elo,
		"hero_card": selected_hero_card.get("sku", ""),
		"preferred_arena_themes": ["nature", "crystal", "divine"]
	}
	
	server_logger.log_system_event("matchmaking_start", matchmaking_data)
	
	# Make API call to join matchmaking queue
	var headers = device_connection_manager.get_auth_headers()
	headers.append("Content-Type: application/json")
	
	var error = http_request.request(
		server_url + "/v1/matchmaking/join",
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(matchmaking_data)
	)
	
	if error != OK:
		print("❌ Failed to join matchmaking: ", error)
		change_state(GameState.MENU)

func cancel_matchmaking():
	"""Cancel matchmaking and return to menu"""
	print("❌ Cancelling matchmaking")
	
	# API call to leave queue
	var headers = device_connection_manager.get_auth_headers()
	http_request.request(
		server_url + "/v1/matchmaking/leave",
		headers,
		HTTPClient.METHOD_POST
	)
	
	change_state(GameState.MENU)

# === BATTLE SETUP ===

func setup_battle():
	"""Setup battle with opponent and arena"""
	print("⚔️ Setting up battle")
	
	# Request arena selection
	if arena_video_manager:
		var player_preferences = {
			"preferred_themes": ["nature", "crystal", "divine"],
			"preferred_rarities": ["rare", "epic"],
			"difficulty_preference": 5,
			"player_level": player_elo / 100
		}
		arena_video_manager.get_weighted_arena(player_preferences)
	
	# Initialize battle state
	current_battle = {
		"battle_id": "battle_" + str(Time.get_unix_time_from_system()),
		"player1_id": player_id,
		"player2_id": opponent_data.get("player_id", 0),
		"arena_id": 0,
		"turn": 1,
		"current_player": player_id,
		"player1_health": 20,
		"player2_health": 20,
		"player1_mana": 1,
		"player2_mana": 1
	}
	
	# Setup video streaming
	if video_stream_manager:
		var streaming_options = {
			"camera": true,
			"screen_share": true,
			"audio": false
		}
		
		video_stream_manager.start_battle_stream(
			opponent_data.get("console_id", 0),
			current_battle.battle_id,
			streaming_options
		)

# === BATTLE MECHANICS ===

func start_battle():
	"""Start the active battle phase"""
	print("⚔️ Battle started!")
	
	# Reset battle state
	scanned_cards.clear()
	played_cards.clear()
	mana_available = current_battle.get("player1_mana", 1)
	is_my_turn = (current_battle.get("current_player", 0) == player_id)
	
	server_logger.log_system_event("battle_start", {
		"battle_id": current_battle.battle_id,
		"opponent_id": opponent_data.get("player_id", 0),
		"arena_id": battle_arena.get("id", 0),
		"hero_card": selected_hero_card.get("sku", "")
	})
	
	# Load battle scene
	get_tree().change_scene_to_file("res://battle_scene.tscn")

func scan_card(card_sku: String) -> bool:
	"""Handle physical card scanning during battle"""
	if not is_in_battle():
		print("⚠️ Not in battle - card scan ignored")
		return false
	
	if not is_my_turn:
		print("⚠️ Not your turn - card scan ignored")
		return false
	
	print("🃏 Card scanned: ", card_sku)
	
	# Validate card with server
	var validation_data = {
		"battle_id": current_battle.battle_id,
		"player_id": player_id,
		"card_sku": card_sku,
		"turn": current_battle.turn
	}
	
	var headers = device_connection_manager.get_auth_headers()
	headers.append("Content-Type: application/json")
	
	var error = http_request.request(
		server_url + "/v1/battle/validate-card",
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(validation_data)
	)
	
	if error == OK:
		# Add to scanned cards (will be validated by server)
		scanned_cards.append({
			"sku": card_sku,
			"scanned_at": Time.get_unix_time_from_system(),
			"turn": current_battle.turn
		})
		
		server_logger.log_nfc_scan(card_sku, true, {
			"battle_id": current_battle.battle_id,
			"turn": current_battle.turn,
			"player_turn": is_my_turn
		})
		
		return true
	else:
		print("❌ Failed to validate card: ", error)
		return false

func play_card(card_data: Dictionary) -> bool:
	"""Play a validated card"""
	if not is_my_turn:
		print("⚠️ Not your turn")
		return false
	
	var card_cost = card_data.get("mana_cost", 1)
	if mana_available < card_cost:
		print("⚠️ Not enough mana: need ", card_cost, ", have ", mana_available)
		return false
	
	print("🎴 Playing card: ", card_data.get("name", "Unknown"))
	
	# Deduct mana
	mana_available -= card_cost
	
	# Add to played cards
	played_cards.append(card_data)
	
	# Send play action to server
	var play_data = {
		"battle_id": current_battle.battle_id,
		"player_id": player_id,
		"card_sku": card_data.get("sku", ""),
		"action": "play",
		"target": null,  # Could be opponent, creature, etc.
		"turn": current_battle.turn
	}
	
	var headers = device_connection_manager.get_auth_headers()
	headers.append("Content-Type: application/json")
	
	http_request.request(
		server_url + "/v1/battle/play-card",
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(play_data)
	)
	
	server_logger.log_system_event("card_played", {
		"battle_id": current_battle.battle_id,
		"card_sku": card_data.get("sku", ""),
		"card_name": card_data.get("name", ""),
		"mana_cost": card_cost,
		"remaining_mana": mana_available
	})
	
	card_scanned.emit(card_data)
	return true

func end_turn():
	"""End current player's turn"""
	if not is_my_turn:
		print("⚠️ Not your turn")
		return
	
	print("⏭️ Ending turn")
	
	# Send end turn to server
	var turn_data = {
		"battle_id": current_battle.battle_id,
		"player_id": player_id,
		"turn": current_battle.turn,
		"cards_played": played_cards.size()
	}
	
	var headers = device_connection_manager.get_auth_headers()
	headers.append("Content-Type: application/json")
	
	http_request.request(
		server_url + "/v1/battle/end-turn",
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(turn_data)
	)
	
	# Reset turn state
	is_my_turn = false
	scanned_cards.clear()
	
	server_logger.log_system_event("turn_ended", {
		"battle_id": current_battle.battle_id,
		"turn": current_battle.turn,
		"cards_played": played_cards.size()
	})

func attack_opponent():
	"""Attack opponent directly"""
	if not is_my_turn:
		print("⚠️ Not your turn")
		return
	
	print("⚔️ Attacking opponent")
	
	var attack_data = {
		"battle_id": current_battle.battle_id,
		"player_id": player_id,
		"action": "attack",
		"target": "opponent",
		"turn": current_battle.turn
	}
	
	var headers = device_connection_manager.get_auth_headers()
	headers.append("Content-Type: application/json")
	
	http_request.request(
		server_url + "/v1/battle/attack",
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(attack_data)
	)

# === BATTLE RESULTS ===

func show_battle_results():
	"""Show battle results and handle rewards"""
	print("🏆 Showing battle results")
	
	var results = current_battle.get("results", {})
	var winner_id = results.get("winner_id", 0)
	var is_winner = (winner_id == player_id)
	
	server_logger.log_system_event("battle_ended", {
		"battle_id": current_battle.battle_id,
		"winner_id": winner_id,
		"is_winner": is_winner,
		"duration_seconds": results.get("duration_seconds", 0)
	})
	
	battle_ended.emit(results)
	
	# End video streaming
	if video_stream_manager:
		video_stream_manager.end_current_stream()
	
	# Return to menu after showing results
	await get_tree().create_timer(5.0).timeout
	change_state(GameState.MENU)

# === EVENT HANDLERS ===

func _on_video_stream_started(stream_id: String, success: bool):
	"""Handle video stream started"""
	if success:
		print("✅ Video stream started for battle: ", stream_id)
		# Move to active battle once video is ready
		change_state(GameState.BATTLE_ACTIVE)
	else:
		print("❌ Failed to start video stream")
		# Continue without video
		change_state(GameState.BATTLE_ACTIVE)

func _on_opponent_joined(participant_info: Dictionary):
	"""Handle opponent joining video stream"""
	print("👥 Opponent joined video stream: ", participant_info)

func _on_http_response(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP responses from game API"""
	var response_text = body.get_string_from_utf8()
	
	if result != HTTPRequest.RESULT_SUCCESS:
		print("❌ Network error: ", result)
		return
	
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(response_text)
		
		if parse_result == OK:
			var data = json.data
			
			# Handle different response types
			if data.has("opponent_found"):
				# Matchmaking success
				opponent_data = data.opponent_data
				player_matched.emit(opponent_data)
				change_state(GameState.BATTLE_SETUP)
			
			elif data.has("card_valid"):
				# Card validation response
				if data.card_valid:
					var card_data = data.card_data
					# Card is valid, can be played
					print("✅ Card validated: ", card_data.get("name", "Unknown"))
				else:
					print("❌ Invalid card: ", data.get("reason", "Unknown"))
			
			elif data.has("battle_update"):
				# Battle state update
				var update = data.battle_update
				current_battle.merge(update)
				
				# Check if it's now our turn
				is_my_turn = (update.get("current_player", 0) == player_id)
				mana_available = update.get("player_mana", mana_available)
				
				print("🔄 Battle updated - My turn: ", is_my_turn, " Mana: ", mana_available)
			
			elif data.has("battle_ended"):
				# Battle finished
				current_battle["results"] = data.results
				change_state(GameState.BATTLE_RESULTS)
	else:
		print("❌ API error: ", response_code, " - ", response_text)

# === UTILITY METHODS ===

func get_battle_data() -> Dictionary:
	"""Get current battle data"""
	return current_battle

func get_current_match() -> Dictionary:
	"""Get current match data from matchmaking"""
	return current_match

func set_current_match(match_data: Dictionary):
	"""Set current match data from matchmaking"""
	current_match = match_data
	print("🎯 Match data set: ", match_data.get("match_id", "unknown"))
	
	# Extract opponent data from match data
	if match_data.has("opponent_name"):
		opponent_data = {
			"player_name": match_data.get("opponent_name", "Unknown"),
			"player_id": match_data.get("opponent_id", 0),
			"player_elo": match_data.get("opponent_rating", 1000),
			"hero_name": match_data.get("opponent_hero", "Unknown Hero")
		}

func get_opponent_data() -> Dictionary:
	"""Get opponent data"""
	return opponent_data

func get_selected_hero() -> Dictionary:
	"""Get selected hero card"""
	return selected_hero_card

func is_player_turn() -> bool:
	"""Check if it's the player's turn"""
	return is_my_turn

func get_available_mana() -> int:
	"""Get available mana for this turn"""
	return mana_available

func get_played_cards() -> Array[Dictionary]:
	"""Get cards played this battle"""
	return played_cards

func set_player_data(id: int, name: String, elo: int):
	"""Set player data"""
	player_id = id
	player_name = name
	player_elo = elo
