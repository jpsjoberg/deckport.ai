"""
Modern SQLAlchemy 2.0+ database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://deckport_app:N0D3-N0D3-N0D3#M0nk3y33@127.0.0.1:5432/deckport"
)

# Create engine with SQLAlchemy 2.0+ configuration
engine = create_engine(
    DATABASE_URL, 
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    future=True  # Enable SQLAlchemy 2.0 mode
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False
)

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
