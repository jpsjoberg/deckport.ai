"""
Matchmaking Handler
Manages player queue and match pairing
"""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Player, Match, MatchParticipant, MMQueue, MatchStatus, ParticipantResult
from shared.utils.logging import setup_logging
from protocols.game_protocol import GameProtocol, MessageType

logger = setup_logging("matchmaking", "INFO")

class MatchmakingHandler:
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self.protocol = GameProtocol()
        self.queue_polling_task = None
        self._polling_started = False
    
    async def start_queue_polling(self):
        """Start background task to process matchmaking queue"""
        if not self._polling_started and (self.queue_polling_task is None or self.queue_polling_task.done()):
            self.queue_polling_task = asyncio.create_task(self._process_queue_loop())
            self._polling_started = True
            logger.info("Matchmaking queue polling started")
    
    async def handle_message(self, message: Dict, connection_id: str, user_info: Dict):
        """Handle matchmaking-related messages"""
        msg_type = message.get('type')
        user_id = user_info.get('user_id')
        
        if msg_type == MessageType.QUEUE_JOIN.value:
            await self._handle_queue_join(message, connection_id, user_id)
        elif msg_type == MessageType.QUEUE_LEAVE.value:
            await self._handle_queue_leave(message, connection_id, user_id)
        else:
            await self.manager.send_personal_message(
                self.protocol.create_error("unknown_message", f"Unknown matchmaking message: {msg_type}"),
                connection_id
            )
    
    async def _handle_queue_join(self, message: Dict, connection_id: str, user_id: int):
        """Handle player joining matchmaking queue"""
        mode = message.get('mode', '1v1')
        preferred_range = message.get('preferred_range')  # [min_elo, max_elo]
        
        logger.info(f"Player {user_id} joining queue for mode {mode}")
        
        try:
            with SessionLocal() as session:
                # Get player info
                player = session.query(Player).filter(Player.id == user_id).first()
                if not player:
                    await self.manager.send_personal_message(
                        self.protocol.create_error("player_not_found", "Player not found"),
                        connection_id
                    )
                    return
                
                # Check if already in queue
                existing_queue = session.query(MMQueue).filter(MMQueue.player_id == user_id).first()
                if existing_queue:
                    await self.manager.send_personal_message(
                        self.protocol.create_error("already_queued", "Already in matchmaking queue"),
                        connection_id
                    )
                    return
                
                # Add to queue
                queue_entry = MMQueue(
                    mode=mode,
                    player_id=user_id,
                    elo=player.elo_rating
                )
                
                session.add(queue_entry)
                session.commit()
                
                # Send acknowledgment
                await self.manager.send_personal_message(
                    self.protocol.create_message(MessageType.QUEUE_ACK, {
                        "mode": mode,
                        "estimated_wait_seconds": await self._estimate_wait_time(mode, player.elo_rating)
                    }),
                    connection_id
                )
                
                logger.info(f"Player {user_id} added to {mode} queue (ELO: {player.elo_rating})")
                
        except Exception as e:
            logger.error(f"Error joining queue: {e}")
            await self.manager.send_personal_message(
                self.protocol.create_error("queue_error", "Failed to join queue"),
                connection_id
            )
    
    async def _handle_queue_leave(self, message: Dict, connection_id: str, user_id: int):
        """Handle player leaving matchmaking queue"""
        logger.info(f"Player {user_id} leaving queue")
        
        try:
            with SessionLocal() as session:
                # Remove from queue
                removed = session.query(MMQueue).filter(MMQueue.player_id == user_id).delete()
                session.commit()
                
                if removed > 0:
                    await self.manager.send_personal_message(
                        self.protocol.create_message("queue.left", {"removed": True}),
                        connection_id
                    )
                    logger.info(f"Player {user_id} removed from queue")
                else:
                    await self.manager.send_personal_message(
                        self.protocol.create_error("not_in_queue", "Not in matchmaking queue"),
                        connection_id
                    )
                    
        except Exception as e:
            logger.error(f"Error leaving queue: {e}")
            await self.manager.send_personal_message(
                self.protocol.create_error("queue_error", "Failed to leave queue"),
                connection_id
            )
    
    async def _process_queue_loop(self):
        """Background loop to process matchmaking queue"""
        while True:
            try:
                await self._process_queue()
                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _process_queue(self):
        """Process the matchmaking queue and create matches"""
        try:
            with SessionLocal() as session:
                # Get all queued players, ordered by wait time
                queue_entries = session.query(MMQueue).order_by(MMQueue.enqueued_at).all()
                
                if len(queue_entries) < 2:
                    return  # Need at least 2 players
                
                # Simple pairing algorithm for MVP
                # TODO: Implement ELO-based pairing with widening windows
                
                paired_players = []
                i = 0
                while i < len(queue_entries) - 1:
                    player1 = queue_entries[i]
                    player2 = queue_entries[i + 1]
                    
                    # For MVP, just pair any two players
                    # TODO: Add ELO range checking
                    elo_diff = abs(player1.elo - player2.elo)
                    if elo_diff <= 200:  # Simple ELO range for MVP
                        paired_players.append((player1, player2))
                        i += 2  # Skip both players
                    else:
                        i += 1  # Try next pair
                
                # Create matches for paired players
                for player1, player2 in paired_players:
                    await self._create_match(session, player1, player2)
                    
        except Exception as e:
            logger.error(f"Error processing queue: {e}")
    
    async def _create_match(self, session, player1: MMQueue, player2: MMQueue):
        """Create a new match for two players"""
        try:
            # Create match record
            new_match = Match(
                mode=player1.mode,
                status=MatchStatus.queued
            )
            session.add(new_match)
            session.flush()  # Get the match ID
            
            # Create participants
            participant1 = MatchParticipant(
                match_id=new_match.id,
                player_id=player1.player_id,
                console_id=player1.console_id,
                team=0
            )
            
            participant2 = MatchParticipant(
                match_id=new_match.id,
                player_id=player2.player_id,
                console_id=player2.console_id,
                team=1
            )
            
            session.add_all([participant1, participant2])
            
            # Remove from queue
            session.delete(player1)
            session.delete(player2)
            
            session.commit()
            
            # Notify players
            await self._notify_match_found(new_match.id, player1.player_id, player2.player_id)
            
            logger.info(f"Match created: {new_match.id} (Players: {player1.player_id} vs {player2.player_id})")
            
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            session.rollback()
    
    async def _notify_match_found(self, match_id: int, player1_id: int, player2_id: int):
        """Notify players that a match was found"""
        try:
            with SessionLocal() as session:
                # Get player info
                player1 = session.query(Player).filter(Player.id == player1_id).first()
                player2 = session.query(Player).filter(Player.id == player2_id).first()
                
                if not player1 or not player2:
                    logger.error(f"Players not found for match {match_id}")
                    return
                
                # Create match found messages
                message1 = self.protocol.create_message(MessageType.MATCH_FOUND, {
                    "match_id": str(match_id),
                    "opponent": {
                        "id": player2.id,
                        "display_name": player2.display_name,
                        "elo_rating": player2.elo_rating
                    },
                    "your_team": 0,
                    "mode": "1v1"
                })
                
                message2 = self.protocol.create_message(MessageType.MATCH_FOUND, {
                    "match_id": str(match_id),
                    "opponent": {
                        "id": player1.id,
                        "display_name": player1.display_name,
                        "elo_rating": player1.elo_rating
                    },
                    "your_team": 1,
                    "mode": "1v1"
                })
                
                # Send to players
                await self.manager.send_to_user(message1, player1_id)
                await self.manager.send_to_user(message2, player2_id)
                
                logger.info(f"Match found notifications sent for match {match_id}")
                
        except Exception as e:
            logger.error(f"Error notifying match found: {e}")
    
    async def _estimate_wait_time(self, mode: str, elo: int) -> int:
        """Estimate wait time for matchmaking"""
        try:
            with SessionLocal() as session:
                # Count players in queue
                queue_count = session.query(MMQueue).filter(MMQueue.mode == mode).count()
                
                # Simple estimation: 30 seconds per player ahead in queue
                estimated_seconds = max(30, queue_count * 30)
                return min(estimated_seconds, 300)  # Cap at 5 minutes
                
        except Exception:
            return 60  # Default estimate
