extends Control

##
## Battle Results Scene - Post-Battle Results and Statistics
##
## This scene displays the outcome of a completed battle, including victory/defeat status,
## detailed battle statistics, ELO rating changes, and options for continuing gameplay.
##
## Key Features:
## - Victory/defeat announcement with visual effects
## - Comprehensive battle statistics and analytics
## - ELO rating changes and progression tracking
## - Return to menu or play again options
## - Battle replay and sharing capabilities
##
## @author Deckport.ai Development Team
## @version 1.0
## @since 2025-09-14
##

@onready var result_banner = $CenterContainer/VBoxContainer/ResultBanner
@onready var battle_stats = $CenterContainer/VBoxContainer/BattleStats
@onready var stats_label = $CenterContainer/VBoxContainer/BattleStats/StatsLabel
@onready var elo_changes = $CenterContainer/VBoxContainer/ELOChanges
@onready var elo_label = $CenterContainer/VBoxContainer/ELOChanges/ELOLabel
@onready var play_again_button = $CenterContainer/VBoxContainer/ButtonContainer/PlayAgainButton
@onready var return_menu_button = $CenterContainer/VBoxContainer/ButtonContainer/ReturnMenuButton
@onready var view_stats_button = $CenterContainer/VBoxContainer/ButtonContainer/ViewStatsButton

var server_logger
var game_state_manager
var player_session_manager
var battle_results: Dictionary = {}

func _ready():
	print("🏆 Battle Results Scene loaded")
	
	# Initialize server logger
	server_logger = preload("res://server_logger.gd").new()
	add_child(server_logger)
	server_logger.log_scene_change("battle", "results")
	
	# Get manager references
	game_state_manager = get_node("/root/GameStateManager")
	player_session_manager = get_node("/root/PlayerSessionManager")
	
	# Connect button signals
	play_again_button.pressed.connect(_on_play_again_pressed)
	return_menu_button.pressed.connect(_on_return_menu_pressed)
	view_stats_button.pressed.connect(_on_view_stats_pressed)
	
	# Get battle results from game state manager
	if game_state_manager:
		battle_results = game_state_manager.get_battle_results()
		display_battle_results()
	else:
		# Fallback for testing
		create_test_results()
		display_battle_results()

func display_battle_results():
	"""Display the battle results and statistics"""
	var player_won = battle_results.get("player_won", false)
	
	# Update result banner
	if player_won:
		result_banner.text = "🏆 VICTORY!"
		result_banner.add_theme_color_override("font_color", Color.GOLD)
	else:
		result_banner.text = "💀 DEFEAT"
		result_banner.add_theme_color_override("font_color", Color.CRIMSON)
	
	# Update battle statistics
	var stats_text = "BATTLE STATISTICS\n\n"
	stats_text += "Duration: " + format_time(battle_results.get("duration", 0)) + "\n"
	stats_text += "Cards Played: " + str(battle_results.get("cards_played", 0)) + "\n"
	stats_text += "Damage Dealt: " + str(battle_results.get("damage_dealt", 0)) + "\n"
	stats_text += "Damage Taken: " + str(battle_results.get("damage_taken", 0)) + "\n"
	stats_text += "Turns: " + str(battle_results.get("turns", 0))
	
	stats_label.text = stats_text
	
	# Update ELO changes
	var old_elo = battle_results.get("old_elo", 1000)
	var new_elo = battle_results.get("new_elo", 1000)
	var elo_change = new_elo - old_elo
	
	var elo_text = "ELO RATING CHANGE\n\n"
	elo_text += "Previous: " + str(old_elo) + "\n"
	elo_text += "New: " + str(new_elo)
	
	if elo_change > 0:
		elo_text += " (+" + str(elo_change) + ")"
		elo_label.add_theme_color_override("font_color", Color.GREEN)
	elif elo_change < 0:
		elo_text += " (" + str(elo_change) + ")"
		elo_label.add_theme_color_override("font_color", Color.RED)
	else:
		elo_text += " (No change)"
		elo_label.add_theme_color_override("font_color", Color.WHITE)
	
	elo_label.text = elo_text

func format_time(seconds: float) -> String:
	"""Format time in MM:SS format"""
	var minutes = int(seconds / 60)
	var secs = int(seconds) % 60
	return "%d:%02d" % [minutes, secs]

func create_test_results():
	"""Create test results for demonstration"""
	battle_results = {
		"player_won": true,
		"duration": 512.0,  # 8:32
		"cards_played": 12,
		"damage_dealt": 25,
		"damage_taken": 18,
		"turns": 15,
		"old_elo": 1000,
		"new_elo": 1025
	}

func _on_play_again_pressed():
	"""Handle play again button"""
	print("🔄 Play again requested")
	server_logger.log_user_action("play_again", {})
	
	# Return to hero selection
	if game_state_manager:
		game_state_manager.change_state(game_state_manager.GameState.HERO_SELECTION)
	else:
		get_tree().change_scene_to_file("res://hero_selection_scene.tscn")

func _on_return_menu_pressed():
	"""Handle return to menu button"""
	print("🏠 Returning to main menu")
	server_logger.log_user_action("return_to_menu", {})
	
	# Return to player menu
	if game_state_manager:
		game_state_manager.change_state(game_state_manager.GameState.MENU)
	else:
		get_tree().change_scene_to_file("res://player_menu.tscn")

func _on_view_stats_pressed():
	"""Handle view detailed stats button"""
	print("📊 Viewing detailed statistics")
	server_logger.log_user_action("view_detailed_stats", battle_results)
	
	# TODO: Show detailed statistics modal or scene
	print("📈 Detailed stats display - Coming soon!")

func _input(event):
	"""Handle input events"""
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE:
			_on_play_again_pressed()
		elif event.keycode == KEY_ESCAPE:
			_on_return_menu_pressed()
		elif event.keycode == KEY_S:
			_on_view_stats_pressed()
