"""
Player Moderation System Models for SQLAlchemy 2.0+
Enhanced player ban, warning, and activity tracking system
"""

from __future__ import annotations

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# === ENUMS ===

class PlayerStatus(str, Enum):
    """Player account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING_VERIFICATION = "pending_verification"
    DEACTIVATED = "deactivated"


class BanType(str, Enum):
    """Types of player bans"""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    SHADOW = "shadow"  # Limited functionality but not fully banned


class BanReason(str, Enum):
    """Reasons for player bans"""
    CHEATING = "cheating"
    HARASSMENT = "harassment"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM = "spam"
    TERMS_VIOLATION = "terms_violation"
    PAYMENT_FRAUD = "payment_fraud"
    MULTIPLE_ACCOUNTS = "multiple_accounts"
    ADMIN_DISCRETION = "admin_discretion"


class WarningType(str, Enum):
    """Types of player warnings"""
    MINOR = "minor"
    MAJOR = "major"
    FINAL = "final"


class ActivityType(str, Enum):
    """Player activity types for logging"""
    LOGIN = "login"
    LOGOUT = "logout"
    MATCH_START = "match_start"
    MATCH_END = "match_end"
    CARD_PURCHASE = "card_purchase"
    CARD_TRADE = "card_trade"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
    EMAIL_CHANGE = "email_change"
    PAYMENT_METHOD_ADD = "payment_method_add"
    CONSOLE_REGISTER = "console_register"
    TOURNAMENT_JOIN = "tournament_join"


class PlayerLogLevel(str, Enum):
    """Log levels for player activities"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SecurityEventType(str, Enum):
    """Security event types"""
    FAILED_LOGIN = "failed_login"
    SUSPICIOUS_IP = "suspicious_ip"
    MULTIPLE_DEVICES = "multiple_devices"
    ACCOUNT_TAKEOVER_ATTEMPT = "account_takeover_attempt"
    PAYMENT_FRAUD_ATTEMPT = "payment_fraud_attempt"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"


class PlayerReportStatus(str, Enum):
    """Player report status"""
    PENDING = "pending"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class PlayerReportPriority(str, Enum):
    """Player report priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# === MODELS ===

class PlayerBan(Base):
    """Player ban tracking with appeal system"""
    __tablename__ = "player_bans"
    __table_args__ = (
        Index("ix_player_bans_player", "player_id"),
        Index("ix_player_bans_expires", "expires_at"),
        Index("ix_player_bans_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Ban details
    ban_type: Mapped[BanType] = mapped_column(SAEnum(BanType), nullable=False)
    reason: Mapped[BanReason] = mapped_column(SAEnum(BanReason), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timing
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # NULL for permanent
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Admin tracking
    banned_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    unbanned_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    unbanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    unban_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Appeal system
    appeal_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    appeal_text: Mapped[Optional[str]] = mapped_column(Text)
    appeal_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    appeal_reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    appeal_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    player: Mapped["Player"] = relationship()
    banned_by: Mapped["Admin"] = relationship(foreign_keys=[banned_by_admin_id])
    unbanned_by: Mapped[Optional["Admin"]] = relationship(foreign_keys=[unbanned_by_admin_id])
    appeal_reviewer: Mapped[Optional["Admin"]] = relationship(foreign_keys=[appeal_reviewed_by])


class PlayerWarning(Base):
    """Player warning system"""
    __tablename__ = "player_warnings"
    __table_args__ = (
        Index("ix_player_warnings_player", "player_id"),
        Index("ix_player_warnings_type", "warning_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Warning details
    warning_type: Mapped[WarningType] = mapped_column(SAEnum(WarningType), nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Admin tracking
    issued_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    
    # Escalation tracking
    previous_warning_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player_warnings.id", ondelete="SET NULL"))
    escalated_to_ban: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    player: Mapped["Player"] = relationship()
    issued_by: Mapped["Admin"] = relationship()
    previous_warning: Mapped[Optional["PlayerWarning"]] = relationship(remote_side=[id])


class PlayerActivityLog(Base):
    """Comprehensive player activity logging"""
    __tablename__ = "player_activity_logs"
    __table_args__ = (
        Index("ix_player_activity_logs_player", "player_id"),
        Index("ix_player_activity_logs_activity", "activity_type"),
        Index("ix_player_activity_logs_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Activity details
    activity_type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    session_id: Mapped[Optional[str]] = mapped_column(String(128))
    
    # Metadata
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    log_level: Mapped[PlayerLogLevel] = mapped_column(SAEnum(PlayerLogLevel), default=PlayerLogLevel.INFO, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timing
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    player: Mapped["Player"] = relationship()


class PlayerSecurityLog(Base):
    """Security-focused logging for player accounts"""
    __tablename__ = "player_security_logs"
    __table_args__ = (
        Index("ix_player_security_logs_player", "player_id"),
        Index("ix_player_security_logs_event", "event_type"),
        Index("ix_player_security_logs_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Security event details
    event_type: Mapped[SecurityEventType] = mapped_column(SAEnum(SecurityEventType), nullable=False)
    severity: Mapped[PlayerLogLevel] = mapped_column(SAEnum(PlayerLogLevel), default=PlayerLogLevel.WARNING, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    email_attempted: Mapped[Optional[str]] = mapped_column(String(320))
    
    # Detection
    detection_method: Mapped[str] = mapped_column(String(100), default="automated", nullable=False)
    risk_score: Mapped[Optional[float]] = mapped_column(Float)  # 0.0-1.0 risk assessment
    
    # Response
    action_taken: Mapped[Optional[str]] = mapped_column(String(200))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    event_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Timing
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    player: Mapped["Player"] = relationship()


class PlayerReport(Base):
    """Player reporting system"""
    __tablename__ = "player_reports"
    __table_args__ = (
        Index("ix_player_reports_reported", "reported_player_id"),
        Index("ix_player_reports_reporter", "reporter_player_id"),
        Index("ix_player_reports_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Players involved
    reported_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    reporter_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))  # NULL for anonymous
    
    # Report details
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[Optional[List[str]]] = mapped_column(JSON)  # Screenshots, videos, etc.
    
    # Status tracking
    status: Mapped[PlayerReportStatus] = mapped_column(SAEnum(PlayerReportStatus), default=PlayerReportStatus.PENDING, nullable=False)
    priority: Mapped[PlayerReportPriority] = mapped_column(SAEnum(PlayerReportPriority), default=PlayerReportPriority.MEDIUM, nullable=False)
    
    # Admin handling
    assigned_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    reported_player: Mapped["Player"] = relationship(foreign_keys=[reported_player_id])
    reporter_player: Mapped[Optional["Player"]] = relationship(foreign_keys=[reporter_player_id])
    assigned_admin: Mapped[Optional["Admin"]] = relationship()


# === HELPER FUNCTIONS ===

def log_player_activity(
    player_id: int,
    activity_type: ActivityType,
    description: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[str] = None,
    event_metadata: Optional[Dict[str, Any]] = None,
    log_level: PlayerLogLevel = PlayerLogLevel.INFO,
    success: bool = True,
) -> None:
    """Log player activity"""
    from shared.database.connection import SessionLocal
    
    with SessionLocal() as session:
        activity_log = PlayerActivityLog(
            player_id=player_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            event_metadata=event_metadata,
            log_level=log_level,
            success=success,
        )
        session.add(activity_log)
        session.commit()


def log_security_event(
    player_id: int,
    event_type: SecurityEventType,
    description: str,
    severity: PlayerLogLevel = PlayerLogLevel.WARNING,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    email_attempted: Optional[str] = None,
    detection_method: str = "automated",
    risk_score: Optional[float] = None,
    action_taken: Optional[str] = None,
    event_metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log security event"""
    from shared.database.connection import SessionLocal
    
    with SessionLocal() as session:
        security_log = PlayerSecurityLog(
            player_id=player_id,
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            email_attempted=email_attempted,
            detection_method=detection_method,
            risk_score=risk_score,
            action_taken=action_taken,
            event_metadata=event_metadata,
        )
        session.add(security_log)
        session.commit()