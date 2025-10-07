#!/usr/bin/env python3
"""
Clear Console Registrations
Removes all console registrations from the database for fresh start
"""

import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleLoginToken, AuditLog
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_console_data():
    """Clear all console-related data from database"""
    
    print("🧹 Clearing Console Registrations")
    print("=" * 40)
    
    try:
        with SessionLocal() as session:
            # Count existing data
            console_count = session.query(Console).count()
            token_count = session.query(ConsoleLoginToken).count()
            
            print(f"📊 Current data:")
            print(f"   Consoles: {console_count}")
            print(f"   Login tokens: {token_count}")
            
            if console_count == 0 and token_count == 0:
                print("✅ Database is already clean - no consoles to remove")
                return True
            
            # Confirm deletion
            print(f"\n⚠️ This will DELETE:")
            print(f"   - {console_count} console registrations")
            print(f"   - {token_count} login tokens")
            print(f"   - Related audit logs")
            
            confirm = input("\nProceed with deletion? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("❌ Deletion cancelled")
                return False
            
            print("\n🗑️ Deleting console data...")
            
            # Delete console login tokens first (foreign key dependency)
            deleted_tokens = session.query(ConsoleLoginToken).delete()
            print(f"✅ Deleted {deleted_tokens} login tokens")
            
            # Delete console-related audit logs
            deleted_logs = session.execute(
                text("DELETE FROM audit_logs WHERE actor_type = 'console'")
            ).rowcount
            print(f"✅ Deleted {deleted_logs} console audit logs")
            
            # Delete consoles
            deleted_consoles = session.query(Console).delete()
            print(f"✅ Deleted {deleted_consoles} console registrations")
            
            # Commit all deletions
            session.commit()
            
            print("\n🎉 Console database cleanup complete!")
            print("✅ All console registrations removed")
            print("✅ All login tokens cleared")
            print("✅ Console audit logs cleaned")
            print("\nYou can now deploy consoles fresh from scratch.")
            
            return True
            
    except Exception as e:
        logger.error(f"Error clearing console data: {e}")
        print(f"❌ Error clearing console data: {e}")
        return False

def reset_console_sequences():
    """Reset database sequences for console tables"""
    try:
        with SessionLocal() as session:
            # Reset console ID sequence
            session.execute(text("ALTER SEQUENCE consoles_id_seq RESTART WITH 1"))
            session.execute(text("ALTER SEQUENCE console_login_tokens_id_seq RESTART WITH 1"))
            session.commit()
            
            print("🔄 Database sequences reset to start from 1")
            return True
            
    except Exception as e:
        logger.error(f"Error resetting sequences: {e}")
        print(f"⚠️ Could not reset sequences: {e}")
        return False

def main():
    """Main function"""
    print("🎮 Deckport Console Database Cleanup")
    print("=" * 50)
    
    # Clear console data
    if clear_console_data():
        # Reset sequences for clean IDs
        reset_console_sequences()
        
        print("\n" + "=" * 50)
        print("✅ Console database cleanup complete!")
        print("🚀 Ready for fresh console deployments")
        print("=" * 50)
        
        return True
    else:
        print("\n❌ Console cleanup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
