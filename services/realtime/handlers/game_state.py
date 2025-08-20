"""
Game State Handler
Manages real-time game state synchronization and match events
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Match, MatchParticipant, MatchStatus, ParticipantResult
from shared.utils.logging import setup_logging
from protocols.game_protocol import GameProtocol, MessageType

logger = setup_logging("game_state", "INFO")

class GameStateHandler:
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self.protocol = GameProtocol()
        self.active_matches: Dict[str, Dict] = {}  # match_id -> game_state
        self.match_timers: Dict[str, asyncio.Task] = {}  # match_id -> timer_task
    
    async def handle_message(self, message: Dict, connection_id: str, user_info: Dict):
        """Handle game state related messages"""
        msg_type = message.get('type')
        user_id = user_info.get('user_id')
        
        if msg_type == MessageType.MATCH_READY.value:
            await self._handle_match_ready(message, connection_id, user_id)
        elif msg_type == MessageType.STATE_UPDATE.value:
            await self._handle_state_update(message, connection_id, user_id)
        elif msg_type == MessageType.CARD_PLAY.value:
            await self._handle_card_play(message, connection_id, user_id)
        elif msg_type == MessageType.SYNC_REQUEST.value:
            await self._handle_sync_request(message, connection_id, user_id)
        else:
            await self.manager.send_personal_message(
                self.protocol.create_error("unknown_message", f"Unknown game message: {msg_type}"),
                connection_id
            )
    
    async def _handle_match_ready(self, message: Dict, connection_id: str, user_id: int):
        """Handle player ready for match"""
        match_id = message.get('match_id')
        
        if not match_id:
            await self.manager.send_personal_message(
                self.protocol.create_error("missing_match_id", "Match ID required"),
                connection_id
            )
            return
        
        logger.info(f"Player {user_id} ready for match {match_id}")
        
        try:
            with SessionLocal() as session:
                # Verify player is in this match
                participant = session.query(MatchParticipant).filter(
                    MatchParticipant.match_id == int(match_id),
                    MatchParticipant.player_id == user_id
                ).first()
                
                if not participant:
                    await self.manager.send_personal_message(
                        self.protocol.create_error("not_in_match", "Not a participant in this match"),
                        connection_id
                    )
                    return
                
                # Add player to match connections
                if match_id not in self.manager.match_connections:
                    self.manager.match_connections[match_id] = []
                
                if connection_id not in self.manager.match_connections[match_id]:
                    self.manager.match_connections[match_id].append(connection_id)
                
                # Check if all players are ready
                match_connections = self.manager.match_connections.get(match_id, [])
                
                # Get all participants
                all_participants = session.query(MatchParticipant).filter(
                    MatchParticipant.match_id == int(match_id)
                ).all()
                
                if len(match_connections) >= len(all_participants):
                    # All players ready - start match
                    await self._start_match(match_id, session)
                else:
                    # Send ready acknowledgment
                    await self.manager.send_personal_message(
                        self.protocol.create_message("match.ready_ack", {
                            "match_id": match_id,
                            "ready_players": len(match_connections),
                            "total_players": len(all_participants)
                        }),
                        connection_id
                    )
                
        except Exception as e:
            logger.error(f"Error handling match ready: {e}")
            await self.manager.send_personal_message(
                self.protocol.create_error("match_error", "Failed to process ready status"),
                connection_id
            )
    
    async def _start_match(self, match_id: str, session):
        """Start a match when all players are ready"""
        logger.info(f"Starting match {match_id}")
        
        try:
            # Update match status
            match = session.query(Match).filter(Match.id == int(match_id)).first()
            if match:
                match.status = MatchStatus.active
                match.started_at = datetime.now(timezone.utc)
                session.commit()
            
            # Initialize game state
            initial_state = self._create_initial_game_state(match_id)
            self.active_matches[match_id] = initial_state
            
            # Send match start to all players
            start_message = self.protocol.create_message(MessageType.MATCH_START, {
                "match_id": match_id,
                "seed": initial_state["seed"],
                "rules": initial_state["rules"],
                "arena": initial_state["arena"],
                "players": initial_state["players"]
            })
            
            await self.manager.send_to_match(start_message, match_id)
            
            # Start match timer
            await self._start_match_timer(match_id)
            
            logger.info(f"Match {match_id} started successfully")
            
        except Exception as e:
            logger.error(f"Error starting match: {e}")
    
    def _create_initial_game_state(self, match_id: str) -> Dict:
        """Create initial game state for a new match"""
        import random
        
        # Generate random seed for reproducible randomness
        seed = random.randint(1000000, 9999999)
        
        # Create initial game state
        initial_state = {
            "match_id": match_id,
            "seed": seed,
            "status": "active",
            "turn": 1,
            "phase": "start",
            "current_player": 0,  # Team 0 starts
            "rules": {
                "turn_time_seconds": 60,
                "play_window_seconds": 10,
                "max_turns": 20
            },
            "arena": {
                "name": "Sunspire Plateau",
                "color": "RADIANT",
                "passive": "first_match_card_discount"
            },
            "players": {
                "0": {
                    "energy": 0,
                    "mana": {},
                    "hero": None,
                    "hand": [],
                    "arsenal": [],
                    "equipment": [],
                    "health": 20
                },
                "1": {
                    "energy": 0,
                    "mana": {},
                    "hero": None,
                    "hand": [],
                    "arsenal": [],
                    "equipment": [],
                    "health": 20
                }
            },
            "timer": {
                "phase_start": datetime.now(timezone.utc).isoformat(),
                "remaining_ms": 60000
            }
        }
        
        return initial_state
    
    async def _start_match_timer(self, match_id: str):
        """Start timer for match phases"""
        if match_id in self.match_timers:
            self.match_timers[match_id].cancel()
        
        self.match_timers[match_id] = asyncio.create_task(self._timer_loop(match_id))
    
    async def _timer_loop(self, match_id: str):
        """Timer loop for match phases"""
        try:
            while match_id in self.active_matches:
                game_state = self.active_matches[match_id]
                
                # Send timer tick
                timer_message = self.protocol.create_message(MessageType.TIMER_TICK, {
                    "match_id": match_id,
                    "server_timestamp": datetime.now(timezone.utc).isoformat(),
                    "phase": game_state["phase"],
                    "remaining_ms": game_state["timer"]["remaining_ms"]
                })
                
                await self.manager.send_to_match(timer_message, match_id)
                
                # Update timer
                game_state["timer"]["remaining_ms"] -= 1000
                
                # Check if time expired
                if game_state["timer"]["remaining_ms"] <= 0:
                    await self._handle_phase_timeout(match_id)
                
                await asyncio.sleep(1)  # Update every second
                
        except asyncio.CancelledError:
            logger.info(f"Timer cancelled for match {match_id}")
        except Exception as e:
            logger.error(f"Timer error for match {match_id}: {e}")
    
    async def _handle_phase_timeout(self, match_id: str):
        """Handle phase timeout"""
        logger.info(f"Phase timeout for match {match_id}")
        
        # TODO: Implement phase transition logic
        # For MVP, just advance to next phase
        
        game_state = self.active_matches.get(match_id)
        if not game_state:
            return
        
        current_phase = game_state["phase"]
        
        # Simple phase progression for MVP
        phase_order = ["start", "main", "attack", "end"]
        current_index = phase_order.index(current_phase) if current_phase in phase_order else 0
        next_index = (current_index + 1) % len(phase_order)
        
        # If back to start, advance turn
        if next_index == 0:
            game_state["turn"] += 1
            game_state["current_player"] = 1 - game_state["current_player"]  # Switch players
        
        game_state["phase"] = phase_order[next_index]
        game_state["timer"]["remaining_ms"] = 60000  # Reset timer
        
        # Notify players of phase change
        phase_message = self.protocol.create_message(MessageType.STATE_APPLY, {
            "match_id": match_id,
            "patch": {
                "turn": game_state["turn"],
                "phase": game_state["phase"],
                "current_player": game_state["current_player"]
            }
        })
        
        await self.manager.send_to_match(phase_message, match_id)
    
    async def _handle_state_update(self, message: Dict, connection_id: str, user_id: int):
        """Handle game state update from player"""
        match_id = message.get('match_id')
        delta = message.get('delta', {})
        
        if not match_id or not delta:
            await self.manager.send_personal_message(
                self.protocol.create_error("invalid_update", "Match ID and delta required"),
                connection_id
            )
            return
        
        logger.info(f"State update from player {user_id} in match {match_id}")
        
        # TODO: Validate state update and apply to game state
        # For MVP, just broadcast to other players
        
        update_message = self.protocol.create_message(MessageType.STATE_APPLY, {
            "match_id": match_id,
            "patch": delta,
            "from_player": user_id
        })
        
        await self.manager.send_to_match(update_message, match_id)
    
    async def _handle_card_play(self, message: Dict, connection_id: str, user_id: int):
        """Handle card play action"""
        match_id = message.get('match_id')
        card_id = message.get('card_id')
        action = message.get('action')
        
        if not all([match_id, card_id, action]):
            await self.manager.send_personal_message(
                self.protocol.create_error("invalid_card_play", "Match ID, card ID, and action required"),
                connection_id
            )
            return
        
        logger.info(f"Card play from player {user_id}: {action} card {card_id} in match {match_id}")
        
        # TODO: Validate card play and update game state
        # For MVP, just notify other players
        
        card_message = self.protocol.create_message("card.played", {
            "match_id": match_id,
            "player_id": user_id,
            "card_id": card_id,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        await self.manager.send_to_match(card_message, match_id)
    
    async def _handle_sync_request(self, message: Dict, connection_id: str, user_id: int):
        """Handle request for game state synchronization"""
        match_id = message.get('match_id')
        
        if not match_id:
            await self.manager.send_personal_message(
                self.protocol.create_error("missing_match_id", "Match ID required"),
                connection_id
            )
            return
        
        # Send current game state
        game_state = self.active_matches.get(match_id)
        if game_state:
            sync_message = self.protocol.create_message(MessageType.SYNC_SNAPSHOT, {
                "match_id": match_id,
                "seq": game_state.get("sequence", 0),
                "full_state": game_state
            })
            
            await self.manager.send_personal_message(sync_message, connection_id)
        else:
            await self.manager.send_personal_message(
                self.protocol.create_error("match_not_found", "Match not found or not active"),
                connection_id
            )
    
    async def end_match(self, match_id: str, result: Dict):
        """End a match and clean up"""
        logger.info(f"Ending match {match_id}")
        
        try:
            # Cancel timer
            if match_id in self.match_timers:
                self.match_timers[match_id].cancel()
                del self.match_timers[match_id]
            
            # Remove from active matches
            if match_id in self.active_matches:
                del self.active_matches[match_id]
            
            # Update database
            with SessionLocal() as session:
                match = session.query(Match).filter(Match.id == int(match_id)).first()
                if match:
                    match.status = MatchStatus.finished
                    match.ended_at = datetime.now(timezone.utc)
                    session.commit()
            
            # Notify players
            end_message = self.protocol.create_message(MessageType.MATCH_END, {
                "match_id": match_id,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            await self.manager.send_to_match(end_message, match_id)
            
            # Clean up match connections
            if match_id in self.manager.match_connections:
                del self.manager.match_connections[match_id]
            
            logger.info(f"Match {match_id} ended successfully")
            
        except Exception as e:
            logger.error(f"Error ending match {match_id}: {e}")
    
    def get_match_state(self, match_id: str) -> Optional[Dict]:
        """Get current state of a match"""
        return self.active_matches.get(match_id)
    
    def get_active_matches(self) -> List[str]:
        """Get list of active match IDs"""
        return list(self.active_matches.keys())
