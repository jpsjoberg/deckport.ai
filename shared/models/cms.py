"""
Content Management System Models
Models for managing news articles, videos, and other content
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

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


# === ENUMS ===

class ContentStatus(str, Enum):
    """Content publication status"""
    draft = "draft"
    published = "published"
    archived = "archived"
    scheduled = "scheduled"


class ContentType(str, Enum):
    """Type of content"""
    news = "news"
    update = "update"
    tournament = "tournament"
    card_reveal = "card_reveal"
    community = "community"
    developer = "developer"


class VideoType(str, Enum):
    """Type of video content"""
    tutorial = "tutorial"
    gameplay = "gameplay"
    card_reveal = "card_reveal"
    tournament = "tournament"
    developer = "developer"
    community = "community"


class VideoPlatform(str, Enum):
    """Video hosting platform"""
    youtube = "youtube"
    vimeo = "vimeo"
    twitch = "twitch"
    direct = "direct"  # Direct file upload


# === MODELS ===

class NewsArticle(Base):
    """News articles and blog posts"""
    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_news_articles_slug"),
        Index("ix_news_articles_status", "status"),
        Index("ix_news_articles_type", "content_type"),
        Index("ix_news_articles_published", "published_at"),
        Index("ix_news_articles_featured", "is_featured"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(SAEnum(ContentType), nullable=False)
    
    # Media
    featured_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    gallery_images: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Publication
    status: Mapped[ContentStatus] = mapped_column(SAEnum(ContentStatus), default=ContentStatus.draft, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Scheduling
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    author_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Additional data
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    author: Mapped["Admin"] = relationship()


class VideoContent(Base):
    """Video content management"""
    __tablename__ = "video_content"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_video_content_slug"),
        Index("ix_video_content_status", "status"),
        Index("ix_video_content_type", "video_type"),
        Index("ix_video_content_platform", "platform"),
        Index("ix_video_content_published", "published_at"),
        Index("ix_video_content_featured", "is_featured"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    video_type: Mapped[VideoType] = mapped_column(SAEnum(VideoType), nullable=False)
    
    # Video Details
    platform: Mapped[VideoPlatform] = mapped_column(SAEnum(VideoPlatform), nullable=False)
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    embed_code: Mapped[Optional[str]] = mapped_column(Text)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Publication
    status: Mapped[ContentStatus] = mapped_column(SAEnum(ContentStatus), default=ContentStatus.draft, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Scheduling
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    watch_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    author_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Additional data
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    author: Mapped["Admin"] = relationship()


class ContentCategory(Base):
    """Categories for organizing content"""
    __tablename__ = "content_categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_content_categories_slug"),
        Index("ix_content_categories_parent", "parent_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Category info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    icon: Mapped[Optional[str]] = mapped_column(String(50))  # Font Awesome icon class
    
    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("content_categories.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    parent: Mapped[Optional["ContentCategory"]] = relationship(remote_side=[id])
    children: Mapped[List["ContentCategory"]] = relationship(overlaps="parent")


class ContentTag(Base):
    """Tags for content organization"""
    __tablename__ = "content_tags"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_content_tags_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Tag info
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    
    # Usage stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ContentView(Base):
    """Track content views for analytics"""
    __tablename__ = "content_views"
    __table_args__ = (
        Index("ix_content_views_article", "article_id"),
        Index("ix_content_views_video", "video_id"),
        Index("ix_content_views_date", "viewed_at"),
        Index("ix_content_views_ip", "ip_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Content reference (one of these will be set)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("news_articles.id", ondelete="CASCADE"))
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("video_content.id", ondelete="CASCADE"))
    
    # Viewer info
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    referrer: Mapped[Optional[str]] = mapped_column(String(500))
    
    # View details
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)  # For videos
    
    # Relationships
    article: Mapped[Optional["NewsArticle"]] = relationship()
    video: Mapped[Optional["VideoContent"]] = relationship()
    player: Mapped[Optional["Player"]] = relationship()
