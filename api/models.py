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
from sqlalchemy.orm import relationship
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
    password_hash = Column(String(255))
    elo_rating = Column(Integer, nullable=False, default=1000)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    consoles = relationship(back_populates="owner_player")
    player_cards = relationship(back_populates="player")


class Console(Base):
    __tablename__ = "consoles"

    id = Column(Integer, primary_key=True)
    device_uid = Column(String(128), unique=True, nullable=False, index=True)
    public_key_pem = Column(Textpublic_key_pem)
    registered_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status: Mapped[ConsoleStatus] = mapped_column(SAEnum(ConsoleStatus), default=ConsoleStatus.pending, nullable=False)
    owner_player_id = Column(ForeignKey("players.id", ondelete="SET NULL"))

    owner_player = relationship(back_populates="consoles")
    login_tokens = relationship(back_populates="console")


class CardCatalog(Base):
    __tablename__ = "card_catalog"
    __table_args__ = (
        UniqueConstraint("product_sku", name="uq_card_catalog_sku"),
        Index("ix_card_catalog_category", "category"),
    )

    id = Column(Integer, primary_key=True)
    product_sku = Column(String(64), nullable=False)
    name = Column(String(160), nullable=False)
    rarity: Mapped[CardRarity] = mapped_column(SAEnum(CardRarity), nullable=False)
    category: Mapped[CardCategory] = mapped_column(SAEnum(CardCategory), nullable=False)
    subtype = Column(String(40))  # e.g., AURA, BOON, CURSE, CHARM
    base_stats: Mapped[Optional[dict]] = mapped_column(JSONB)
    attachment_rules: Mapped[Optional[dict]] = mapped_column(JSONB)
    duration: Mapped[Optional[dict]] = mapped_column(JSONB)  # number of turns or condition
    token_spec: Mapped[Optional[dict]] = mapped_column(JSONB)
    reveal_trigger: Mapped[Optional[dict]] = mapped_column(JSONB)
    display_label = Column(String(40))

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    batches = relationship(back_populates="product")


class CardBatch(Base):
    __tablename__ = "card_batches"

    id = Column(Integer, primary_key=True)
    product_sku: Mapped[str] = mapped_column(ForeignKey("card_catalog.product_sku", ondelete="CASCADE"), nullable=False)
    name = Column(String(160))
    notes = Column(Textnotes)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    product = relationship(back_populates="batches")
    nfc_cards = relationship(back_populates="batch")


class NFCCard(Base):
    __tablename__ = "nfc_cards"
    __table_args__ = (
        UniqueConstraint("ntag_uid", name="uq_nfc_cards_uid"),
        Index("ix_nfc_cards_status", "status"),
        Index("ix_nfc_cards_batch", "batch_id"),
    )

    id = Column(Integer, primary_key=True)
    ntag_uid = Column(String(32), nullable=False)
    product_sku: Mapped[str] = mapped_column(ForeignKey("card_catalog.product_sku", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(ForeignKey("card_batches.id", ondelete="SET NULL"))
    issuer_key_ref = Column(String(128))
    status: Mapped[NFCCardStatus] = mapped_column(SAEnum(NFCCardStatus), default=NFCCardStatus.provisioned, nullable=False)
    activation_code_hash = Column(String(255))

    provisioned_at = Column(DateTime(timezone=True))
    provisioned_by_admin_id = Column(ForeignKey("players.id", ondelete="SET NULL"))
    activated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    batch = relationship(back_populates="nfc_cards")
    owner_links = relationship(back_populates="nfc_card")


class PlayerCard(Base):
    __tablename__ = "player_cards"
    __table_args__ = (
        UniqueConstraint("player_id", "nfc_card_id", name="uq_player_card_unique"),
        Index("ix_player_cards_player", "player_id"),
    )

    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    nfc_card_id = Column(ForeignKey("nfc_cards.id", ondelete="CASCADE"), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    custom_state: Mapped[Optional[dict]] = mapped_column(JSONB)

    player = relationship(back_populates="player_cards")
    nfc_card = relationship(back_populates="owner_links")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (Index("ix_matches_status", "status"),)

    id = Column(Integer, primary_key=True)
    mode = Column(String(32), default="1v1", nullable=False)
    status: Mapped[MatchStatus] = mapped_column(SAEnum(MatchStatus), default=MatchStatus.queued, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

    participants = relationship(back_populates="match", cascade="all, delete-orphan")


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id = Column(Integer, primary_key=True)
    match_id = Column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(ForeignKey("players.id", ondelete="SET NULL"))
    console_id = Column(ForeignKey("consoles.id", ondelete="SET NULL"))
    team: Mapped[Optional[int]] = mapped_column(Integer)  # 0/1 for 1v1
    result: Mapped[ParticipantResult] = mapped_column(SAEnum(ParticipantResult), default=ParticipantResult.none, nullable=False)
    mmr_delta: Mapped[Optional[int]] = mapped_column(Integer)

    match = relationship(back_populates="participants")


class ConsoleUpdate(Base):
    __tablename__ = "console_updates"

    id = Column(Integer, primary_key=True)
    version = Column(String(32), nullable=False)
    platform = Column(String(64), nullable=False)
    artifact_url = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False)
    signature = Column(Text, nullable=False)
    mandatory = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_type = Column(String(16), nullable=False)  # player/console/system/admin
    actor_id: Mapped[Optional[int]] = mapped_column(Integer)
    action = Column(String(64), nullable=False)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class ConsoleLoginToken(Base):
    __tablename__ = "console_login_tokens"
    __table_args__ = (
        Index("ix_console_login_tokens_status", "status"),
        Index("ix_console_login_tokens_expires", "expires_at"),
    )

    id = Column(Integer, primary_key=True)
    console_id = Column(ForeignKey("consoles.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    status: Mapped[LoginTokenStatus] = mapped_column(SAEnum(LoginTokenStatus), default=LoginTokenStatus.pending, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    confirmed_player_id = Column(ForeignKey("players.id", ondelete="SET NULL"))

    console = relationship(back_populates="login_tokens")


class CardTransferOffer(Base):
    __tablename__ = "card_transfer_offers"
    __table_args__ = (
        Index("ix_transfer_offers_status", "status"),
        Index("ix_transfer_offers_expires", "expires_at"),
    )

    id = Column(Integer, primary_key=True)
    nfc_card_id = Column(ForeignKey("nfc_cards.id", ondelete="CASCADE"), nullable=False)
    seller_player_id = Column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status: Mapped[TransferStatus] = mapped_column(SAEnum(TransferStatus), default=TransferStatus.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class MMQueue(Base):
    """Postgres-backed matchmaking queue (MVP, no Redis)."""

    __tablename__ = "mm_queue"
    __table_args__ = (
        Index("ix_mm_queue_mode", "mode"),
        Index("ix_mm_queue_enqueued_at", "enqueued_at"),
    )

    id = Column(Integer, primary_key=True)
    mode = Column(String(32), default="1v1", nullable=False)
    player_id = Column(ForeignKey("players.id", ondelete="SET NULL"))
    console_id = Column(ForeignKey("consoles.id", ondelete="SET NULL"))
    elo = Column(Integer, nullable=False)
    enqueued_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

