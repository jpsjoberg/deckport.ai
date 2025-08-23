"""
NFC Card Instance Models - Unique physical cards with evolution
Extensions to the existing NFC card system for unique card instances
"""

from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, ForeignKey, 
    UniqueConstraint, Index, JSON, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum as SAEnum

from .base import Base
from .card_templates import ManaColor, EffectTrigger, ActionSpeed


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CardInstanceStatus(str, Enum):
    """Status of individual NFC card instances"""
    MINT = "mint"              # Newly created, unused
    ACTIVE = "active"          # In use by player
    EVOLVED = "evolved"        # Has been modified from base template
    RETIRED = "retired"        # No longer in active use
    DAMAGED = "damaged"        # Physical card damaged
    LOST = "lost"             # Card reported lost


class EvolutionTrigger(str, Enum):
    """What triggered a card evolution"""
    BATTLE_EXPERIENCE = "battle_experience"    # From match participation
    PLAYER_CHOICE = "player_choice"           # Player-initiated evolution
    SPECIAL_EVENT = "special_event"           # Event-based evolution
    ACHIEVEMENT = "achievement"               # Achievement unlock
    FUSION = "fusion"                        # Card fusion/combination


class NFCCardInstance(Base):
    """
    Unique NFC card instances - each physical card is unique and can evolve
    Links to CardTemplate for base stats but can have unique modifications
    """
    __tablename__ = "nfc_card_instances"
    __table_args__ = (
        UniqueConstraint("ntag_uid", name="uq_nfc_card_instances_uid"),
        Index("ix_nfc_card_instances_template", "template_id"),
        Index("ix_nfc_card_instances_owner", "current_owner_id"),
        Index("ix_nfc_card_instances_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Link to base template (the "raw card design")
    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="RESTRICT"), nullable=False)
    
    # Physical NFC data
    ntag_uid: Mapped[str] = mapped_column(String(32), nullable=False)  # Unique NFC identifier
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_batches.id", ondelete="SET NULL"))
    
    # Instance-specific properties
    instance_name: Mapped[Optional[str]] = mapped_column(String(120))  # Custom name (e.g., "Lightning Phoenix Alpha")
    serial_number: Mapped[str] = mapped_column(String(50), nullable=False)  # Human-readable serial
    
    # Ownership and status
    current_owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    status: Mapped[CardInstanceStatus] = mapped_column(SAEnum(CardInstanceStatus), default=CardInstanceStatus.MINT, nullable=False)
    
    # Evolution tracking
    evolution_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # How many times evolved
    experience_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_matches_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Custom instance data (overrides template where present)
    custom_stats: Mapped[Optional[dict]] = mapped_column(JSONB)  # Modified stats from base template
    custom_abilities: Mapped[Optional[dict]] = mapped_column(JSONB)  # Additional or modified abilities
    custom_effects: Mapped[Optional[dict]] = mapped_column(JSONB)  # Additional or modified effects
    custom_keywords: Mapped[Optional[str]] = mapped_column(String(500))  # Additional keywords
    
    # Instance metadata
    mint_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    first_activation: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Authentication and security
    activation_code_hash: Mapped[Optional[str]] = mapped_column(String(255))
    issuer_key_ref: Mapped[Optional[str]] = mapped_column(String(128))

    # Relationships
    template: Mapped["CardTemplate"] = relationship("CardTemplate")  # Base template
    current_owner: Mapped[Optional["Player"]] = relationship("Player")
    batch: Mapped[Optional["CardBatch"]] = relationship("CardBatch")
    evolutions: Mapped[List["CardEvolution"]] = relationship(back_populates="card_instance", cascade="all, delete-orphan")
    match_participations: Mapped[List["CardMatchParticipation"]] = relationship(back_populates="card_instance")


class CardEvolution(Base):
    """
    Evolution history for NFC card instances
    Tracks how cards change over time from their base template
    """
    __tablename__ = "card_evolutions"
    __table_args__ = (
        Index("ix_card_evolutions_instance", "card_instance_id"),
        Index("ix_card_evolutions_date", "evolution_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_instance_id: Mapped[int] = mapped_column(ForeignKey("nfc_card_instances.id", ondelete="CASCADE"), nullable=False)
    
    # Evolution details
    evolution_trigger: Mapped[EvolutionTrigger] = mapped_column(SAEnum(EvolutionTrigger), nullable=False)
    evolution_level: Mapped[int] = mapped_column(Integer, nullable=False)  # What level this evolution brought the card to
    
    # What changed
    stat_changes: Mapped[Optional[dict]] = mapped_column(JSONB)  # Changes to attack/defense/health/etc
    ability_changes: Mapped[Optional[dict]] = mapped_column(JSONB)  # New or modified abilities
    effect_changes: Mapped[Optional[dict]] = mapped_column(JSONB)  # New or modified effects
    keyword_changes: Mapped[Optional[str]] = mapped_column(String(500))  # New keywords added
    
    # Context
    trigger_context: Mapped[Optional[dict]] = mapped_column(JSONB)  # What caused the evolution (match ID, event ID, etc.)
    evolution_description: Mapped[Optional[str]] = mapped_column(Text)  # Human-readable description
    
    # Metadata
    evolution_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    triggered_by_admin: Mapped[Optional[str]] = mapped_column(String(100))  # Admin who triggered manual evolution

    # Relationships
    card_instance: Mapped[NFCCardInstance] = relationship(back_populates="evolutions")


class CardMatchParticipation(Base):
    """
    Track which cards participated in which matches
    Used for experience calculation and evolution triggers
    """
    __tablename__ = "card_match_participations"
    __table_args__ = (
        UniqueConstraint("card_instance_id", "match_id", name="uq_card_match_participation"),
        Index("ix_card_match_participations_card", "card_instance_id"),
        Index("ix_card_match_participations_match", "match_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_instance_id: Mapped[int] = mapped_column(ForeignKey("nfc_card_instances.id", ondelete="CASCADE"), nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    
    # Performance in this match
    damage_dealt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    damage_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    abilities_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    match_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Experience gained from this match
    experience_gained: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Match context
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    card_instance: Mapped[NFCCardInstance] = relationship(back_populates="match_participations")
    match: Mapped["Match"] = relationship("Match")


class CardFusion(Base):
    """
    Track card fusion events where multiple cards combine into one
    """
    __tablename__ = "card_fusions"
    __table_args__ = (
        Index("ix_card_fusions_result", "result_card_id"),
        Index("ix_card_fusions_date", "fusion_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # The cards that were fused together (JSON array of card instance IDs)
    source_card_ids: Mapped[List[int]] = mapped_column(JSONB, nullable=False)
    
    # The resulting card
    result_card_id: Mapped[int] = mapped_column(ForeignKey("nfc_card_instances.id", ondelete="CASCADE"), nullable=False)
    
    # Fusion details
    fusion_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "elemental_fusion", "power_merge"
    fusion_recipe: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Rules used for fusion
    
    # Metadata
    fusion_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    performed_by_player: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    result_card: Mapped[NFCCardInstance] = relationship("NFCCardInstance")
    player: Mapped["Player"] = relationship("Player")

