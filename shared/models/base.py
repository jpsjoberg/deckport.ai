"""
Modern SQLAlchemy 2.0+ database models for Deckport.ai
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
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Enums ---

class ConsoleStatus(str, Enum):
    active = "active"
    revoked = "revoked"
    pending = "pending"


class CardRarity(str, Enum):
    common = "COMMON"
    rare = "RARE"
    epic = "EPIC"
    legendary = "LEGENDARY"


class CardCategory(str, Enum):
    creature = "CREATURE"
    structure = "STRUCTURE"
    action_fast = "ACTION_FAST"
    action_slow = "ACTION_SLOW"
    special = "SPECIAL"
    equipment = "EQUIPMENT"
    enchantment = "ENCHANTMENT"
    artifact = "ARTIFACT"
    ritual = "RITUAL"
    trap = "TRAP"
    summon = "SUMMON"
    terrain = "TERRAIN"
    objective = "OBJECTIVE"
    hero = "HERO"
    legendary_creature = "LEGENDARY_CREATURE"
    legendary_artifact = "LEGENDARY_ARTIFACT"
    token = "TOKEN"
    consumable = "CONSUMABLE"
    vehicle = "VEHICLE"
    planeswalker = "PLANESWALKER"


class NFCCardStatus(str, Enum):
    provisioned = "provisioned"
    sold = "sold"
    activated = "activated"
    revoked = "revoked"


class MatchStatus(str, Enum):
    queued = "queued"
    active = "active"
    finished = "finished"
    completed = "completed"
    cancelled = "cancelled"


class TransferStatus(str, Enum):
    pending = "pending"
    cancelled = "cancelled"
    claimed = "claimed"


class ParticipantResult(str, Enum):
    none = "none"
    win = "win"
    loss = "loss"
    draw = "draw"


class LoginTokenStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    expired = "expired"


class ArenaTheme(str, Enum):
    nature = "nature"
    crystal = "crystal"
    shadow = "shadow"
    divine = "divine"
    fire = "fire"
    ice = "ice"
    tech = "tech"
    cosmic = "cosmic"
    underwater = "underwater"
    desert = "desert"


class ArenaRarity(str, Enum):
    common = "common"
    uncommon = "uncommon"
    rare = "rare"
    epic = "epic"
    legendary = "legendary"


class VideoStreamType(str, Enum):
    battle_stream = "battle_stream"
    admin_surveillance = "admin_surveillance"
    console_monitoring = "console_monitoring"


class VideoStreamStatus(str, Enum):
    starting = "starting"
    active = "active"
    paused = "paused"
    ended = "ended"
    failed = "failed"


class VideoCallParticipantRole(str, Enum):
    player = "player"
    admin = "admin"
    observer = "observer"


# --- Models ---

class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    elo_rating: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    
    # Account status and moderation
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, suspended, banned, etc.
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
    profile_completion_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    
    # Preferences and settings
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    privacy_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    consoles: Mapped[List["Console"]] = relationship(back_populates="owner_player")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin", nullable=False)  # AdminRole enum value
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    initiated_streams: Mapped[List["VideoStream"]] = relationship(back_populates="initiated_by_admin")


class Console(Base):
    __tablename__ = "consoles"
    __table_args__ = (
        UniqueConstraint("device_uid", name="uq_consoles_device_uid"),
        Index("ix_consoles_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    public_key_pem: Mapped[Optional[str]] = mapped_column(Text)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    status: Mapped[ConsoleStatus] = mapped_column(SAEnum(ConsoleStatus), default=ConsoleStatus.pending, nullable=False)
    owner_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    current_arena_id: Mapped[Optional[int]] = mapped_column(ForeignKey("arenas.id", ondelete="SET NULL"))

    # Relationships
    owner_player: Mapped[Optional["Player"]] = relationship(back_populates="consoles")
    login_tokens: Mapped[List["ConsoleLoginToken"]] = relationship(back_populates="console")
    # Note: Arena relationship defined in arena.py to avoid circular imports


class CardCatalog(Base):
    __tablename__ = "card_catalog"
    __table_args__ = (
        UniqueConstraint("product_sku", name="uq_card_catalog_sku"),
        Index("ix_card_catalog_category", "category"),
        Index("ix_card_catalog_frame_type", "frame_type"),
        Index("ix_card_catalog_has_animation", "has_animation"),
        Index("ix_card_catalog_card_set", "card_set_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    rarity: Mapped[CardRarity] = mapped_column(SAEnum(CardRarity), nullable=False)
    category: Mapped[CardCategory] = mapped_column(SAEnum(CardCategory), nullable=False)
    subtype: Mapped[Optional[str]] = mapped_column(String(40))
    base_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    attachment_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    duration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    token_spec: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    flavor_text: Mapped[Optional[str]] = mapped_column(Text)
    rules_text: Mapped[Optional[str]] = mapped_column(Text)
    artwork_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Enhanced fields for video and frame system
    frame_type: Mapped[Optional[str]] = mapped_column(String(100))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    static_url: Mapped[Optional[str]] = mapped_column(String(500))
    has_animation: Mapped[bool] = mapped_column(Boolean, default=False)
    frame_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)
    asset_quality_levels: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=lambda: ['low', 'medium', 'high'])
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text)
    video_prompt: Mapped[Optional[str]] = mapped_column(Text)
    frame_style: Mapped[Optional[str]] = mapped_column(String(50), default='standard')
    mana_colors: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    action_speed: Mapped[Optional[str]] = mapped_column(String(20))
    card_set_id: Mapped[str] = mapped_column(String(50), default='open_portal')
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    nfc_cards: Mapped[List["NFCCard"]] = relationship(back_populates="card_template")
    player_cards: Mapped[List["PlayerCard"]] = relationship(back_populates="card_template")
    assets: Mapped[List["CardAsset"]] = relationship(back_populates="card", cascade="all, delete-orphan")


class NFCCard(Base):
    __tablename__ = "nfc_cards"
    __table_args__ = (
        UniqueConstraint("nfc_uid", name="uq_nfc_cards_uid"),
        Index("ix_nfc_cards_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfc_uid: Mapped[str] = mapped_column(String(32), nullable=False)
    card_template_id: Mapped[int] = mapped_column(ForeignKey("card_catalog.id"), nullable=False)
    status: Mapped[NFCCardStatus] = mapped_column(SAEnum(NFCCardStatus), default=NFCCardStatus.provisioned, nullable=False)
    owner_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    card_template: Mapped["CardCatalog"] = relationship(back_populates="nfc_cards")
    owner_player: Mapped[Optional["Player"]] = relationship()


class PlayerCard(Base):
    __tablename__ = "player_cards"
    __table_args__ = (
        UniqueConstraint("player_id", "card_template_id", name="uq_player_cards_player_template"),
        Index("ix_player_cards_player", "player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    card_template_id: Mapped[int] = mapped_column(ForeignKey("card_catalog.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    player: Mapped["Player"] = relationship()
    card_template: Mapped["CardCatalog"] = relationship(back_populates="player_cards")


class CardAsset(Base):
    __tablename__ = "card_assets"
    __table_args__ = (
        UniqueConstraint("card_catalog_id", "asset_type", "quality_level", name="uq_card_assets_card_type_quality"),
        Index("ix_card_assets_card_id", "card_catalog_id"),
        Index("ix_card_assets_type", "asset_type"),
        Index("ix_card_assets_quality", "quality_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_catalog_id: Mapped[int] = mapped_column(ForeignKey("card_catalog.id", ondelete="CASCADE"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'static', 'video', 'frame', 'composite', 'thumbnail'
    quality_level: Mapped[str] = mapped_column(String(20), nullable=False)  # 'low', 'medium', 'high', 'print'
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)  # For video assets
    format: Mapped[Optional[str]] = mapped_column(String(20))  # PNG, JPG, MP4, WEBM, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    card: Mapped["CardCatalog"] = relationship(back_populates="assets")


class FrameType(Base):
    __tablename__ = "frame_types"
    __table_args__ = (
        UniqueConstraint("frame_code", name="uq_frame_types_code"),
        Index("ix_frame_types_category", "category"),
        Index("ix_frame_types_rarity", "rarity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    frame_code: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False)
    mana_color: Mapped[Optional[str]] = mapped_column(String(20))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CardGenerationQueue(Base):
    __tablename__ = "card_generation_queue"
    __table_args__ = (
        Index("ix_generation_queue_status", "status"),
        Index("ix_generation_queue_priority", "priority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_catalog_id: Mapped[int] = mapped_column(ForeignKey("card_catalog.id", ondelete="CASCADE"), nullable=False)
    generation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'art', 'video', 'frame', 'composite', 'all'
    priority: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    card: Mapped["CardCatalog"] = relationship()


class ConsoleLoginToken(Base):
    __tablename__ = "console_login_tokens"
    __table_args__ = (
        UniqueConstraint("token", name="uq_console_login_tokens_token"),
        Index("ix_console_login_tokens_status", "status"),
        Index("ix_console_login_tokens_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), nullable=False)
    console_id: Mapped[int] = mapped_column(ForeignKey("consoles.id", ondelete="CASCADE"), nullable=False)
    qr_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[LoginTokenStatus] = mapped_column(SAEnum(LoginTokenStatus), default=LoginTokenStatus.pending, nullable=False)
    confirmed_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    console: Mapped["Console"] = relationship(back_populates="login_tokens")
    confirmed_player: Mapped[Optional["Player"]] = relationship()


class VideoStream(Base):
    __tablename__ = "video_streams"
    __table_args__ = (
        Index("ix_video_streams_status", "status"),
        Index("ix_video_streams_type", "stream_type"),
        Index("ix_video_streams_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # Unique stream identifier
    stream_type: Mapped[VideoStreamType] = mapped_column(SAEnum(VideoStreamType), nullable=False)
    status: Mapped[VideoStreamStatus] = mapped_column(SAEnum(VideoStreamStatus), default=VideoStreamStatus.starting, nullable=False)
    
    # Stream configuration
    title: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_recording: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recording_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Technical details
    stream_url: Mapped[Optional[str]] = mapped_column(String(500))
    rtmp_key: Mapped[Optional[str]] = mapped_column(String(100))
    quality_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Security and monitoring
    initiated_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    security_flags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Security incidents, warnings
    stream_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Additional stream data
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    initiated_by_admin: Mapped[Optional["Admin"]] = relationship(back_populates="initiated_streams")
    participants: Mapped[List["VideoStreamParticipant"]] = relationship(back_populates="stream", cascade="all, delete-orphan")
    logs: Mapped[List["VideoStreamLog"]] = relationship(back_populates="stream", cascade="all, delete-orphan")


class VideoStreamParticipant(Base):
    __tablename__ = "video_stream_participants"
    __table_args__ = (
        Index("ix_video_stream_participants_stream", "stream_id"),
        Index("ix_video_stream_participants_console", "console_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_id: Mapped[int] = mapped_column(ForeignKey("video_streams.id", ondelete="CASCADE"), nullable=False)
    console_id: Mapped[Optional[int]] = mapped_column(ForeignKey("consoles.id", ondelete="CASCADE"))
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    
    role: Mapped[VideoCallParticipantRole] = mapped_column(SAEnum(VideoCallParticipantRole), nullable=False)
    
    # Participation details
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_camera_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_screen_sharing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_audio_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Technical info
    connection_quality: Mapped[Optional[str]] = mapped_column(String(20))  # excellent, good, poor, failed
    bandwidth_usage_mb: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    stream: Mapped["VideoStream"] = relationship(back_populates="participants")
    console: Mapped[Optional["Console"]] = relationship()
    player: Mapped[Optional["Player"]] = relationship()
    admin: Mapped[Optional["Admin"]] = relationship()


class VideoStreamLog(Base):
    __tablename__ = "video_stream_logs"
    __table_args__ = (
        Index("ix_video_stream_logs_stream", "stream_id"),
        Index("ix_video_stream_logs_timestamp", "timestamp"),
        Index("ix_video_stream_logs_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_id: Mapped[int] = mapped_column(ForeignKey("video_streams.id", ondelete="CASCADE"), nullable=False)
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # join, leave, quality_change, security_alert, etc.
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info, warning, error, critical
    
    # Context
    participant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("video_stream_participants.id", ondelete="SET NULL"))
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    
    # Technical data
    technical_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Quality metrics, error codes, etc.
    security_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Security-related information
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    stream: Mapped["VideoStream"] = relationship(back_populates="logs")
    participant: Mapped[Optional["VideoStreamParticipant"]] = relationship()
    admin: Mapped[Optional["Admin"]] = relationship()


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_status", "status"),
        Index("ix_matches_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    console_id: Mapped[Optional[int]] = mapped_column(ForeignKey("consoles.id"))
    arena_id: Mapped[Optional[int]] = mapped_column(ForeignKey("arenas.id"))
    status: Mapped[MatchStatus] = mapped_column(SAEnum(MatchStatus), default=MatchStatus.queued, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # Keep for compatibility
    winner_team: Mapped[Optional[int]] = mapped_column(Integer)
    end_reason: Mapped[Optional[str]] = mapped_column(String(100))
    match_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # Relationships
    console: Mapped[Optional["Console"]] = relationship()
    participants: Mapped[List["MatchParticipant"]] = relationship(back_populates="match")


class MatchParticipant(Base):
    __tablename__ = "match_participants"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_participants_match_player"),
        Index("ix_match_participants_match", "match_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    console_id: Mapped[Optional[int]] = mapped_column(ForeignKey("consoles.id", ondelete="CASCADE"))
    team: Mapped[Optional[int]] = mapped_column(Integer)
    result: Mapped[ParticipantResult] = mapped_column(SAEnum(ParticipantResult), default=ParticipantResult.none, nullable=False)
    elo_change: Mapped[Optional[int]] = mapped_column(Integer)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    match: Mapped["Match"] = relationship(back_populates="participants")
    player: Mapped[Optional["Player"]] = relationship()
    console: Mapped[Optional["Console"]] = relationship()


class CardTransfer(Base):
    __tablename__ = "card_transfers"
    __table_args__ = (
        Index("ix_card_transfers_status", "status"),
        Index("ix_card_transfers_from_player", "from_player_id"),
        Index("ix_card_transfers_to_player", "to_player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    to_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    card_template_id: Mapped[int] = mapped_column(ForeignKey("card_catalog.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[TransferStatus] = mapped_column(SAEnum(TransferStatus), default=TransferStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    from_player: Mapped["Player"] = relationship(foreign_keys=[from_player_id])
    to_player: Mapped["Player"] = relationship(foreign_keys=[to_player_id])
    card_template: Mapped["CardCatalog"] = relationship()


class MMQueue(Base):
    """Postgres-backed matchmaking queue (MVP, no Redis)."""
    __tablename__ = "mm_queue"
    __table_args__ = (
        Index("ix_mm_queue_mode", "mode"),
        Index("ix_mm_queue_enqueued_at", "enqueued_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(32), default="1v1", nullable=False)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    console_id: Mapped[Optional[int]] = mapped_column(ForeignKey("consoles.id", ondelete="SET NULL"))
    elo: Mapped[int] = mapped_column(Integer, nullable=False)
    enqueued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    player: Mapped[Optional["Player"]] = relationship()
    console: Mapped[Optional["Console"]] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_actor", "actor_type", "actor_id"),
        Index("ix_audit_logs_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'player', 'console', 'admin'
    actor_id: Mapped[Optional[int]] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    resource_id: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)