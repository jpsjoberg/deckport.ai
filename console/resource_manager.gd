extends Node
# class_name ResourceManager  # Commented out to avoid autoload conflict

signal energy_changed(current: int, maximum: int)
signal mana_changed(mana_pool: Dictionary)
signal resource_insufficient(resource_type: String, required: int, available: int)

# Energy system (universal resource)
var current_energy: int = 0
var max_energy: int = 0

# Mana system (arena-dependent resource)
var available_mana: Dictionary = {
	"CRIMSON": 0,
	"AZURE": 0,
	"VERDANT": 0, 
	"GOLDEN": 0,
	"SHADOW": 0,
	"AETHER": 0
}

# Mana that carries over between turns (optional rule)
var persistent_mana: bool = false

func _ready():
	print("⚡🔮 Resource Manager initialized")

func start_new_turn(turn_number: int, arena_mana: Dictionary = {}):
	"""Initialize resources for a new turn"""
	# Energy: Always equals turn number
	max_energy = turn_number
	current_energy = turn_number
	
	# Mana: Add arena generation
	if not persistent_mana:
		# Reset mana each turn
		for color in available_mana:
			available_mana[color] = 0
	
	# Add arena-generated mana
	for color in arena_mana:
		available_mana[color] += arena_mana[color]
	
	# Emit signals
	energy_changed.emit(current_energy, max_energy)
	mana_changed.emit(available_mana.duplicate())
	
	print("⚡ Turn ", turn_number, " - Energy: ", current_energy)
	print("🔮 Mana pool: ", _format_mana_display())

func can_afford_energy_cost(cost: int) -> bool:
	"""Check if player has enough energy"""
	return current_energy >= cost

func can_afford_mana_cost(mana_costs: Dictionary) -> bool:
	"""Check if player has enough mana of required colors"""
	for color in mana_costs:
		var required = mana_costs[color]
		var available = available_mana.get(color, 0)
		if available < required:
			return false
	return true

func can_afford_card_cost(card_data: Dictionary) -> Dictionary:
	"""Check if player can afford both energy and mana costs"""
	var result = {
		"can_afford": true,
		"energy_sufficient": true,
		"mana_sufficient": true,
		"missing_resources": []
	}
	
	# Check energy cost
	var energy_cost = card_data.get("energy_cost", 1)
	if not can_afford_energy_cost(energy_cost):
		result.can_afford = false
		result.energy_sufficient = false
		result.missing_resources.append({
			"type": "energy",
			"required": energy_cost,
			"available": current_energy
		})
	
	# Check mana costs
	var mana_costs = card_data.get("mana_cost", {})
	if not mana_costs.is_empty():
		for color in mana_costs:
			var required = mana_costs[color]
			var available = available_mana.get(color, 0)
			if available < required:
				result.can_afford = false
				result.mana_sufficient = false
				result.missing_resources.append({
					"type": "mana",
					"color": color,
					"required": required,
					"available": available
				})
	
	return result

func spend_energy(amount: int) -> bool:
	"""Spend energy if available"""
	if current_energy >= amount:
		current_energy -= amount
		energy_changed.emit(current_energy, max_energy)
		print("⚡ Spent ", amount, " energy (", current_energy, "/", max_energy, " remaining)")
		return true
	else:
		resource_insufficient.emit("energy", amount, current_energy)
		return false

func spend_mana(mana_costs: Dictionary) -> bool:
	"""Spend mana if available"""
	# First check if we can afford it
	if not can_afford_mana_cost(mana_costs):
		for color in mana_costs:
			var required = mana_costs[color]
			var available = available_mana.get(color, 0)
			if available < required:
				resource_insufficient.emit("mana_" + color, required, available)
		return false
	
	# Spend the mana
	for color in mana_costs:
		available_mana[color] -= mana_costs[color]
	
	mana_changed.emit(available_mana.duplicate())
	print("🔮 Spent mana: ", mana_costs, " (remaining: ", _format_mana_display(), ")")
	return true

func spend_card_resources(card_data: Dictionary) -> bool:
	"""Spend both energy and mana for a card"""
	var cost_check = can_afford_card_cost(card_data)
	if not cost_check.can_afford:
		print("❌ Cannot afford card: ", card_data.get("name", "Unknown"))
		for resource in cost_check.missing_resources:
			print("  Missing ", resource.type, ": ", resource.required, "/", resource.available)
		return false
	
	# Spend energy
	var energy_cost = card_data.get("energy_cost", 1)
	if not spend_energy(energy_cost):
		return false
	
	# Spend mana
	var mana_costs = card_data.get("mana_cost", {})
	if not mana_costs.is_empty():
		if not spend_mana(mana_costs):
			# Refund energy if mana spending failed
			current_energy += energy_cost
			energy_changed.emit(current_energy, max_energy)
			return false
	
	print("✅ Card resources spent for: ", card_data.get("name", "Unknown"))
	return true

func add_mana(color: String, amount: int):
	"""Add mana of specific color"""
	if available_mana.has(color):
		available_mana[color] += amount
		mana_changed.emit(available_mana.duplicate())
		print("🔮 Added ", amount, " ", color, " mana")

func add_energy(amount: int):
	"""Add energy (rare, usually from card effects)"""
	current_energy = min(current_energy + amount, max_energy)
	energy_changed.emit(current_energy, max_energy)
	print("⚡ Added ", amount, " energy")

func get_energy_status() -> Dictionary:
	"""Get current energy status"""
	return {
		"current": current_energy,
		"maximum": max_energy,
		"percentage": float(current_energy) / float(max_energy) if max_energy > 0 else 0.0
	}

func get_mana_status() -> Dictionary:
	"""Get current mana status"""
	var total_mana = 0
	var active_colors = []
	
	for color in available_mana:
		var amount = available_mana[color]
		if amount > 0:
			active_colors.append({"color": color, "amount": amount})
			total_mana += amount
	
	return {
		"total": total_mana,
		"colors": active_colors,
		"full_pool": available_mana.duplicate()
	}

func reset_resources():
	"""Reset all resources (for new game)"""
	current_energy = 0
	max_energy = 0
	for color in available_mana:
		available_mana[color] = 0
	
	energy_changed.emit(current_energy, max_energy)
	mana_changed.emit(available_mana.duplicate())
	print("🔄 Resources reset")

func _format_mana_display() -> String:
	"""Format mana for display"""
	var mana_parts = []
	for color in available_mana:
		var amount = available_mana[color]
		if amount > 0:
			mana_parts.append(color + ":" + str(amount))
	
	if mana_parts.is_empty():
		return "None"
	return " ".join(mana_parts)

# Debug functions
func debug_add_energy(amount: int):
	"""Debug: Add energy beyond normal limits"""
	current_energy += amount
	max_energy = max(max_energy, current_energy)
	energy_changed.emit(current_energy, max_energy)

func debug_add_all_mana(amount: int):
	"""Debug: Add mana of all colors"""
	for color in available_mana:
		available_mana[color] += amount
	mana_changed.emit(available_mana.duplicate())











