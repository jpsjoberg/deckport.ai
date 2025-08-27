#!/usr/bin/env python3
"""
Console Approval Script
Approve a pending console device for testing
"""

import sys
import os
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def approve_console(device_uid: str):
    """Approve a pending console device"""
    try:
        with SessionLocal() as session:
            # Find the console
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            
            if not console:
                logger.error(f"Console with UID {device_uid} not found")
                return False
            
            if console.status == ConsoleStatus.active:
                logger.info(f"Console {device_uid} is already active")
                return True
            
            if console.status != ConsoleStatus.pending:
                logger.error(f"Console {device_uid} has status {console.status}, cannot approve")
                return False
            
            # Approve the console
            console.status = ConsoleStatus.active
            session.commit()
            
            logger.info(f"✅ Console {device_uid} approved successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error approving console: {e}")
        return False

def list_pending_consoles():
    """List all pending consoles"""
    try:
        with SessionLocal() as session:
            pending_consoles = session.query(Console).filter(
                Console.status == ConsoleStatus.pending
            ).all()
            
            if not pending_consoles:
                logger.info("No pending consoles found")
                return
            
            logger.info(f"Found {len(pending_consoles)} pending console(s):")
            for console in pending_consoles:
                logger.info(f"  🔄 {console.device_uid} (registered: {console.registered_at})")
                
    except Exception as e:
        logger.error(f"Error listing consoles: {e}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 approve-console.py list                    # List pending consoles")
        print("  python3 approve-console.py approve <device_uid>    # Approve specific console")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_pending_consoles()
    elif command == "approve" and len(sys.argv) == 3:
        device_uid = sys.argv[2]
        if approve_console(device_uid):
            print(f"✅ Console {device_uid} approved successfully")
        else:
            print(f"❌ Failed to approve console {device_uid}")
    else:
        print("Invalid command. Use 'list' or 'approve <device_uid>'")

if __name__ == "__main__":
    main()
