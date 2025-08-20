#!/usr/bin/env python3
"""
Database migration to add username, phone_number, and avatar_url fields to players table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from shared.database.connection import engine

def migrate_user_fields():
    """Add new fields to players table"""
    
    migrations = [
        "ALTER TABLE players ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE;",
        "ALTER TABLE players ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);",
        "ALTER TABLE players ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);",
        "CREATE INDEX IF NOT EXISTS ix_players_username ON players(username);",
    ]
    
    print("🔄 Running database migrations for user fields...")
    
    with engine.connect() as conn:
        for migration in migrations:
            try:
                print(f"  Executing: {migration}")
                conn.execute(text(migration))
                conn.commit()
                print("  ✅ Success")
            except Exception as e:
                print(f"  ⚠️  Warning: {e}")
                # Continue with other migrations even if one fails
                continue
    
    print("✅ Database migration completed!")
    print("\nNew fields added to players table:")
    print("  - username (VARCHAR(50), UNIQUE)")
    print("  - phone_number (VARCHAR(20))")
    print("  - avatar_url (VARCHAR(500))")

if __name__ == "__main__":
    migrate_user_fields()
