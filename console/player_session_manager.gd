extends Node

# Player Session Manager - Global singleton for managing player authentication state

signal player_logged_in(player_data: Dictionary)
signal player_logged_out()
signal session_expired()

# Player session data
var is_logged_in: bool = false
var player_jwt: String = ""
var player_id: int = 0
var email: String = ""
var display_name: String = ""
var elo_rating: int = 1000
var login_time: float = 0

# Session management
var session_check_timer: Timer
var jwt_expires_at: float = 0

func _ready():
	print("👤 Player Session Manager initialized")
	
	# Setup session check timer
	session_check_timer = Timer.new()
	session_check_timer.wait_time = 60.0  # Check every minute
	session_check_timer.timeout.connect(_check_session_validity)
	add_child(session_check_timer)
	
	# Try to restore previous session
	restore_session()

func login_player(jwt: String, player_data: Dictionary):
	"""Login a player with JWT and data"""
	print("👤 Logging in player: ", player_data.get("display_name", "Unknown"))
	
	player_jwt = jwt
	player_id = player_data.get("id", 0)
	email = player_data.get("email", "")
	display_name = player_data.get("display_name", "Player")
	elo_rating = player_data.get("elo_rating", 1000)
	login_time = Time.get_unix_time_from_system()
	
	# Calculate JWT expiration (assume 24 hours if not specified)
	jwt_expires_at = login_time + 86400  # 24 hours
	
	is_logged_in = true
	
	# Save session
	save_session()
	
	# Start session monitoring
	session_check_timer.start()
	
	# Emit signal
	player_logged_in.emit(player_data)
	
	print("✅ Player logged in successfully")

func logout_player():
	"""Logout the current player"""
	print("👤 Logging out player: ", display_name)
	
	# Clear session data
	is_logged_in = false
	player_jwt = ""
	player_id = 0
	email = ""
	display_name = ""
	elo_rating = 1000
	login_time = 0
	jwt_expires_at = 0
	
	# Stop session monitoring
	session_check_timer.stop()
	
	# Clear saved session
	clear_saved_session()
	
	# Emit signal
	player_logged_out.emit()
	
	print("✅ Player logged out")

func get_player_data() -> Dictionary:
	"""Get current player data"""
	return {
		"id": player_id,
		"email": email,
		"display_name": display_name,
		"elo_rating": elo_rating,
		"login_time": login_time,
		"is_logged_in": is_logged_in
	}

func get_authenticated_headers() -> Array[String]:
	"""Get headers with player authentication"""
	var headers = [
		"Content-Type: application/json",
		"User-Agent: Deckport-Console/1.0"
	]
	
	if is_logged_in and not player_jwt.is_empty():
		headers.append("Authorization: Bearer " + player_jwt)
	
	return headers

func is_session_valid() -> bool:
	"""Check if current session is valid"""
	if not is_logged_in or player_jwt.is_empty():
		return false
	
	# Check if JWT has expired
	if Time.get_unix_time_from_system() > jwt_expires_at:
		return false
	
	return true

func save_session():
	"""Save session to persistent storage"""
	var session_data = {
		"player_jwt": player_jwt,
		"player_id": player_id,
		"email": email,
		"display_name": display_name,
		"elo_rating": elo_rating,
		"login_time": login_time,
		"jwt_expires_at": jwt_expires_at
	}
	
	var file = FileAccess.open("user://player_session.dat", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(session_data))
		file.close()
		print("💾 Player session saved")
	else:
		print("❌ Failed to save player session")

func restore_session():
	"""Restore session from persistent storage"""
	var file = FileAccess.open("user://player_session.dat", FileAccess.READ)
	if not file:
		print("📂 No saved session found")
		return
	
	var json_text = file.get_as_text()
	file.close()
	
	var json = JSON.new()
	var parse_result = json.parse(json_text)
	
	if parse_result != OK:
		print("❌ Failed to parse saved session")
		return
	
	var session_data = json.data
	
	# Restore session data
	player_jwt = session_data.get("player_jwt", "")
	player_id = session_data.get("player_id", 0)
	email = session_data.get("email", "")
	display_name = session_data.get("display_name", "")
	elo_rating = session_data.get("elo_rating", 1000)
	login_time = session_data.get("login_time", 0)
	jwt_expires_at = session_data.get("jwt_expires_at", 0)
	
	# Check if session is still valid
	if is_session_valid():
		is_logged_in = true
		session_check_timer.start()
		print("✅ Session restored for: ", display_name)
		player_logged_in.emit(get_player_data())
	else:
		print("⏰ Saved session expired")
		clear_saved_session()

func clear_saved_session():
	"""Clear saved session file"""
	if FileAccess.file_exists("user://player_session.dat"):
		DirAccess.remove_absolute("user://player_session.dat")
		print("🗑️ Saved session cleared")

func _check_session_validity():
	"""Periodically check if session is still valid"""
	if not is_session_valid():
		print("⏰ Session expired")
		session_expired.emit()
		logout_player()
