"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://deckport_app:N0D3-N0D3-N0D3#M0nk3y33@127.0.0.1:5432/deckport"
)

# Create engine
engine = create_engine(DATABASE_URL, echo=os.getenv("DB_ECHO", "false").lower() == "true")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    from shared.models.base import Base
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables (dev/test only)"""
    from shared.models.base import Base
    Base.metadata.drop_all(bind=engine)
