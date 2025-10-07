"""
Card Generation Queue System
Production-ready background job processing for card generation
"""

import os
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    SINGLE_CARD = "single_card"
    BATCH_CARDS = "batch_cards"
    FULL_PRODUCTION = "full_production"

@dataclass
class CardGenerationJob:
    """Card generation job definition"""
    id: str
    job_type: JobType
    status: JobStatus
    config: Dict[str, Any]
    progress: int = 0  # 0-100
    total_cards: int = 0
    processed_cards: int = 0
    successful_cards: int = 0
    failed_cards: int = 0
    error_message: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

class CardGenerationQueue:
    """Background job queue for card generation"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/home/jp/deckport.ai/card_generation_queue.db"
        self.running = False
        self.worker_thread = None
        self.progress_callbacks: List[Callable[[CardGenerationJob], None]] = []
        
        # Initialize database
        self._init_database()
        
        # Import database processor
        from .card_database_processor import get_card_database_processor, DatabaseProcessingConfig
        self.get_database_processor = get_card_database_processor
        self.DatabaseProcessingConfig = DatabaseProcessingConfig
    
    def _init_database(self):
        """Initialize SQLite database for job queue"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS generation_jobs (
                        id TEXT PRIMARY KEY,
                        job_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        config TEXT NOT NULL,
                        progress INTEGER DEFAULT 0,
                        total_cards INTEGER DEFAULT 0,
                        processed_cards INTEGER DEFAULT 0,
                        successful_cards INTEGER DEFAULT 0,
                        failed_cards INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT
                    )
                """)
                conn.commit()
                
            logger.info(f"Queue database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize queue database: {e}")
            raise
    
    def start_worker(self):
        """Start background worker thread"""
        if self.running:
            logger.warning("Queue worker already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Queue worker started")
    
    def stop_worker(self):
        """Stop background worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        logger.info("Queue worker stopped")
    
    def add_job(self, job_type: JobType, config: Dict[str, Any]) -> str:
        """Add a new job to the queue"""
        try:
            job_id = f"{job_type.value}_{int(time.time())}_{os.getpid()}"
            
            job = CardGenerationJob(
                id=job_id,
                job_type=job_type,
                status=JobStatus.PENDING,
                config=config
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO generation_jobs 
                    (id, job_type, status, config, progress, total_cards, processed_cards, 
                     successful_cards, failed_cards, error_message, created_at, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.id, job.job_type.value, job.status.value, json.dumps(job.config),
                    job.progress, job.total_cards, job.processed_cards, job.successful_cards,
                    job.failed_cards, job.error_message, job.created_at.isoformat(),
                    None, None
                ))
                conn.commit()
            
            logger.info(f"Added job to queue: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to add job to queue: {e}")
            raise
    
    def get_job(self, job_id: str) -> Optional[CardGenerationJob]:
        """Get job by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return self._row_to_job(row)
                
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    def get_all_jobs(self, limit: int = 50) -> List[CardGenerationJob]:
        """Get all jobs, most recent first"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM generation_jobs ORDER BY created_at DESC LIMIT ?", 
                    (limit,)
                )
                rows = cursor.fetchall()
                
                return [self._row_to_job(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
            return []
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE generation_jobs SET status = ? WHERE id = ? AND status = ?",
                    (JobStatus.CANCELLED.value, job_id, JobStatus.PENDING.value)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Cancelled job: {job_id}")
                    return True
                else:
                    logger.warning(f"Could not cancel job {job_id} (not pending)")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def add_progress_callback(self, callback: Callable[[CardGenerationJob], None]):
        """Add callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _worker_loop(self):
        """Main worker loop"""
        logger.info("Queue worker loop started")
        
        while self.running:
            try:
                # Get next pending job
                job = self._get_next_pending_job()
                
                if job:
                    self._process_job(job)
                else:
                    # No jobs, sleep briefly
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)  # Wait longer on error
        
        logger.info("Queue worker loop ended")
    
    def _get_next_pending_job(self) -> Optional[CardGenerationJob]:
        """Get the next pending job from the queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM generation_jobs WHERE status = ? ORDER BY created_at ASC LIMIT 1",
                    (JobStatus.PENDING.value,)
                )
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_job(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get next pending job: {e}")
            return None
    
    def _process_job(self, job: CardGenerationJob):
        """Process a single job"""
        try:
            logger.info(f"Processing job: {job.id}")
            
            # Update job status to processing
            self._update_job_status(job.id, JobStatus.PROCESSING, started_at=datetime.now(timezone.utc))
            
            # Process based on job type
            if job.job_type == JobType.SINGLE_CARD:
                self._process_single_card_job(job)
            elif job.job_type == JobType.BATCH_CARDS:
                self._process_batch_cards_job(job)
            elif job.job_type == JobType.FULL_PRODUCTION:
                self._process_full_production_job(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            # Mark as completed
            self._update_job_status(job.id, JobStatus.COMPLETED, completed_at=datetime.now(timezone.utc))
            logger.info(f"Job completed: {job.id}")
            
        except Exception as e:
            logger.error(f"Job processing failed {job.id}: {e}")
            self._update_job_status(job.id, JobStatus.FAILED, error_message=str(e), 
                                  completed_at=datetime.now(timezone.utc))
    
    def _process_single_card_job(self, job: CardGenerationJob):
        """Process single card generation job"""
        config = job.config
        card_id = config.get('card_id')
        
        if not card_id:
            raise ValueError("Card ID required for single card job")
        
        # Create database processor config
        db_config = self.DatabaseProcessingConfig(
            max_workers=1,
            generate_videos=config.get('generate_videos', False),
            generate_thumbnails=config.get('generate_thumbnails', True),
            quality_checks=config.get('quality_checks', True),
            skip_existing_assets=config.get('skip_existing_assets', True)
        )
        
        processor = self.get_database_processor(db_config)
        
        # Update progress
        self._update_job_progress(job.id, total_cards=1, processed_cards=0)
        
        # Process the card
        result = processor.process_single_card(card_id)
        
        # Update final progress
        if result.success:
            self._update_job_progress(job.id, processed_cards=1, successful_cards=1)
        else:
            self._update_job_progress(job.id, processed_cards=1, failed_cards=1)
            if result.errors:
                raise ValueError(f"Card processing failed: {result.errors}")
    
    def _process_batch_cards_job(self, job: CardGenerationJob):
        """Process batch card generation job using database"""
        config = job.config
        
        # Create database processor config
        db_config = self.DatabaseProcessingConfig(
            max_workers=config.get('max_workers', 4),
            generate_videos=config.get('generate_videos', False),
            generate_thumbnails=config.get('generate_thumbnails', True),
            quality_checks=config.get('quality_checks', True),
            comfyui_timeout=config.get('comfyui_timeout', 300),
            skip_existing_assets=config.get('skip_existing_assets', True)
        )
        
        processor = self.get_database_processor(db_config)
        
        start_index = config.get('start_index', 0)
        end_index = config.get('end_index', None)
        
        # Progress callback to update job status
        def progress_callback(current, total, card_name):
            progress_percent = int((current / total) * 100) if total > 0 else 0
            self._update_job_progress(
                job.id,
                processed_cards=current,
                progress=progress_percent
            )
        
        # Process cards from database
        results = processor.process_all_cards_with_prompts(
            start_index=start_index,
            end_index=end_index,
            progress_callback=progress_callback
        )
        
        # Update final statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self._update_job_progress(
            job.id,
            processed_cards=len(results),
            successful_cards=successful,
            failed_cards=failed,
            progress=100
        )
    
    def _process_full_production_job(self, job: CardGenerationJob):
        """Process full production job (all cards with prompts)"""
        config = job.config
        config['start_index'] = 0
        config['end_index'] = None  # Process all cards
        
        # Use batch processing logic
        self._process_batch_cards_job(job)
    
    def _update_job_status(self, job_id: str, status: JobStatus, error_message: str = None,
                          started_at: datetime = None, completed_at: datetime = None):
        """Update job status in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                updates = ["status = ?"]
                params = [status.value]
                
                if error_message is not None:
                    updates.append("error_message = ?")
                    params.append(error_message)
                
                if started_at is not None:
                    updates.append("started_at = ?")
                    params.append(started_at.isoformat())
                
                if completed_at is not None:
                    updates.append("completed_at = ?")
                    params.append(completed_at.isoformat())
                
                params.append(job_id)
                
                conn.execute(
                    f"UPDATE generation_jobs SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                conn.commit()
                
                # Notify callbacks
                job = self.get_job(job_id)
                if job:
                    for callback in self.progress_callbacks:
                        try:
                            callback(job)
                        except Exception as e:
                            logger.error(f"Progress callback error: {e}")
                
        except Exception as e:
            logger.error(f"Failed to update job status {job_id}: {e}")
    
    def _update_job_progress(self, job_id: str, total_cards: int = None, processed_cards: int = None,
                            successful_cards: int = None, failed_cards: int = None, progress: int = None):
        """Update job progress in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                updates = []
                params = []
                
                if total_cards is not None:
                    updates.append("total_cards = ?")
                    params.append(total_cards)
                
                if processed_cards is not None:
                    updates.append("processed_cards = ?")
                    params.append(processed_cards)
                
                if successful_cards is not None:
                    updates.append("successful_cards = ?")
                    params.append(successful_cards)
                
                if failed_cards is not None:
                    updates.append("failed_cards = ?")
                    params.append(failed_cards)
                
                if progress is not None:
                    updates.append("progress = ?")
                    params.append(progress)
                
                if updates:
                    params.append(job_id)
                    conn.execute(
                        f"UPDATE generation_jobs SET {', '.join(updates)} WHERE id = ?",
                        params
                    )
                    conn.commit()
                    
                    # Notify callbacks
                    job = self.get_job(job_id)
                    if job:
                        for callback in self.progress_callbacks:
                            try:
                                callback(job)
                            except Exception as e:
                                logger.error(f"Progress callback error: {e}")
                
        except Exception as e:
            logger.error(f"Failed to update job progress {job_id}: {e}")
    
    def _row_to_job(self, row) -> CardGenerationJob:
        """Convert database row to CardGenerationJob"""
        return CardGenerationJob(
            id=row['id'],
            job_type=JobType(row['job_type']),
            status=JobStatus(row['status']),
            config=json.loads(row['config']),
            progress=row['progress'],
            total_cards=row['total_cards'],
            processed_cards=row['processed_cards'],
            successful_cards=row['successful_cards'],
            failed_cards=row['failed_cards'],
            error_message=row['error_message'],
            created_at=datetime.fromisoformat(row['created_at']),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None
        )


# Global queue instance
_generation_queue = None

def get_card_generation_queue() -> CardGenerationQueue:
    """Get global card generation queue instance"""
    global _generation_queue
    if _generation_queue is None:
        _generation_queue = CardGenerationQueue()
        _generation_queue.start_worker()
    return _generation_queue
