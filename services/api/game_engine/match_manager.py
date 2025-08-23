"""
Match Manager
Handles match lifecycle, creation, and coordination
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Match, MatchParticipant, MatchStatus, ParticipantResult, MMQueue
from shared.models.arena import Arena
from shared.utils.logging import setup_logging
from .game_state import GameState

logger = setup_logging("match_manager", "INFO")

class MatchManager:
    """Manages match creation, lifecycle, and coordination"""
    
    def __init__(self):
        self.active_matches: Dict[str, GameState] = {}
        self.match_timers: Dict[str, asyncio.Task] = {}
    
    async def create_match_from_queue(self, queue_entries: List[MMQueue]) -> Optional[Match]:
        """Create a match from matchmaking queue entries"""
        if len(queue_entries) < 2:
            logger.warning("Not enough players to create match")
            return None
        
        try:
            with SessionLocal() as session:
                # Create match record
                match = Match(
                    mode="1v1",
                    status=MatchStatus.queued
                )
                session.add(match)
                session.flush()  # Get match ID
                
                # Add participants
                for i, queue_entry in enumerate(queue_entries[:2]):  # Only take first 2 for 1v1
                    participant = MatchParticipant(
                        match_id=match.id,
                        player_id=queue_entry.player_id,
                        console_id=queue_entry.console_id,
                        team=i
                    )
                    session.add(participant)
                
                # Remove from queue
                for queue_entry in queue_entries[:2]:
                    session.delete(queue_entry)
                
                session.commit()
                
                logger.info(f"Created match {match.id} with {len(queue_entries)} players")
                return match
                
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            return None
    
    async def start_match(self, match_id: int, connection_manager=None) -> Optional[GameState]:
        """Start a match and initialize game state"""
        try:
            with SessionLocal() as session:
                match = session.query(Match).filter(Match.id == match_id).first()
                if not match:
                    logger.error(f"Match {match_id} not found")
                    return None
                
                # Get participants
                participants = session.query(MatchParticipant).filter(
                    MatchParticipant.match_id == match_id
                ).all()
                
                if len(participants) < 2:
                    logger.error(f"Match {match_id} doesn't have enough participants")
                    return None
                
                # Update match status
                match.status = MatchStatus.active
                match.started_at = datetime.now(timezone.utc)
                session.commit()
                
                # Create player data for game state
                players = []
                for participant in participants:
                    players.append({
                        'player_id': participant.player_id,
                        'console_id': participant.console_id,
                        'team': participant.team
                    })
                
                # Get arena data
                arena_data = None
                if match.arena:
                    arena_data = {
                        'name': match.arena.name,
                        'color': match.arena.primary_color,
                        'passive': match.arena.passive_effect
                    }
                
                # Initialize game state
                game_state = GameState(
                    match_id=str(match_id),
                    players=players,
                    arena=arena_data
                )
                
                self.active_matches[str(match_id)] = game_state
                
                # Start match timer
                await self._start_match_timer(str(match_id), connection_manager)
                
                logger.info(f"Started match {match_id}")
                return game_state
                
        except Exception as e:
            logger.error(f"Error starting match {match_id}: {e}")
            return None
    
    async def _start_match_timer(self, match_id: str, connection_manager=None):
        """Start the match timer loop"""
        if match_id in self.match_timers:
            self.match_timers[match_id].cancel()
        
        self.match_timers[match_id] = asyncio.create_task(
            self._timer_loop(match_id, connection_manager)
        )
    
    async def _timer_loop(self, match_id: str, connection_manager=None):
        """Main timer loop for match"""
        try:
            while match_id in self.active_matches:
                game_state = self.active_matches[match_id]
                
                # Update timer
                game_state.update_timer(1000)  # 1 second
                
                # Send timer tick if connection manager available
                if connection_manager:
                    timer_message = {
                        "type": "timer.tick",
                        "match_id": match_id,
                        "server_timestamp": datetime.now(timezone.utc).isoformat(),
                        "phase": game_state.phase.value,
                        "remaining_ms": game_state.timer["remaining_ms"],
                        "play_window": game_state.play_window
                    }
                    await connection_manager.send_to_match(timer_message, match_id)
                
                # Check for phase timeout
                if game_state.timer["remaining_ms"] <= 0:
                    await self._handle_phase_timeout(match_id, connection_manager)
                
                # Check win conditions
                win_result = game_state.check_win_conditions()
                if win_result:
                    await self.end_match(match_id, win_result, connection_manager)
                    break
                
                await asyncio.sleep(1)  # Update every second
                
        except asyncio.CancelledError:
            logger.info(f"Timer cancelled for match {match_id}")
        except Exception as e:
            logger.error(f"Timer error for match {match_id}: {e}")
    
    async def _handle_phase_timeout(self, match_id: str, connection_manager=None):
        """Handle phase timeout - advance to next phase"""
        game_state = self.active_matches.get(match_id)
        if not game_state:
            return
        
        logger.info(f"Phase timeout for match {match_id} - advancing phase")
        
        # Advance phase
        phase_changes = game_state.advance_phase()
        
        # Notify players if connection manager available
        if connection_manager:
            phase_message = {
                "type": "state.apply",
                "match_id": match_id,
                "patch": phase_changes,
                "reason": "phase_timeout"
            }
            await connection_manager.send_to_match(phase_message, match_id)
    
    async def play_card(self, match_id: str, player_team: int, card_id: str, action: str, target: Optional[str] = None, connection_manager=None) -> Dict[str, Any]:
        """Handle card play in a match"""
        game_state = self.active_matches.get(match_id)
        if not game_state:
            raise ValueError("Match not found")
        
        try:
            # Apply card play to game state
            result = game_state.play_card(player_team, card_id, action, target)
            
            # Notify other players if connection manager available
            if connection_manager:
                card_message = {
                    "type": "card.played",
                    "match_id": match_id,
                    "player_team": player_team,
                    "card_id": card_id,
                    "action": action,
                    "target": target,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await connection_manager.send_to_match(card_message, match_id)
            
            logger.info(f"Card played in match {match_id}: {card_id} by team {player_team}")
            return result
            
        except Exception as e:
            logger.error(f"Error playing card in match {match_id}: {e}")
            raise
    
    async def end_match(self, match_id: str, result: Dict[str, Any], connection_manager=None):
        """End a match and update database"""
        logger.info(f"Ending match {match_id}: {result}")
        
        try:
            # Cancel timer
            if match_id in self.match_timers:
                self.match_timers[match_id].cancel()
                del self.match_timers[match_id]
            
            # Remove from active matches
            game_state = self.active_matches.pop(match_id, None)
            
            # Update database
            with SessionLocal() as session:
                match = session.query(Match).filter(Match.id == int(match_id)).first()
                if match:
                    match.status = MatchStatus.finished
                    match.ended_at = datetime.now(timezone.utc)
                    
                    # Update participant results
                    participants = session.query(MatchParticipant).filter(
                        MatchParticipant.match_id == int(match_id)
                    ).all()
                    
                    winner = result.get('winner')
                    for participant in participants:
                        if winner is None:
                            participant.result = ParticipantResult.draw
                        elif participant.team == winner:
                            participant.result = ParticipantResult.win
                        else:
                            participant.result = ParticipantResult.loss
                    
                    session.commit()
            
            # Notify players if connection manager available
            if connection_manager:
                end_message = {
                    "type": "match.end",
                    "match_id": match_id,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await connection_manager.send_to_match(end_message, match_id)
                
                # Clean up match connections
                if hasattr(connection_manager, 'match_connections'):
                    connection_manager.match_connections.pop(match_id, None)
            
            logger.info(f"Match {match_id} ended successfully")
            
        except Exception as e:
            logger.error(f"Error ending match {match_id}: {e}")
    
    def get_match_state(self, match_id: str) -> Optional[GameState]:
        """Get current state of a match"""
        return self.active_matches.get(match_id)
    
    def get_player_view(self, match_id: str, player_team: int) -> Optional[Dict[str, Any]]:
        """Get match state from player's perspective"""
        game_state = self.active_matches.get(match_id)
        if not game_state:
            return None
        
        return game_state.get_player_view(player_team)
    
    def get_active_matches(self) -> List[str]:
        """Get list of active match IDs"""
        return list(self.active_matches.keys())
    
    async def force_advance_phase(self, match_id: str, connection_manager=None) -> bool:
        """Force advance to next phase (admin/debug function)"""
        game_state = self.active_matches.get(match_id)
        if not game_state:
            return False
        
        try:
            phase_changes = game_state.advance_phase()
            
            if connection_manager:
                phase_message = {
                    "type": "state.apply",
                    "match_id": match_id,
                    "patch": phase_changes,
                    "reason": "force_advance"
                }
                await connection_manager.send_to_match(phase_message, match_id)
            
            logger.info(f"Force advanced phase for match {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error force advancing phase for match {match_id}: {e}")
            return False
