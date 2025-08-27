#!/usr/bin/env python3
"""
Manual SQLAlchemy 2.0 Model Fixer
Carefully fix the most critical model files for SQLAlchemy 2.0 compatibility
"""

import re

def fix_base_model():
    """Fix the base.py model file manually"""
    
    # Read the current file
    with open('shared/models/base.py', 'r') as f:
        content = f.read()
    
    # Fix imports first
    content = re.sub(
        r'from sqlalchemy\.ext\.declarative import declarative_base\nfrom sqlalchemy\.orm import relationship\nfrom sqlalchemy import Column',
        'from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship',
        content
    )
    
    # Fix Base class
    content = re.sub(
        r'Base = declarative_base\(\)',
        'class Base(DeclarativeBase):\n    pass',
        content
    )
    
    # Fix Player model - convert Column to mapped_column with proper typing
    player_fixes = [
        (r'id = Column\(Integer, primary_key=True\)', 'id: Mapped[int] = mapped_column(Integer, primary_key=True)'),
        (r'email = Column\(String\(320\), unique=True, nullable=False\)', 'email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)'),
        (r'display_name = Column\(String\(120\)\)', 'display_name: Mapped[Optional[str]] = mapped_column(String(120))'),
        (r'username = Column\(String\(50\), unique=True\)', 'username: Mapped[Optional[str]] = mapped_column(String(50), unique=True)'),
        (r'phone_number = Column\(String\(20\)\)', 'phone_number: Mapped[Optional[str]] = mapped_column(String(20))'),
        (r'avatar_url = Column\(String\(500\)\)', 'avatar_url: Mapped[Optional[str]] = mapped_column(String(500))'),
        (r'password_hash = Column\(String\(255\)\)', 'password_hash: Mapped[Optional[str]] = mapped_column(String(255))'),
        (r'elo_rating = Column\(Integer, nullable=False, default=1000\)', 'elo_rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)'),
        
        # Moderation fields
        (r'status = Column\(String\(50\), nullable=False, default="active"\)', 'status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")'),
        (r'is_verified = Column\(Boolean, default=False, nullable=False\)', 'is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)'),
        (r'is_premium = Column\(Boolean, default=False, nullable=False\)', 'is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)'),
        (r'is_banned = Column\(Boolean, default=False, nullable=False\)', 'is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)'),
        (r'ban_expires_at = Column\(DateTime\(timezone=True\)\)', 'ban_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))'),
        (r'ban_reason = Column\(String\(200\)\)', 'ban_reason: Mapped[Optional[str]] = mapped_column(String(200))'),
        (r'warning_count = Column\(Integer, default=0, nullable=False\)', 'warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)'),
        (r'last_warning_at = Column\(DateTime\(timezone=True\)\)', 'last_warning_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))'),
        (r'last_login_at = Column\(DateTime\(timezone=True\)\)', 'last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))'),
        (r'last_login_ip = Column\(String\(45\)\)', 'last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))'),
        (r'login_count = Column\(Integer, default=0, nullable=False\)', 'login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)'),
        (r'failed_login_attempts = Column\(Integer, default=0, nullable=False\)', 'failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)'),
        (r'last_failed_login_at = Column\(DateTime\(timezone=True\)\)', 'last_failed_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))'),
        (r'account_locked_until = Column\(DateTime\(timezone=True\)\)', 'account_locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))'),
        (r'profile_completion_score = Column\(Integer, default=0, nullable=False\)', 'profile_completion_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)'),
        (r'email_notifications = Column\(Boolean, default=True, nullable=False\)', 'email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)'),
        (r'privacy_settings = Column\(JSON\)', 'privacy_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)'),
        (r'created_at = Column\(DateTime\(timezone=True\), default=utcnow, nullable=False\)', 'created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)'),
        (r'updated_at = Column\(DateTime\(timezone=True\), default=utcnow, onupdate=utcnow, nullable=False\)', 'updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)'),
        
        # Relationships
        (r'consoles = relationship\("Console", back_populates="owner_player"\)', 'consoles: Mapped[List["Console"]] = relationship(back_populates="owner_player")'),
        (r'player_cards = relationship\("PlayerCard", back_populates="player"\)', 'player_cards: Mapped[List["PlayerCard"]] = relationship(back_populates="player")'),
    ]
    
    for old, new in player_fixes:
        content = re.sub(old, new, content)
    
    # Write the fixed content
    with open('shared/models/base.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed base.py model")

def fix_player_moderation_model():
    """Fix the player_moderation.py model file"""
    
    with open('shared/models/player_moderation.py', 'r') as f:
        content = f.read()
    
    # Ensure proper imports
    if 'from sqlalchemy.orm import relationship' in content and 'mapped_column' not in content:
        content = re.sub(
            r'from sqlalchemy.orm import relationship',
            'from sqlalchemy.orm import Mapped, mapped_column, relationship',
            content
        )
    
    # Remove any Column import
    content = re.sub(r'from sqlalchemy import Column\n', '', content)
    
    with open('shared/models/player_moderation.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed player_moderation.py model")

def main():
    """Fix the critical model files"""
    print("🔧 Manual SQLAlchemy 2.0 Model Fixer")
    print("=" * 40)
    
    try:
        fix_base_model()
        fix_player_moderation_model()
        print("\n🎉 Critical models fixed for SQLAlchemy 2.0!")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
