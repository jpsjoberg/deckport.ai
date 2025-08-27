extends Node

# Dynamic Arena Video Manager - Handles thousands of server-driven arenas
# Downloads and caches arena videos on-demand from the server

signal arena_loaded(arena_data: Dictionary, success: bool)
signal video_loaded(arena_id: int, video_type: String, success: bool)
signal video_changed(arena_id: int, arena_name: String)
signal cache_updated(cache_size: int, cache_limit: int)

# Server configuration
var server_url: String = "http://127.0.0.1:8002"
var api_headers: Array[String] = []

# Cache configuration
var cache_directory: String = "user://arena_cache/"
var max_cache_size_mb: int = 500  # 500MB cache limit
var max_cached_arenas: int = 50   # Keep 50 most recent arenas
var cache_metadata: Dictionary = {}

# Current state
var current_arena_data: Dictionary = {}
var current_video_player: VideoStreamPlayer = null
var available_arenas: Array = []
var arena_list_cache: Dictionary = {}

# HTTP requests
var http_request: HTTPRequest
var video_http_request: HTTPRequest

var server_logger

func _ready():
	print("🏟️ Dynamic Arena Video Manager initialized")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	
	# Setup HTTP requests
	setup_http_requests()
	
	# Initialize cache system
	setup_cache_system()
	
	# Load cached arena list
	load_cached_arena_list()

func setup_http_requests():
	"""Setup HTTP request nodes for API calls"""
	# Main HTTP request for API calls
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_http_response)
	http_request.timeout = 30.0
	
	# Dedicated HTTP request for video downloads
	video_http_request = HTTPRequest.new()
	add_child(video_http_request)
	video_http_request.request_completed.connect(_on_video_download_response)
	video_http_request.timeout = 120.0  # Longer timeout for video downloads
	
	print("📡 HTTP requests configured for arena system")

func setup_cache_system():
	"""Initialize the arena cache system"""
	# Create cache directory if it doesn't exist
	if not DirAccess.dir_exists_absolute(cache_directory):
		DirAccess.open("user://").make_dir_recursive(cache_directory)
		print("📁 Created arena cache directory: ", cache_directory)
	
	# Load cache metadata
	load_cache_metadata()
	
	# Clean up old cache if needed
	cleanup_cache()

func load_cache_metadata():
	"""Load cache metadata from disk"""
	var metadata_path = cache_directory + "cache_metadata.json"
	if FileAccess.file_exists(metadata_path):
		var file = FileAccess.open(metadata_path, FileAccess.READ)
		if file:
			var json_text = file.get_as_text()
			file.close()
			
			var json = JSON.new()
			var parse_result = json.parse(json_text)
			if parse_result == OK:
				cache_metadata = json.data
				print("📋 Loaded cache metadata: ", cache_metadata.size(), " entries")
			else:
				print("❌ Failed to parse cache metadata")
	else:
		cache_metadata = {}
		print("📋 No existing cache metadata found")

func save_cache_metadata():
	"""Save cache metadata to disk"""
	var metadata_path = cache_directory + "cache_metadata.json"
	var file = FileAccess.open(metadata_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(cache_metadata))
		file.close()
		print("💾 Cache metadata saved")

func cleanup_cache():
	"""Clean up old cache entries if over limits"""
	var cache_size = get_cache_size_mb()
	var arena_count = cache_metadata.size()
	
	if cache_size > max_cache_size_mb or arena_count > max_cached_arenas:
		print("🧹 Cache cleanup needed - Size: ", cache_size, "MB, Count: ", arena_count)
		
		# Sort by last accessed time (LRU eviction)
		var sorted_entries = []
		for arena_id in cache_metadata.keys():
			var entry = cache_metadata[arena_id]
			sorted_entries.append([arena_id, entry.get("last_accessed", 0)])
		
		sorted_entries.sort_custom(func(a, b): return a[1] < b[1])
		
		# Remove oldest entries
		var entries_to_remove = max(0, arena_count - max_cached_arenas)
		for i in range(entries_to_remove):
			var arena_id = str(sorted_entries[i][0])
			remove_cached_arena(arena_id)
		
		save_cache_metadata()
		cache_updated.emit(get_cache_size_mb(), max_cache_size_mb)

func get_cache_size_mb() -> float:
	"""Calculate current cache size in MB"""
	var total_size = 0
	for arena_id in cache_metadata.keys():
		var entry = cache_metadata[arena_id]
		total_size += entry.get("file_size", 0)
	return total_size / (1024.0 * 1024.0)

func remove_cached_arena(arena_id: String):
	"""Remove an arena from cache"""
	if cache_metadata.has(arena_id):
		var entry = cache_metadata[arena_id]
		
		# Remove video files
		for video_type in ["background", "battle"]:
			var video_path = entry.get(video_type + "_path", "")
			if video_path and FileAccess.file_exists(video_path):
				DirAccess.remove_absolute(video_path)
		
		# Remove thumbnail
		var thumb_path = entry.get("thumbnail_path", "")
		if thumb_path and FileAccess.file_exists(thumb_path):
			DirAccess.remove_absolute(thumb_path)
		
		# Remove from metadata
		cache_metadata.erase(arena_id)
		print("🗑️ Removed cached arena: ", arena_id)

# === PUBLIC API ===

func fetch_arena_list(filters: Dictionary = {}):
	"""Fetch list of available arenas from server"""
	var url = server_url + "/v1/arenas/list"
	var query_params = []
	
	# Add filter parameters
	for key in filters.keys():
		query_params.append(key + "=" + str(filters[key]))
	
	if query_params.size() > 0:
		url += "?" + "&".join(query_params)
	
	print("📡 Fetching arena list from: ", url)
	server_logger.log_system_event("arena_list_request", filters)
	
	var error = http_request.request(url, api_headers, HTTPClient.METHOD_GET)
	if error != OK:
		print("❌ Failed to request arena list: ", error)
		arena_loaded.emit({}, false)

func get_weighted_arena(player_preferences: Dictionary = {}):
	"""Get arena based on player preferences from server"""
	var url = server_url + "/v1/arenas/weighted"
	var body = JSON.stringify(player_preferences)
	
	print("🎲 Requesting weighted arena with preferences: ", player_preferences)
	server_logger.log_system_event("weighted_arena_request", player_preferences)
	
	var headers = api_headers.duplicate()
	headers.append("Content-Type: application/json")
	
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		print("❌ Failed to request weighted arena: ", error)
		arena_loaded.emit({}, false)

func load_arena_video(arena_data: Dictionary, video_player: VideoStreamPlayer, battle_mode: bool = false) -> bool:
	"""Load and play arena video from server or cache"""
	var arena_id = str(arena_data.get("id", 0))
	var arena_name = arena_data.get("name", "Unknown Arena")
	
	if arena_id == "0":
		print("❌ Invalid arena data provided")
		return false
	
	print("🏟️ Loading arena video: ", arena_name, " (ID: ", arena_id, ")")
	current_arena_data = arena_data
	current_video_player = video_player
	
	# Check if video is cached
	if is_arena_cached(arena_id, "background" if not battle_mode else "battle"):
		return load_cached_video(arena_id, "background" if not battle_mode else "battle")
	else:
		# Download video from server
		download_arena_video(arena_id, "background" if not battle_mode else "battle")
		return false  # Will be loaded asynchronously

func is_arena_cached(arena_id: String, video_type: String) -> bool:
	"""Check if arena video is cached locally"""
	if not cache_metadata.has(arena_id):
		return false
	
	var entry = cache_metadata[arena_id]
	var video_path = entry.get(video_type + "_path", "")
	
	return video_path != "" and FileAccess.file_exists(video_path)

func load_cached_video(arena_id: String, video_type: String) -> bool:
	"""Load video from local cache"""
	if not cache_metadata.has(arena_id):
		return false
	
	var entry = cache_metadata[arena_id]
	var video_path = entry.get(video_type + "_path", "")
	
	if video_path == "" or not FileAccess.file_exists(video_path):
		return false
	
	print("📁 Loading cached video: ", video_path)
	
	# Load video file
	var video_file = FileAccess.open(video_path, FileAccess.READ)
	if not video_file:
		print("❌ Failed to open cached video file")
		return false
	
	# Create video stream from file
	var video_stream = VideoStreamTheora.new()
	video_stream.file = video_path
	
	current_video_player.stream = video_stream
	current_video_player.loop = true
	current_video_player.volume_db = -80.0  # Mute audio
	current_video_player.visible = true
	current_video_player.play()
	
	# Update last accessed time
	entry["last_accessed"] = Time.get_unix_time_from_system()
	cache_metadata[arena_id] = entry
	save_cache_metadata()
	
	server_logger.log_system_event("arena_video_cached_loaded", {
		"arena_id": arena_id,
		"video_type": video_type,
		"path": video_path
	})
	
	print("✅ Cached arena video loaded successfully")
	video_loaded.emit(int(arena_id), video_type, true)
	video_changed.emit(int(arena_id), current_arena_data.get("name", "Unknown"))
	
	return true

func download_arena_video(arena_id: String, video_type: String):
	"""Download arena video from server"""
	var video_url = server_url + "/v1/arenas/" + arena_id + "/video/" + video_type
	
	print("📥 Downloading arena video: ", video_url)
	server_logger.log_system_event("arena_video_download_start", {
		"arena_id": arena_id,
		"video_type": video_type,
		"url": video_url
	})
	
	# Store download context for response handler
	video_http_request.set_meta("arena_id", arena_id)
	video_http_request.set_meta("video_type", video_type)
	
	var error = video_http_request.request(video_url, api_headers, HTTPClient.METHOD_GET)
	if error != OK:
		print("❌ Failed to start video download: ", error)
		video_loaded.emit(int(arena_id), video_type, false)

func load_cached_arena_list():
	"""Load cached arena list from disk"""
	var cache_path = cache_directory + "arena_list_cache.json"
	if FileAccess.file_exists(cache_path):
		var file = FileAccess.open(cache_path, FileAccess.READ)
		if file:
			var json_text = file.get_as_text()
			file.close()
			
			var json = JSON.new()
			var parse_result = json.parse(json_text)
			if parse_result == OK:
				arena_list_cache = json.data
				available_arenas = arena_list_cache.get("arenas", [])
				print("📋 Loaded cached arena list: ", available_arenas.size(), " arenas")
			else:
				print("❌ Failed to parse cached arena list")

func save_arena_list_cache(arena_data: Dictionary):
	"""Save arena list to cache"""
	var cache_path = cache_directory + "arena_list_cache.json"
	arena_list_cache = arena_data
	arena_list_cache["cached_at"] = Time.get_unix_time_from_system()
	
	var file = FileAccess.open(cache_path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(arena_list_cache))
		file.close()
		print("💾 Arena list cached")

# === HTTP RESPONSE HANDLERS ===

func _on_http_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle HTTP responses for arena API calls"""
	var response_text = body.get_string_from_utf8()
	
	print("📡 Arena API Response - Code: ", response_code, " Size: ", body.size())
	
	if result != HTTPRequest.RESULT_SUCCESS:
		print("❌ Network error: ", result)
		arena_loaded.emit({}, false)
		return
	
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(response_text)
		
		if parse_result == OK:
			var data = json.data
			
			# Handle different response types
			if data.has("arenas"):
				# Arena list response
				available_arenas = data.arenas
				save_arena_list_cache(data)
				arena_loaded.emit(data, true)
				print("✅ Arena list loaded: ", available_arenas.size(), " arenas")
			elif data.has("id"):
				# Single arena response (weighted selection)
				current_arena_data = data
				arena_loaded.emit(data, true)
				print("✅ Weighted arena selected: ", data.get("name", "Unknown"))
		else:
			print("❌ Failed to parse arena response")
			arena_loaded.emit({}, false)
	else:
		print("❌ Arena API error: ", response_code, " - ", response_text)
		arena_loaded.emit({}, false)

func _on_video_download_response(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""Handle video download responses"""
	var arena_id = video_http_request.get_meta("arena_id", "")
	var video_type = video_http_request.get_meta("video_type", "")
	
	print("📥 Video download response - Arena: ", arena_id, " Type: ", video_type, " Code: ", response_code, " Size: ", body.size())
	
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		print("❌ Video download failed: ", result, " / ", response_code)
		video_loaded.emit(int(arena_id), video_type, false)
		return
	
	# Save video to cache
	var video_filename = "arena_" + arena_id + "_" + video_type + ".mp4"
	var video_path = cache_directory + video_filename
	
	var file = FileAccess.open(video_path, FileAccess.WRITE)
	if file:
		file.store_buffer(body)
		file.close()
		
		# Update cache metadata
		if not cache_metadata.has(arena_id):
			cache_metadata[arena_id] = {}
		
		cache_metadata[arena_id][video_type + "_path"] = video_path
		cache_metadata[arena_id]["file_size"] = cache_metadata[arena_id].get("file_size", 0) + body.size()
		cache_metadata[arena_id]["last_accessed"] = Time.get_unix_time_from_system()
		cache_metadata[arena_id]["downloaded_at"] = Time.get_unix_time_from_system()
		
		save_cache_metadata()
		
		# Load the downloaded video
		if load_cached_video(arena_id, video_type):
			print("✅ Arena video downloaded and loaded successfully")
		else:
			print("❌ Failed to load downloaded video")
			video_loaded.emit(int(arena_id), video_type, false)
	else:
		print("❌ Failed to save downloaded video")
		video_loaded.emit(int(arena_id), video_type, false)

# === UTILITY METHODS ===

func set_api_headers(headers: Array[String]):
	"""Set API headers for authentication"""
	api_headers = headers

func get_available_arenas() -> Array:
	"""Get list of available arenas"""
	return available_arenas

func get_current_arena_data() -> Dictionary:
	"""Get current arena data"""
	return current_arena_data

func get_cache_info() -> Dictionary:
	"""Get cache information"""
	return {
		"size_mb": get_cache_size_mb(),
		"max_size_mb": max_cache_size_mb,
		"arena_count": cache_metadata.size(),
		"max_arenas": max_cached_arenas
	}
