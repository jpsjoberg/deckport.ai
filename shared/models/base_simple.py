"""
Simple SQLAlchemy 1.4 compatible models for testing
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    elo_rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    
    # Account status and moderation
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, default="active")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Ban tracking (quick access fields)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ban_reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Warning system
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_warning_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Security tracking
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failed_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    account_locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Profile completeness
    profile_completion_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Preferences and settings
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    privacy_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(20), default="admin", nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
