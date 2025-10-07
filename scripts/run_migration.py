#!/usr/bin/env python3
"""
Simple script to run database migrations
"""

import os
import sys
from sqlalchemy import text

# Add shared modules to path
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal

def run_migration(migration_file):
    """Run a SQL migration file"""
    try:
        # Use existing database connection
        with SessionLocal() as session:
            # Read migration file
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute migration using SQLAlchemy
            session.execute(text(sql))
            session.commit()
            
            print(f"✅ Migration {migration_file} executed successfully")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
    else:
        migration_file = "migrations/add_featured_products_with_images.sql"
    
    if os.path.exists(migration_file):
        run_migration(migration_file)
    else:
        print(f"Migration file {migration_file} not found")
