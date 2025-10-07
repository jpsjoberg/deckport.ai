#!/usr/bin/env python3

import os
import sys
import urllib.parse

# Add the project root to Python path
sys.path.insert(0, '/home/jp/deckport.ai')

# Set up database connection
password = 'N0D3-N0D3-N0D3#M0nk3y33'
encoded_password = urllib.parse.quote(password, safe='')
os.environ['DATABASE_URL'] = f'postgresql+psycopg://deckport_app:{encoded_password}@127.0.0.1:5432/deckport'

try:
    from shared.database.connection import engine
    from sqlalchemy import text

    print('🔍 Checking existing database structure...')

    with engine.begin() as conn:
        # List all tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f'📊 Existing tables ({len(tables)}):')
        for table in tables:
            print(f'  - {table}')
        
        print()
        
        # Check card_catalog structure if it exists
        if 'card_catalog' in tables:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'card_catalog' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print(f'🎴 card_catalog columns ({len(columns)}):')
            for col in columns:
                print(f'  - {col[0]} ({col[1]}) - nullable: {col[2]}')
            
            # Check if we have any cards
            result = conn.execute(text('SELECT COUNT(*) FROM card_catalog'))
            card_count = result.scalar()
            print(f'📈 Total cards in catalog: {card_count}')
            
            # Check categories
            result = conn.execute(text('SELECT DISTINCT category FROM card_catalog ORDER BY category'))
            categories = [row[0] for row in result.fetchall()]
            print(f'🏷️  Existing categories: {categories}')
        
        # Check if enhanced columns already exist
        if 'card_catalog' in tables:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'card_catalog' 
                AND column_name IN ('frame_type', 'video_url', 'has_animation', 'card_set_id')
            """))
            enhanced_cols = [row[0] for row in result.fetchall()]
            if enhanced_cols:
                print(f'✅ Enhanced columns already exist: {enhanced_cols}')
            else:
                print('❌ Enhanced columns not found - migration needed')
        
        # Check if card_assets table exists
        if 'card_assets' in tables:
            result = conn.execute(text('SELECT COUNT(*) FROM card_assets'))
            asset_count = result.scalar()
            print(f'🎨 Total card assets: {asset_count}')
        else:
            print('❌ card_assets table not found - needs creation')

except Exception as e:
    print(f'❌ Database check failed: {e}')
    import traceback
    traceback.print_exc()
