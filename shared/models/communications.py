"""
Communications System Models
Handles announcements, email campaigns, and social media integration
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Enums ---

class AnnouncementType(str, Enum):
    info = "info"
    warning = "warning"
    success = "success"
    error = "error"
    maintenance = "maintenance"


class AnnouncementPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class AnnouncementStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    expired = "expired"
    archived = "archived"


class CampaignStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    sending = "sending"
    sent = "sent"
    paused = "paused"
    cancelled = "cancelled"


class RecipientType(str, Enum):
    all_players = "all_players"
    active_players = "active_players"
    new_players = "new_players"
    premium_players = "premium_players"
    inactive_players = "inactive_players"
    custom_segment = "custom_segment"


class CommunicationChannel(str, Enum):
    in_app = "in_app"
    email = "email"
    discord = "discord"
    telegram = "telegram"
    push_notification = "push_notification"


# --- Models ---

class Announcement(Base):
    """System announcements and notifications"""
    __tablename__ = "announcements"
    __table_args__ = (
        Index("ix_announcements_status", "status"),
        Index("ix_announcements_type", "type"),
        Index("ix_announcements_created", "created_at"),
        Index("ix_announcements_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[AnnouncementType] = mapped_column(SAEnum(AnnouncementType), nullable=False)
    priority: Mapped[AnnouncementPriority] = mapped_column(SAEnum(AnnouncementPriority), default=AnnouncementPriority.normal, nullable=False)
    
    # Targeting
    target_audience: Mapped[str] = mapped_column(String(50), default="all", nullable=False)
    channels: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # List of CommunicationChannel values
    
    # Status and timing
    status: Mapped[AnnouncementStatus] = mapped_column(SAEnum(AnnouncementStatus), default=AnnouncementStatus.draft, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Additional data
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    created_by_admin: Mapped["Admin"] = relationship()


class EmailCampaign(Base):
    """Email marketing campaigns"""
    __tablename__ = "email_campaigns"
    __table_args__ = (
        Index("ix_email_campaigns_status", "status"),
        Index("ix_email_campaigns_created", "created_at"),
        Index("ix_email_campaigns_scheduled", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Campaign details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text)
    
    # Recipients
    recipient_type: Mapped[RecipientType] = mapped_column(SAEnum(RecipientType), nullable=False)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    custom_segment_query: Mapped[Optional[str]] = mapped_column(Text)  # SQL query for custom segments
    
    # Status and timing
    status: Mapped[CampaignStatus] = mapped_column(SAEnum(CampaignStatus), default=CampaignStatus.draft, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Analytics
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bounce_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unsubscribe_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Configuration
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Email provider settings, templates, etc.
    
    # Relationships
    created_by_admin: Mapped["Admin"] = relationship()
    email_logs: Mapped[List["EmailLog"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


class EmailLog(Base):
    """Individual email delivery logs"""
    __tablename__ = "email_logs"
    __table_args__ = (
        Index("ix_email_logs_campaign", "campaign_id"),
        Index("ix_email_logs_player", "player_id"),
        Index("ix_email_logs_status", "status"),
        Index("ix_email_logs_sent", "sent_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # References
    campaign_id: Mapped[int] = mapped_column(ForeignKey("email_campaigns.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Email details
    email_address: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # sent, delivered, opened, clicked, bounced, unsubscribed
    
    # Timing
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Provider data
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(200))
    provider_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    campaign: Mapped["EmailCampaign"] = relationship(back_populates="email_logs")
    player: Mapped["Player"] = relationship()


class SocialMediaPost(Base):
    """Social media posts and integration"""
    __tablename__ = "social_media_posts"
    __table_args__ = (
        Index("ix_social_media_posts_platform", "platform"),
        Index("ix_social_media_posts_status", "status"),
        Index("ix_social_media_posts_created", "created_at"),
        Index("ix_social_media_posts_scheduled", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # discord, telegram, twitter, etc.
    media_urls: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)  # draft, scheduled, posted, failed
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Platform-specific data
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(200))
    platform_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Analytics (platform-specific)
    engagement_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # likes, shares, comments, etc.
    
    # Relationships
    created_by_admin: Mapped["Admin"] = relationship()


class CommunicationTemplate(Base):
    """Reusable communication templates"""
    __tablename__ = "communication_templates"
    __table_args__ = (
        Index("ix_communication_templates_type", "template_type"),
        Index("ix_communication_templates_category", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Template details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)  # email, announcement, social
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # welcome, tournament, maintenance, etc.
    
    # Content
    subject_template: Mapped[Optional[str]] = mapped_column(String(300))
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[Optional[str]] = mapped_column(Text)
    
    # Configuration
    variables: Mapped[Optional[List[str]]] = mapped_column(JSON)  # Available template variables
    default_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    created_by_admin: Mapped["Admin"] = relationship()
