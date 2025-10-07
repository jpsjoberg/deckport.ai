#!/usr/bin/env python3
"""
Clean up duplicate console registrations
Keeps only the latest registration and removes duplicates
"""

import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleLoginToken, AuditLog
from sqlalchemy import desc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_duplicate_consoles():
    """Clean up duplicate console registrations"""
    
    print("🧹 Cleaning Up Duplicate Console Registrations")
    print("=" * 50)
    
    try:
        with SessionLocal() as session:
            # Get all consoles ordered by registration time
            all_consoles = session.query(Console).order_by(desc(Console.registered_at)).all()
            
            if len(all_consoles) <= 1:
                print("✅ Only one or no consoles found - nothing to clean")
                return True
            
            print(f"📊 Found {len(all_consoles)} console registrations:")
            for i, console in enumerate(all_consoles):
                print(f"  {i+1}. ID: {console.id}, UID: {console.device_uid}")
                print(f"      Registered: {console.registered_at}")
                print(f"      Status: {console.status}")
                print(f"      MAC: {getattr(console, 'mac_address', 'Unknown')}")
                print(f"      Hostname: {getattr(console, 'hostname', 'Unknown')}")
                print()
            
            # Keep the latest one (first in desc order)
            latest_console = all_consoles[0]
            duplicates = all_consoles[1:]
            
            print(f"✅ Keeping latest console:")
            print(f"   ID: {latest_console.id}, UID: {latest_console.device_uid}")
            print(f"   Registered: {latest_console.registered_at}")
            
            print(f"\n🗑️ Will remove {len(duplicates)} duplicate registrations:")
            for console in duplicates:
                print(f"   ID: {console.id}, UID: {console.device_uid}")
            
            # Confirm deletion
            confirm = input(f"\nProceed with deleting {len(duplicates)} duplicate consoles? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("❌ Cleanup cancelled")
                return False
            
            print(f"\n🗑️ Removing duplicate console registrations...")
            
            # Delete related data for duplicate consoles
            total_deleted_tokens = 0
            total_deleted_logs = 0
            
            for console in duplicates:
                # Delete console login tokens
                deleted_tokens = session.query(ConsoleLoginToken).filter(
                    ConsoleLoginToken.console_id == console.id
                ).delete()
                total_deleted_tokens += deleted_tokens
                
                # Delete audit logs for this console
                deleted_logs = session.query(AuditLog).filter(
                    AuditLog.actor_type == 'console',
                    AuditLog.actor_id == console.id
                ).delete()
                total_deleted_logs += deleted_logs
                
                # Delete the console itself
                session.delete(console)
                
                print(f"   ✅ Deleted console {console.id} ({console.device_uid})")
            
            # Commit all deletions
            session.commit()
            
            print(f"\n🎉 Cleanup complete!")
            print(f"✅ Kept 1 console (latest): {latest_console.device_uid}")
            print(f"✅ Removed {len(duplicates)} duplicate consoles")
            print(f"✅ Removed {total_deleted_tokens} login tokens")
            print(f"✅ Removed {total_deleted_logs} audit log entries")
            
            print(f"\n📊 Final status:")
            print(f"   Console ID: {latest_console.id}")
            print(f"   Device UID: {latest_console.device_uid}")
            print(f"   Status: {latest_console.status}")
            print(f"   Registered: {latest_console.registered_at}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error cleaning up duplicate consoles: {e}")
        print(f"❌ Error during cleanup: {e}")
        return False

def main():
    """Main function"""
    print("🎮 Deckport Console Duplicate Cleanup")
    print("=" * 50)
    
    success = cleanup_duplicate_consoles()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Duplicate console cleanup complete!")
        print("🚀 Ready for fresh console deployment")
        print("=" * 50)
    else:
        print("\n❌ Cleanup failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
