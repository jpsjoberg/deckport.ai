#!/usr/bin/env python3
"""
Update Match Schema
Adds missing fields to matches and match_participants tables
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_matches_table():
    """Add missing fields to matches table"""
    logger.info("Updating matches table...")
    
    try:
        with engine.connect() as conn:
            # Add arena_id column
            try:
                conn.execute(text("""
                    ALTER TABLE matches 
                    ADD COLUMN arena_id INTEGER REFERENCES arenas(id) ON DELETE SET NULL
                """))
                logger.info("✅ Added arena_id column to matches table")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ arena_id column already exists")
                else:
                    raise e
            
            # Add ended_at column
            try:
                conn.execute(text("""
                    ALTER TABLE matches 
                    ADD COLUMN ended_at TIMESTAMP WITH TIME ZONE
                """))
                logger.info("✅ Added ended_at column to matches table")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ ended_at column already exists")
                else:
                    raise e
            
            # Add winner_team column
            try:
                conn.execute(text("""
                    ALTER TABLE matches 
                    ADD COLUMN winner_team INTEGER
                """))
                logger.info("✅ Added winner_team column to matches table")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ winner_team column already exists")
                else:
                    raise e
            
            # Add end_reason column
            try:
                conn.execute(text("""
                    ALTER TABLE matches 
                    ADD COLUMN end_reason VARCHAR(100)
                """))
                logger.info("✅ Added end_reason column to matches table")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ end_reason column already exists")
                else:
                    raise e
            
            # Make console_id nullable
            try:
                conn.execute(text("""
                    ALTER TABLE matches 
                    ALTER COLUMN console_id DROP NOT NULL
                """))
                logger.info("✅ Made console_id nullable in matches table")
            except Exception as e:
                logger.info(f"⚠️ console_id constraint update: {e}")
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Error updating matches table: {e}")
        return False
    
    return True

def update_match_participants_table():
    """Add missing fields to match_participants table"""
    logger.info("Updating match_participants table...")
    
    try:
        with engine.connect() as conn:
            # Add console_id column
            try:
                conn.execute(text("""
                    ALTER TABLE match_participants 
                    ADD COLUMN console_id INTEGER REFERENCES consoles(id) ON DELETE CASCADE
                """))
                logger.info("✅ Added console_id column to match_participants table")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ console_id column already exists")
                else:
                    raise e
            
            # Add team column
            try:
                conn.execute(text("""
                    ALTER TABLE match_participants 
                    ADD COLUMN team INTEGER
                """))
                logger.info("✅ Added team column to match_participants table")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ team column already exists")
                else:
                    raise e
            
            # Make player_id nullable
            try:
                conn.execute(text("""
                    ALTER TABLE match_participants 
                    ALTER COLUMN player_id DROP NOT NULL
                """))
                logger.info("✅ Made player_id nullable in match_participants table")
            except Exception as e:
                logger.info(f"⚠️ player_id constraint update: {e}")
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Error updating match_participants table: {e}")
        return False
    
    return True

def add_match_status_values():
    """Add new match status values"""
    logger.info("Adding new match status values...")
    
    try:
        with engine.connect() as conn:
            # Add 'completed' status to the enum
            try:
                conn.execute(text("""
                    ALTER TYPE matchstatus ADD VALUE 'completed'
                """))
                logger.info("✅ Added 'completed' status to matchstatus enum")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info("⚠️ 'completed' status already exists")
                else:
                    logger.info(f"⚠️ Status enum update: {e}")
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Error updating match status enum: {e}")
        return False
    
    return True

def main():
    """Main function to update match schema"""
    logger.info("🔄 Updating Match Schema")
    logger.info("=" * 40)
    
    # Step 1: Update matches table
    if not update_matches_table():
        logger.error("Failed to update matches table")
        return False
    
    # Step 2: Update match_participants table
    if not update_match_participants_table():
        logger.error("Failed to update match_participants table")
        return False
    
    # Step 3: Add new match status values
    if not add_match_status_values():
        logger.error("Failed to update match status enum")
        return False
    
    logger.info("🎉 Match schema update complete!")
    logger.info("=" * 40)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
