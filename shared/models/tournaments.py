"""
Tournament System Models for SQLAlchemy 2.0+
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal

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
    UniqueConstraint,
    Numeric
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# === ENUMS ===

class TournamentStatus(str, Enum):
    DRAFT = "draft"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TournamentType(str, Enum):
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TOURNAMENT_ENTRY = "tournament_entry"
    TOURNAMENT_PRIZE = "tournament_prize"
    PURCHASE = "purchase"
    REFUND = "refund"


# === MODELS ===

class PlayerWallet(Base):
    """Player wallet for tournament entry fees and prizes"""
    __tablename__ = "player_wallets"
    __table_args__ = (
        UniqueConstraint("player_id", name="uq_player_wallets_player"),
        Index("ix_player_wallets_balance", "balance"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Balance
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    player: Mapped["Player"] = relationship()
    transactions: Mapped[List["WalletTransaction"]] = relationship(back_populates="wallet")


class WalletTransaction(Base):
    """Wallet transaction history"""
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        Index("ix_wallet_transactions_wallet", "wallet_id"),
        Index("ix_wallet_transactions_type", "transaction_type"),
        Index("ix_wallet_transactions_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("player_wallets.id", ondelete="CASCADE"), nullable=False)
    
    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # References
    tournament_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournaments.id", ondelete="SET NULL"))
    reference_id: Mapped[Optional[str]] = mapped_column(String(100))  # External payment reference
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    wallet: Mapped["PlayerWallet"] = relationship(back_populates="transactions")
    tournament: Mapped[Optional["Tournament"]] = relationship()


class Tournament(Base):
    """Tournament management"""
    __tablename__ = "tournaments"
    __table_args__ = (
        Index("ix_tournaments_status", "status"),
        Index("ix_tournaments_start_time", "start_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tournament_type: Mapped[TournamentType] = mapped_column(SAEnum(TournamentType), nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(SAEnum(TournamentStatus), default=TournamentStatus.DRAFT, nullable=False)
    
    # Entry requirements
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    min_participants: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    
    # Prize pool
    prize_pool: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    prize_distribution: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)  # How prizes are distributed
    
    # Timing
    registration_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Settings
    tournament_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Admin tracking
    created_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    participants: Mapped[List["TournamentParticipant"]] = relationship(back_populates="tournament")
    matches: Mapped[List["TournamentMatch"]] = relationship(back_populates="tournament")
    created_by: Mapped["Admin"] = relationship()


class TournamentParticipant(Base):
    """Tournament participant registration"""
    __tablename__ = "tournament_participants"
    __table_args__ = (
        UniqueConstraint("tournament_id", "player_id", name="uq_tournament_participants_tournament_player"),
        Index("ix_tournament_participants_tournament", "tournament_id"),
        Index("ix_tournament_participants_player", "player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Registration details
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    seed: Mapped[Optional[int]] = mapped_column(Integer)  # Tournament seeding
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    eliminated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    final_placement: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Prize
    prize_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Relationships
    tournament: Mapped["Tournament"] = relationship(back_populates="participants")
    player: Mapped["Player"] = relationship()


class TournamentMatch(Base):
    """Individual matches within tournaments"""
    __tablename__ = "tournament_matches"
    __table_args__ = (
        Index("ix_tournament_matches_tournament", "tournament_id"),
        Index("ix_tournament_matches_round", "round_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    
    # Match details
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    match_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Match within the round
    
    # Players
    player1_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    player2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    winner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    
    # Match reference
    match_id: Mapped[Optional[int]] = mapped_column(ForeignKey("matches.id", ondelete="SET NULL"))
    
    # Status
    is_bye: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Bye round
    
    # Timestamps
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    tournament: Mapped["Tournament"] = relationship(back_populates="matches")
    match: Mapped[Optional["Match"]] = relationship()
    player1: Mapped[Optional["Player"]] = relationship(foreign_keys=[player1_id])
    player2: Mapped[Optional["Player"]] = relationship(foreign_keys=[player2_id])
    winner: Mapped[Optional["Player"]] = relationship(foreign_keys=[winner_id])