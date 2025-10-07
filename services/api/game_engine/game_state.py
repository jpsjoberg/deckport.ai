"""
Game State Management
Handles the complete state of a match including players, cards, and game rules
Enhanced with card abilities and arena effects integration
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import sys
sys.path.append('/home/jp/deckport.ai')

from .card_abilities import CardAbilitiesEngine
from .arena_effects import ArenaEffectsEngine

class GamePhase(str, Enum):
    START = "start"
    MAIN = "main" 
    ATTACK = "attack"
    END = "end"

class CardLocation(str, Enum):
    HAND = "hand"
    ARSENAL = "arsenal"
    EQUIPMENT = "equipment"
    BATTLEFIELD = "battlefield"
    GRAVEYARD = "graveyard"

@dataclass
class PlayerState:
    """State for a single player"""
    player_id: int
    team: int
    health: int = 20
    energy: int = 0
    mana: Dict[str, int] = None
    hero: Optional[Dict] = None
    hand: List[Dict] = None
    arsenal: List[Dict] = None
    equipment: List[Dict] = None
    battlefield: List[Dict] = None
    graveyard: List[Dict] = None
    
    def __post_init__(self):
        if self.mana is None:
            self.mana = {}
        if self.hand is None:
            self.hand = []
        if self.arsenal is None:
            self.arsenal = []
        if self.equipment is None:
            self.equipment = []
        if self.battlefield is None:
            self.battlefield = []
        if self.graveyard is None:
            self.graveyard = []

@dataclass
class ArenaState:
    """State for the game arena"""
    name: str
    color: str
    passive_effect: str
    active_effects: List[Dict] = None
    
    def __post_init__(self):
        if self.active_effects is None:
            self.active_effects = []

class GameState:
    """Complete game state manager"""
    
    def __init__(self, match_id: str, players: List[Dict], arena: Dict = None):
        self.match_id = match_id
        self.seed = self._generate_seed()
        self.status = "active"
        self.turn = 1
        self.phase = GamePhase.START
        self.current_player = 0
        self.sequence = 0  # For state synchronization
        
        # Initialize game engines
        self.abilities_engine = CardAbilitiesEngine()
        self.arena_engine = ArenaEffectsEngine()
        
        # Game rules
        self.rules = {
            "turn_time_seconds": 60,
            "play_window_seconds": 10,
            "quickdraw_bonus_seconds": 3,
            "max_turns": 20,
            "starting_health": 20,
            "starting_hand_size": 5
        }
        
        # Match tracking for objectives
        self.match_stats = {
            "fire_damage_total": 0,
            "healing_total": 0,
            "creatures_frozen_count": 0,
            "cards_played": 0
        }
        
        # Initialize players
        self.players = {}
        for i, player_data in enumerate(players):
            self.players[str(i)] = PlayerState(
                player_id=player_data.get('player_id'),
                team=i,
                health=self.rules["starting_health"]
            )
        
        # Initialize arena
        if arena:
            arena_name = arena.get('name', 'aether_void')
            self.arena = ArenaState(
                name=arena.get('display_name', arena_name),
                color=arena.get('color', 'AETHER'),
                passive_effect=arena.get('passive', 'none')
            )
        else:
            arena_name = "aether_void"
            self.arena = ArenaState(
                name="Aether Void",
                color="AETHER", 
                passive_effect="neutral_ground"
            )
        
        # Initialize arena effects
        self.arena_state = self.arena_engine.initialize_arena(arena_name, self)
        
        # Timer state
        self.timer = {
            "phase_start": datetime.now(timezone.utc).isoformat(),
            "remaining_ms": self._get_phase_duration(self.phase) * 1000
        }
        
        # Play window state
        self.play_window = {
            "active": False,
            "card_types": [],
            "start_time": None,
            "remaining_ms": 0
        }
        
        # Match history
        self.history = []
        
    def _generate_seed(self) -> int:
        """Generate random seed for reproducible randomness"""
        import random
        return random.randint(1000000, 9999999)
    
    def _get_phase_duration(self, phase: GamePhase) -> int:
        """Get duration in seconds for a phase"""
        durations = {
            GamePhase.START: 10,
            GamePhase.MAIN: 40, 
            GamePhase.ATTACK: 15,
            GamePhase.END: 5
        }
        return durations.get(phase, 10)
    
    def advance_phase(self) -> Dict[str, Any]:
        """Advance to next phase and return state changes"""
        old_phase = self.phase
        
        # Determine next phase
        phase_order = [GamePhase.START, GamePhase.MAIN, GamePhase.ATTACK, GamePhase.END]
        current_index = phase_order.index(self.phase)
        next_index = (current_index + 1) % len(phase_order)
        
        # If back to start, advance turn
        if next_index == 0:
            self.turn += 1
            self.current_player = 1 - self.current_player
        
        self.phase = phase_order[next_index]
        self.sequence += 1
        
        # Reset timer
        self.timer = {
            "phase_start": datetime.now(timezone.utc).isoformat(),
            "remaining_ms": self._get_phase_duration(self.phase) * 1000
        }
        
        # Close any active play window
        self.play_window["active"] = False
        
        # Handle phase-specific logic
        phase_changes = self._handle_phase_start()
        
        # Record in history
        self.history.append({
            "type": "phase_change",
            "from": old_phase.value,
            "to": self.phase.value,
            "turn": self.turn,
            "player": self.current_player,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "turn": self.turn,
            "phase": self.phase.value,
            "current_player": self.current_player,
            "timer": self.timer,
            "play_window": self.play_window,
            **phase_changes
        }
    
    def _handle_phase_start(self) -> Dict[str, Any]:
        """Handle phase-specific start logic"""
        changes = {}
        
        if self.phase == GamePhase.START:
            changes.update(self._handle_start_phase())
        elif self.phase == GamePhase.MAIN:
            changes.update(self._handle_main_phase())
        elif self.phase == GamePhase.ATTACK:
            changes.update(self._handle_attack_phase())
        elif self.phase == GamePhase.END:
            changes.update(self._handle_end_phase())
            
        return changes
    
    def _handle_start_phase(self) -> Dict[str, Any]:
        """Handle start phase - resource generation and arena effects"""
        current_player_state = self.players[str(self.current_player)]
        
        # Generate energy (turn number = energy available)
        energy_gain = self.turn
        current_player_state.energy = energy_gain
        
        # Generate arena-based mana
        arena_name = self.arena_state.get("arena_name", "aether_void")
        generated_mana = self.arena_engine.generate_turn_mana(arena_name, self, self.current_player)
        
        # Process turn start effects (status effects, arena rules)
        status_effects = self.abilities_engine.process_turn_start_effects(self)
        arena_effects = self.arena_engine.apply_turn_start_effects(arena_name, self, self.turn)
        
        # Update arena turn counter
        self.arena_state["turn_counter"] = self.turn
        
        return {
            "players": {
                str(self.current_player): {
                    "energy": current_player_state.energy,
                    "mana": current_player_state.mana
                }
            },
            "generated_mana": generated_mana,
            "status_effects": status_effects,
            "arena_effects": arena_effects
        }
    
    def _handle_main_phase(self) -> Dict[str, Any]:
        """Handle main phase - open play window"""
        playable_types = [
            "CREATURE", "STRUCTURE", "ACTION_SLOW", 
            "EQUIPMENT", "ENCHANTMENT", "ARTIFACT", "RITUAL"
        ]
        
        self.play_window = {
            "active": True,
            "card_types": playable_types,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "remaining_ms": self.rules["play_window_seconds"] * 1000
        }
        
        return {"play_window": self.play_window}
    
    def _handle_attack_phase(self) -> Dict[str, Any]:
        """Handle attack phase - reactions allowed"""
        reaction_types = ["ACTION_FAST", "TRAP"]
        
        self.play_window = {
            "active": True,
            "card_types": reaction_types,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "remaining_ms": self.rules["play_window_seconds"] * 1000
        }
        
        return {"play_window": self.play_window}
    
    def _handle_end_phase(self) -> Dict[str, Any]:
        """Handle end phase - cleanup"""
        # TODO: Implement end-of-turn effects
        # - Resolve temporary effects
        # - Handle Focus banking
        # - Cleanup expired effects
        
        return {}
    
    def play_card(self, player_team: int, card_id: str, action: str, target: Optional[str] = None) -> Dict[str, Any]:
        """Play a card and return state changes"""
        if player_team != self.current_player:
            raise ValueError("Not your turn")
        
        if not self.play_window["active"]:
            raise ValueError("No play window active")
        
        player_state = self.players[str(player_team)]
        
        # Find card in hand or arsenal
        card = None
        card_location = None
        
        for location in ["hand", "arsenal"]:
            cards = getattr(player_state, location)
            for i, c in enumerate(cards):
                if c.get('id') == card_id:
                    card = cards.pop(i)
                    card_location = location
                    break
            if card:
                break
        
        if not card:
            raise ValueError("Card not found")
        
        # Validate card type is playable
        card_category = card.get('category', '')
        if card_category not in self.play_window["card_types"]:
            raise ValueError(f"Cannot play {card_category} in {self.phase.value} phase")
        
        # Check costs
        if not self._can_afford_card(player_state, card):
            raise ValueError("Cannot afford card")
        
        # Pay costs
        self._pay_card_costs(player_state, card)
        
        # Apply card effect
        effect_result = self._apply_card_effect(player_state, card, action, target)
        
        # Record in history
        self.history.append({
            "type": "card_played",
            "player": player_team,
            "card_id": card_id,
            "card_name": card.get('name', 'Unknown'),
            "action": action,
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        self.sequence += 1
        
        return {
            "players": {str(player_team): asdict(player_state)},
            "effect_result": effect_result,
            "sequence": self.sequence
        }
    
    def _can_afford_card(self, player_state: PlayerState, card: Dict) -> bool:
        """Check if player can afford to play card"""
        energy_cost = card.get('energy_cost', 0)
        mana_costs = card.get('mana_costs', {})
        
        if player_state.energy < energy_cost:
            return False
        
        for color, cost in mana_costs.items():
            if player_state.mana.get(color, 0) < cost:
                return False
        
        return True
    
    def _pay_card_costs(self, player_state: PlayerState, card: Dict):
        """Pay the costs for playing a card"""
        energy_cost = card.get('energy_cost', 0)
        mana_costs = card.get('mana_costs', {})
        
        player_state.energy -= energy_cost
        
        for color, cost in mana_costs.items():
            player_state.mana[color] -= cost
    
    def _apply_card_effect(self, player_state: PlayerState, card: Dict, action: str, target: Optional[str]) -> Dict:
        """Apply card effect to game state with full ability execution"""
        card_category = card.get('category', '')
        effect_results = []
        
        # Execute card abilities
        card_abilities = card.get('abilities', [])
        for ability_data in card_abilities:
            if isinstance(ability_data, dict):
                ability_name = ability_data.get('name', '')
                ability_params = ability_data.get('parameters', {})
            else:
                ability_name = str(ability_data)
                ability_params = {}
            
            if ability_name:
                # Add card as caster context
                caster = {
                    "id": card.get('id', 'unknown'),
                    "name": card.get('name', 'Unknown Card'),
                    "team": player_state.team,
                    "health": card.get('health', 1),
                    "attack": card.get('attack', 0),
                    "defense": card.get('defense', 0)
                }
                
                # Execute ability
                ability_result = self.abilities_engine.execute_ability(
                    ability_name, ability_params, caster, self, target
                )
                
                if ability_result.success:
                    effect_results.append(ability_result.to_dict())
                    
                    # Update match stats for objectives
                    self.match_stats["fire_damage_total"] += ability_result.damage_dealt
                    self.match_stats["healing_total"] += ability_result.healing_done
                    
                    # Check arena objectives
                    arena_name = self.arena_state.get("arena_name", "aether_void")
                    objective_result = self.arena_engine.check_arena_objectives(
                        arena_name, self, {
                            "player_id": player_state.player_id,
                            "fire_damage_total": self.match_stats["fire_damage_total"],
                            "healing_total": self.match_stats["healing_total"],
                            "creatures_frozen_count": self.match_stats["creatures_frozen_count"]
                        }
                    )
                    
                    if objective_result:
                        effect_results.append({"type": "objective_completed", "objective": objective_result})
        
        # Handle card placement
        placement_result = {"type": "unknown", "location": "graveyard"}
        
        if card_category in ["CREATURE", "STRUCTURE"]:
            # Summon to battlefield
            card["id"] = f"{card.get('name', 'card')}_{self.sequence}"
            player_state.battlefield.append(card)
            placement_result = {"type": "summon", "location": "battlefield"}
        
        elif card_category == "EQUIPMENT":
            # Equip to player
            player_state.equipment.append(card)
            placement_result = {"type": "equip", "location": "equipment"}
        
        elif card_category in ["ACTION_FAST", "ACTION_SLOW"]:
            # Immediate effect then discard
            player_state.graveyard.append(card)
            placement_result = {"type": "action", "location": "graveyard"}
        
        elif card_category == "ENCHANTMENT":
            # Apply ongoing effect
            player_state.battlefield.append(card)
            placement_result = {"type": "enchantment", "location": "battlefield"}
        
        else:
            # Default: discard
            player_state.graveyard.append(card)
            placement_result = {"type": "discard", "location": "graveyard"}
        
        # Update match stats
        self.match_stats["cards_played"] += 1
        
        return {
            "placement": placement_result,
            "ability_results": effect_results,
            "match_stats": self.match_stats
        }
    
    def _resolve_action_card(self, card: Dict, target: Optional[str]) -> Dict:
        """Resolve action card effects"""
        # TODO: Implement specific card effects
        # For now, return basic effect info
        return {
            "card_name": card.get('name', 'Unknown'),
            "description": card.get('description', 'No effect'),
            "target": target
        }
    
    def check_win_conditions(self) -> Optional[Dict[str, Any]]:
        """Check if any win conditions are met"""
        for team_str, player_state in self.players.items():
            # Health-based win condition
            if player_state.health <= 0:
                winner = 1 - int(team_str)  # Other player wins
                return {
                    "winner": winner,
                    "condition": "health",
                    "description": f"Player {team_str} health reached 0"
                }
        
        # Turn limit win condition
        if self.turn > self.rules["max_turns"]:
            # Player with higher health wins
            p0_health = self.players["0"].health
            p1_health = self.players["1"].health
            
            if p0_health > p1_health:
                winner = 0
            elif p1_health > p0_health:
                winner = 1
            else:
                return {"winner": None, "condition": "draw", "description": "Turn limit reached - draw"}
            
            return {
                "winner": winner,
                "condition": "turn_limit",
                "description": f"Turn limit reached - Player {winner} wins with {self.players[str(winner)].health} health"
            }
        
        return None
    
    def get_player_view(self, team: int) -> Dict[str, Any]:
        """Get game state from a specific player's perspective"""
        player_state = self.players[str(team)]
        opponent_state = self.players[str(1 - team)]
        
        return {
            "match_id": self.match_id,
            "turn": self.turn,
            "phase": self.phase.value,
            "current_player": self.current_player,
            "your_turn": self.current_player == team,
            "sequence": self.sequence,
            "timer": self.timer,
            "play_window": self.play_window,
            "arena": asdict(self.arena),
            "you": asdict(player_state),
            "opponent": {
                "player_id": opponent_state.player_id,
                "team": opponent_state.team,
                "health": opponent_state.health,
                "energy": opponent_state.energy,
                "mana": opponent_state.mana,
                "hero": opponent_state.hero,
                "hand_size": len(opponent_state.hand),
                "arsenal_size": len(opponent_state.arsenal),
                "equipment": opponent_state.equipment,
                "battlefield": opponent_state.battlefield,
                "graveyard_size": len(opponent_state.graveyard)
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert complete game state to dictionary"""
        return {
            "match_id": self.match_id,
            "seed": self.seed,
            "status": self.status,
            "turn": self.turn,
            "phase": self.phase.value,
            "current_player": self.current_player,
            "sequence": self.sequence,
            "rules": self.rules,
            "arena": asdict(self.arena),
            "players": {k: asdict(v) for k, v in self.players.items()},
            "timer": self.timer,
            "play_window": self.play_window,
            "history": self.history[-10:]  # Last 10 actions only
        }
    
    def update_timer(self, delta_ms: int):
        """Update timer state"""
        self.timer["remaining_ms"] -= delta_ms
        
        if self.play_window["active"]:
            self.play_window["remaining_ms"] -= delta_ms
            if self.play_window["remaining_ms"] <= 0:
                self.play_window["active"] = False
