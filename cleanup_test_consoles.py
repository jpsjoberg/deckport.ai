#!/usr/bin/env python3
"""
Script to remove all test consoles from the database
"""
import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleLoginToken
from shared.models.arena import Arena
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_test_consoles():
    """Remove all test consoles and related data"""
    try:
        with SessionLocal() as session:
            # Get count before deletion
            console_count = session.query(Console).count()
            login_token_count = session.query(ConsoleLoginToken).count()
            
            logger.info(f"Found {console_count} consoles and {login_token_count} login tokens")
            
            if console_count == 0:
                logger.info("No consoles to delete")
                return
            
            # Delete console login tokens first (foreign key dependency)
            deleted_tokens = session.query(ConsoleLoginToken).delete()
            logger.info(f"Deleted {deleted_tokens} console login tokens")
            
            # No need to update arenas - consoles reference arenas, not the other way around
            # The foreign key constraint will handle this automatically
            
            # Delete all consoles
            deleted_consoles = session.query(Console).delete()
            logger.info(f"Deleted {deleted_consoles} consoles")
            
            # Commit the changes
            session.commit()
            
            logger.info("✅ Successfully cleaned up all test consoles")
            
            # Verify deletion
            remaining_consoles = session.query(Console).count()
            remaining_tokens = session.query(ConsoleLoginToken).count()
            
            logger.info(f"Remaining: {remaining_consoles} consoles, {remaining_tokens} login tokens")
            
    except Exception as e:
        logger.error(f"Error cleaning up consoles: {e}")
        raise

if __name__ == "__main__":
    print("🧹 Cleaning up test consoles from database...")
    cleanup_test_consoles()
    print("🎉 Cleanup complete!")
