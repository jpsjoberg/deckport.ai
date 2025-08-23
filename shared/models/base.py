from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy import Column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


Base = declarative_base()


# --- Enums (code-facing, display labels live in content/clients) ---


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
    creature = "CREATURE"  # display: Denizen
    structure = "STRUCTURE"  # display: Bastion
    action_fast = "ACTION_FAST"  # display: Instant
    action_slow = "ACTION_SLOW"  # display: Sorcery
    special = "SPECIAL"  # display: Planar
    equipment = "EQUIPMENT"  # display: Relic
    enchantment = "ENCHANTMENT"  # display: Sigil
    artifact = "ARTIFACT"  # display: Artifact
    ritual = "RITUAL"  # display: Rite
    trap = "TRAP"  # display: Ward
    summon = "SUMMON"  # display: Conjuration
    terrain = "TERRAIN"  # display: Realm
    objective = "OBJECTIVE"  # display: Quest


class NFCCardStatus(str, Enum):
    provisioned = "provisioned"
    sold = "sold"
    activated = "activated"
    revoked = "revoked"


class MatchStatus(str, Enum):
    queued = "queued"
    active = "active"
    finished = "finished"
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


# --- Models ---


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False)
    display_name = Column(String(120))
    username = Column(String(50), unique=True, nullable=True)
    phone_number = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    password_hash = Column(String(255))
    elo_rating = Column(Integer, nullable=False, default=1000)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    consoles = relationship("Console", back_populates="owner_player")
    player_cards = relationship("PlayerCard", back_populates="player")


class Console(Base):
    __tablename__ = "consoles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    public_key_pem: Mapped[Optional[str]] = mapped_column(Text)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    status: Mapped[ConsoleStatus] = mapped_column(SAEnum(ConsoleStatus), default=ConsoleStatus.pending, nullable=False)
    owner_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))

    owner_player: Mapped[Optional[Player]] = relationship(back_populates="consoles")
    login_tokens: Mapped[List[ConsoleLoginToken]] = relationship(back_populates="console")


class CardCatalog(Base):
    __tablename__ = "card_catalog"
    __table_args__ = (
        UniqueConstraint("product_sku", name="uq_card_catalog_sku"),
        Index("ix_card_catalog_category", "category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    rarity: Mapped[CardRarity] = mapped_column(SAEnum(CardRarity), nullable=False)
    category: Mapped[CardCategory] = mapped_column(SAEnum(CardCategory), nullable=False)
    subtype: Mapped[Optional[str]] = mapped_column(String(40))  # e.g., AURA, BOON, CURSE, CHARM
    base_stats: Mapped[Optional[dict]] = mapped_column(JSONB)
    attachment_rules: Mapped[Optional[dict]] = mapped_column(JSONB)
    duration: Mapped[Optional[dict]] = mapped_column(JSONB)  # number of turns or condition
    token_spec: Mapped[Optional[dict]] = mapped_column(JSONB)
    reveal_trigger: Mapped[Optional[dict]] = mapped_column(JSONB)
    display_label: Mapped[Optional[str]] = mapped_column(String(40))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    batches: Mapped[List[CardBatch]] = relationship(back_populates="product")


class CardBatch(Base):
    __tablename__ = "card_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_sku: Mapped[str] = mapped_column(ForeignKey("card_catalog.product_sku", ondelete="CASCADE"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(160))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    product: Mapped[CardCatalog] = relationship(back_populates="batches")
    nfc_cards: Mapped[List[NFCCard]] = relationship(back_populates="batch")


class NFCCard(Base):
    __tablename__ = "nfc_cards"
    __table_args__ = (
        UniqueConstraint("ntag_uid", name="uq_nfc_cards_uid"),
        Index("ix_nfc_cards_status", "status"),
        Index("ix_nfc_cards_batch", "batch_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ntag_uid: Mapped[str] = mapped_column(String(32), nullable=False)
    product_sku: Mapped[str] = mapped_column(ForeignKey("card_catalog.product_sku", ondelete="RESTRICT"), nullable=False)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_batches.id", ondelete="SET NULL"))
    issuer_key_ref: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[NFCCardStatus] = mapped_column(SAEnum(NFCCardStatus), default=NFCCardStatus.provisioned, nullable=False)
    activation_code_hash: Mapped[Optional[str]] = mapped_column(String(255))

    provisioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    provisioned_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    batch: Mapped[Optional[CardBatch]] = relationship(back_populates="nfc_cards")
    owner_links: Mapped[List[PlayerCard]] = relationship(back_populates="nfc_card")


class PlayerCard(Base):
    __tablename__ = "player_cards"
    __table_args__ = (
        UniqueConstraint("player_id", "nfc_card_id", name="uq_player_card_unique"),
        Index("ix_player_cards_player", "player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    nfc_card_id: Mapped[int] = mapped_column(ForeignKey("nfc_cards.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    custom_state: Mapped[Optional[dict]] = mapped_column(JSONB)

    player: Mapped[Player] = relationship(back_populates="player_cards")
    nfc_card: Mapped[NFCCard] = relationship(back_populates="owner_links")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (Index("ix_matches_status", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mode: Mapped[str] = mapped_column(String(32), default="1v1", nullable=False)
    status: Mapped[MatchStatus] = mapped_column(SAEnum(MatchStatus), default=MatchStatus.queued, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    participants: Mapped[List[MatchParticipant]] = relationship(back_populates="match", cascade="all, delete-orphan")


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    console_id: Mapped[Optional[int]] = mapped_column(ForeignKey("consoles.id", ondelete="SET NULL"))
    team: Mapped[Optional[int]] = mapped_column(Integer)  # 0/1 for 1v1
    result: Mapped[ParticipantResult] = mapped_column(SAEnum(ParticipantResult), default=ParticipantResult.none, nullable=False)
    mmr_delta: Mapped[Optional[int]] = mapped_column(Integer)

    match: Mapped[Match] = relationship(back_populates="participants")


class ConsoleUpdate(Base):
    __tablename__ = "console_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_url: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)  # player/console/system/admin
    actor_id: Mapped[Optional[int]] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ConsoleLoginToken(Base):
    __tablename__ = "console_login_tokens"
    __table_args__ = (
        Index("ix_console_login_tokens_status", "status"),
        Index("ix_console_login_tokens_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    console_id: Mapped[int] = mapped_column(ForeignKey("consoles.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[LoginTokenStatus] = mapped_column(SAEnum(LoginTokenStatus), default=LoginTokenStatus.pending, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    confirmed_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))

    console: Mapped[Console] = relationship(back_populates="login_tokens")


class CardTransferOffer(Base):
    __tablename__ = "card_transfer_offers"
    __table_args__ = (
        Index("ix_transfer_offers_status", "status"),
        Index("ix_transfer_offers_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfc_card_id: Mapped[int] = mapped_column(ForeignKey("nfc_cards.id", ondelete="CASCADE"), nullable=False)
    seller_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[TransferStatus] = mapped_column(SAEnum(TransferStatus), default=TransferStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


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

