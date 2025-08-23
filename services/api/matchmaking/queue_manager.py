"""
Queue Manager
Handles matchmaking queue operations and player matching
"""

import asyncio
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import MMQueue, Player, Console
from shared.utils.logging import setup_logging

logger = setup_logging("queue_manager", "INFO")

class QueueManager:
    """Manages matchmaking queues and player matching"""
    
    def __init__(self, match_manager=None):
        self.match_manager = match_manager
        self.queue_check_interval = 5.0  # Check every 5 seconds
        self.max_elo_difference = 200  # Maximum ELO difference for matching
        self.queue_timeout = 300  # 5 minutes timeout
        self.running = False
        self.queue_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the queue manager"""
        if self.running:
            logger.warning("Queue manager already running")
            return
        
        self.running = True
        self.queue_task = asyncio.create_task(self._queue_processing_loop())
        logger.info("Queue manager started")
    
    async def stop(self):
        """Stop the queue manager"""
        self.running = False
        if self.queue_task:
            self.queue_task.cancel()
            try:
                await self.queue_task
            except asyncio.CancelledError:
                pass
        logger.info("Queue manager stopped")
    
    async def _queue_processing_loop(self):
        """Main queue processing loop"""
        try:
            while self.running:
                await self._process_queues()
                await asyncio.sleep(self.queue_check_interval)
        except asyncio.CancelledError:
            logger.info("Queue processing loop cancelled")
        except Exception as e:
            logger.error(f"Error in queue processing loop: {e}")
    
    async def _process_queues(self):
        """Process all game mode queues"""
        try:
            with SessionLocal() as session:
                # Get all unique game modes in queue
                modes = session.query(MMQueue.mode).distinct().all()
                
                for (mode,) in modes:
                    await self._process_mode_queue(session, mode)
                    
        except Exception as e:
            logger.error(f"Error processing queues: {e}")
    
    async def _process_mode_queue(self, session, mode: str):
        """Process queue for a specific game mode"""
        # Get all players in queue for this mode
        queue_entries = session.query(MMQueue).filter(
            MMQueue.mode == mode
        ).order_by(MMQueue.enqueued_at).all()
        
        if len(queue_entries) < 2:
            return  # Not enough players
        
        # Clean up expired entries
        await self._cleanup_expired_entries(session, queue_entries)
        
        # Refresh after cleanup
        queue_entries = session.query(MMQueue).filter(
            MMQueue.mode == mode
        ).order_by(MMQueue.enqueued_at).all()
        
        if len(queue_entries) < 2:
            return
        
        # Try to find matches
        matches_found = await self._find_matches(session, queue_entries, mode)
        
        if matches_found > 0:
            logger.info(f"Found {matches_found} matches for mode {mode}")
    
    async def _cleanup_expired_entries(self, session, queue_entries: List[MMQueue]):
        """Remove expired queue entries"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.queue_timeout)
        
        expired_count = 0
        for entry in queue_entries:
            if entry.enqueued_at < cutoff_time:
                logger.info(f"Removing expired queue entry for player {entry.player_id}")
                session.delete(entry)
                expired_count += 1
        
        if expired_count > 0:
            session.commit()
            logger.info(f"Removed {expired_count} expired queue entries")
    
    async def _find_matches(self, session, queue_entries: List[MMQueue], mode: str) -> int:
        """Find and create matches from queue entries"""
        matches_created = 0
        used_entries = set()
        
        # For 1v1 mode, match players in pairs
        if mode == "1v1":
            matches_created = await self._find_1v1_matches(session, queue_entries, used_entries)
        
        # Add support for other modes here (2v2, tournament, etc.)
        
        return matches_created
    
    async def _find_1v1_matches(self, session, queue_entries: List[MMQueue], used_entries: set) -> int:
        """Find 1v1 matches"""
        matches_created = 0
        
        for i, player1 in enumerate(queue_entries):
            if player1.id in used_entries:
                continue
            
            # Find best opponent for player1
            best_opponent = None
            best_elo_diff = float('inf')
            
            for j, player2 in enumerate(queue_entries[i+1:], i+1):
                if player2.id in used_entries:
                    continue
                
                # Calculate ELO difference
                elo_diff = abs(player1.elo - player2.elo)
                
                # Check if this is a valid match
                if elo_diff <= self.max_elo_difference and elo_diff < best_elo_diff:
                    best_opponent = player2
                    best_elo_diff = elo_diff
            
            # If we found a good opponent, create match
            if best_opponent:
                match_created = await self._create_match_from_players(
                    session, [player1, best_opponent]
                )
                
                if match_created:
                    used_entries.add(player1.id)
                    used_entries.add(best_opponent.id)
                    matches_created += 1
                    
                    logger.info(f"Created 1v1 match: Player {player1.player_id} (ELO {player1.elo}) vs Player {best_opponent.player_id} (ELO {best_opponent.elo})")
        
        return matches_created
    
    async def _create_match_from_players(self, session, queue_entries: List[MMQueue]) -> bool:
        """Create a match from queue entries"""
        try:
            if not self.match_manager:
                logger.error("No match manager available")
                return False
            
            # Create match using match manager
            match = await self.match_manager.create_match_from_queue(queue_entries)
            
            if match:
                # Remove players from queue (done in match manager)
                logger.info(f"Successfully created match {match.id}")
                return True
            else:
                logger.error("Failed to create match from queue entries")
                return False
                
        except Exception as e:
            logger.error(f"Error creating match from players: {e}")
            return False
    
    def get_queue_stats(self, mode: str = None) -> Dict:
        """Get queue statistics"""
        try:
            with SessionLocal() as session:
                if mode:
                    # Stats for specific mode
                    total_queued = session.query(MMQueue).filter(MMQueue.mode == mode).count()
                    
                    if total_queued > 0:
                        avg_elo = session.query(MMQueue.elo).filter(MMQueue.mode == mode).all()
                        avg_elo = sum(elo[0] for elo in avg_elo) / len(avg_elo)
                        
                        oldest_entry = session.query(MMQueue).filter(
                            MMQueue.mode == mode
                        ).order_by(MMQueue.enqueued_at).first()
                        
                        wait_time = (datetime.now(timezone.utc) - oldest_entry.enqueued_at).total_seconds()
                    else:
                        avg_elo = 0
                        wait_time = 0
                    
                    return {
                        "mode": mode,
                        "total_queued": total_queued,
                        "average_elo": round(avg_elo),
                        "longest_wait_seconds": round(wait_time)
                    }
                else:
                    # Overall stats
                    total_queued = session.query(MMQueue).count()
                    modes = session.query(MMQueue.mode).distinct().all()
                    
                    mode_stats = {}
                    for (mode_name,) in modes:
                        mode_count = session.query(MMQueue).filter(MMQueue.mode == mode_name).count()
                        mode_stats[mode_name] = mode_count
                    
                    return {
                        "total_queued": total_queued,
                        "modes": mode_stats
                    }
                    
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"error": str(e)}
    
    def get_player_queue_info(self, player_id: int, mode: str) -> Optional[Dict]:
        """Get specific player's queue information"""
        try:
            with SessionLocal() as session:
                queue_entry = session.query(MMQueue).filter(
                    MMQueue.player_id == player_id,
                    MMQueue.mode == mode
                ).first()
                
                if not queue_entry:
                    return None
                
                # Calculate position in queue
                position = session.query(MMQueue).filter(
                    MMQueue.mode == mode,
                    MMQueue.enqueued_at <= queue_entry.enqueued_at
                ).count()
                
                # Calculate wait time
                wait_time = (datetime.now(timezone.utc) - queue_entry.enqueued_at).total_seconds()
                
                return {
                    "player_id": player_id,
                    "mode": mode,
                    "position": position,
                    "elo": queue_entry.elo,
                    "enqueued_at": queue_entry.enqueued_at.isoformat(),
                    "wait_time_seconds": round(wait_time)
                }
                
        except Exception as e:
            logger.error(f"Error getting player queue info: {e}")
            return None
    
    async def add_player_to_queue(self, player_id: int, console_id: Optional[int], mode: str, elo: int) -> bool:
        """Add player to matchmaking queue"""
        try:
            with SessionLocal() as session:
                # Check if player is already in queue
                existing = session.query(MMQueue).filter(
                    MMQueue.player_id == player_id,
                    MMQueue.mode == mode
                ).first()
                
                if existing:
                    logger.warning(f"Player {player_id} already in queue for mode {mode}")
                    return False
                
                # Add to queue
                queue_entry = MMQueue(
                    mode=mode,
                    player_id=player_id,
                    console_id=console_id,
                    elo=elo
                )
                
                session.add(queue_entry)
                session.commit()
                
                logger.info(f"Added player {player_id} to {mode} queue (ELO: {elo})")
                return True
                
        except Exception as e:
            logger.error(f"Error adding player to queue: {e}")
            return False
    
    async def remove_player_from_queue(self, player_id: int, mode: str) -> bool:
        """Remove player from matchmaking queue"""
        try:
            with SessionLocal() as session:
                queue_entry = session.query(MMQueue).filter(
                    MMQueue.player_id == player_id,
                    MMQueue.mode == mode
                ).first()
                
                if queue_entry:
                    session.delete(queue_entry)
                    session.commit()
                    logger.info(f"Removed player {player_id} from {mode} queue")
                    return True
                else:
                    logger.warning(f"Player {player_id} not found in {mode} queue")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing player from queue: {e}")
            return False
    
    def set_match_manager(self, match_manager):
        """Set the match manager reference"""
        self.match_manager = match_manager
        logger.info("Match manager reference set")
    
    def configure(self, **kwargs):
        """Configure queue manager settings"""
        if 'check_interval' in kwargs:
            self.queue_check_interval = kwargs['check_interval']
        if 'max_elo_difference' in kwargs:
            self.max_elo_difference = kwargs['max_elo_difference']
        if 'queue_timeout' in kwargs:
            self.queue_timeout = kwargs['queue_timeout']
        
        logger.info(f"Queue manager configured: interval={self.queue_check_interval}s, max_elo_diff={self.max_elo_difference}, timeout={self.queue_timeout}s")
