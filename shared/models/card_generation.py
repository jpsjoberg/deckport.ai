"""
Card Generation and Management Models
SQLAlchemy models for the AI-powered card creation system
"""

from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, ForeignKey, 
    UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum as SAEnum
import uuid

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Enums for card generation system
class GeneratedCardCategory(str, Enum):
    CREATURE = "CREATURE"
    STRUCTURE = "STRUCTURE"
    ACTION = "ACTION"
    SPECIAL = "SPECIAL"
    EQUIPMENT = "EQUIPMENT"


class GeneratedCardRarity(str, Enum):
    COMMON = "COMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"


class ManaColor(str, Enum):
    CRIMSON = "CRIMSON"
    AZURE = "AZURE"
    VERDANT = "VERDANT"
    OBSIDIAN = "OBSIDIAN"
    RADIANT = "RADIANT"
    AETHER = "AETHER"


class EffectTrigger(str, Enum):
    ON_PLAY = "on_play"
    ON_BASIC_ATTACK = "on_basic_attack"
    ON_DAMAGE_TAKEN = "on_damage_taken"
    END_PHASE = "end_phase"


class ActionSpeed(str, Enum):
    FAST = "FAST"
    SLOW = "SLOW"


class ArtGenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# Raw card template models (for card sets and designs)
class CardTemplate(Base):
    """Raw card templates - the base designs for card sets"""
    __tablename__ = "card_templates"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_generated_cards_slug"),
        Index("ix_generated_cards_category", "category"),
        Index("ix_generated_cards_rarity", "rarity"),
        Index("ix_generated_cards_color", "primary_color"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[GeneratedCardCategory] = mapped_column(SAEnum(GeneratedCardCategory), nullable=False)
    rarity: Mapped[GeneratedCardRarity] = mapped_column(SAEnum(GeneratedCardRarity), nullable=False)
    legendary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primary_color: Mapped[ManaColor] = mapped_column(SAEnum(ManaColor), nullable=False)
    energy_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    equipment_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(String(500))  # Comma-separated keywords
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by_admin: Mapped[Optional[str]] = mapped_column(String(100))  # Admin username who created it

    # Relationships
    stats: Mapped[Optional["GeneratedCardStats"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    mana_costs: Mapped[List["GeneratedCardManaCost"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    targeting: Mapped[Optional["GeneratedCardTargeting"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    limits: Mapped[Optional["GeneratedCardLimits"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    effects: Mapped[List["GeneratedCardEffect"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    abilities: Mapped[List["GeneratedCardAbility"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    art_generations: Mapped[List["CardArtGeneration"]] = relationship(back_populates="card", cascade="all, delete-orphan")


class GeneratedCardStats(Base):
    """Combat and gameplay stats for creatures/structures"""
    __tablename__ = "generated_card_stats"

    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), primary_key=True)
    attack: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    health: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    base_energy_per_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    card: Mapped[GeneratedCard] = relationship(back_populates="stats")


class GeneratedCardManaCost(Base):
    """Mana costs per color (supports multi-color cards)"""
    __tablename__ = "generated_card_mana_costs"
    __table_args__ = (
        Index("ix_generated_card_mana_costs_card", "card_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), nullable=False)
    color: Mapped[ManaColor] = mapped_column(SAEnum(ManaColor), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    card: Mapped[GeneratedCard] = relationship(back_populates="mana_costs")


class GeneratedCardTargeting(Base):
    """Targeting rules for cards"""
    __tablename__ = "generated_card_targeting"

    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), primary_key=True)
    target_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_enemy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_self: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    card: Mapped[GeneratedCard] = relationship(back_populates="targeting")


class GeneratedCardLimits(Base):
    """Usage limits and charge rules"""
    __tablename__ = "generated_card_limits"

    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), primary_key=True)
    max_uses_per_match: Mapped[Optional[int]] = mapped_column(Integer)
    charges_max: Mapped[Optional[int]] = mapped_column(Integer)
    charge_rule: Mapped[Optional[dict]] = mapped_column(JSONB)

    card: Mapped[GeneratedCard] = relationship(back_populates="limits")


class GeneratedCardEffect(Base):
    """Card effects and abilities"""
    __tablename__ = "generated_card_effects"
    __table_args__ = (
        Index("ix_generated_card_effects_card", "card_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), nullable=False)
    trigger: Mapped[EffectTrigger] = mapped_column(SAEnum(EffectTrigger), nullable=False)
    speed: Mapped[ActionSpeed] = mapped_column(SAEnum(ActionSpeed), default=ActionSpeed.SLOW, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    card: Mapped[GeneratedCard] = relationship(back_populates="effects")
    conditions: Mapped[List["GeneratedCardEffectCondition"]] = relationship(back_populates="effect", cascade="all, delete-orphan")
    actions: Mapped[List["GeneratedCardEffectAction"]] = relationship(back_populates="effect", cascade="all, delete-orphan")


class GeneratedCardEffectCondition(Base):
    """Conditions for card effects"""
    __tablename__ = "generated_card_effect_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effect_id: Mapped[int] = mapped_column(ForeignKey("generated_card_effects.id", ondelete="CASCADE"), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    effect: Mapped[GeneratedCardEffect] = relationship(back_populates="conditions")


class GeneratedCardEffectAction(Base):
    """Actions performed by card effects"""
    __tablename__ = "generated_card_effect_actions"
    __table_args__ = (
        Index("ix_generated_card_effect_actions_effect", "effect_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effect_id: Mapped[int] = mapped_column(ForeignKey("generated_card_effects.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    effect: Mapped[GeneratedCardEffect] = relationship(back_populates="actions")


class GeneratedCardAbility(Base):
    """Card abilities including ultimates"""
    __tablename__ = "generated_card_abilities"
    __table_args__ = (
        Index("ix_generated_card_abilities_card", "card_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_ultimate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    charges_max: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    charge_rule: Mapped[Optional[dict]] = mapped_column(JSONB)
    trigger: Mapped[Optional[EffectTrigger]] = mapped_column(SAEnum(EffectTrigger))
    speed: Mapped[ActionSpeed] = mapped_column(SAEnum(ActionSpeed), default=ActionSpeed.FAST, nullable=False)

    card: Mapped[GeneratedCard] = relationship(back_populates="abilities")
    actions: Mapped[List["GeneratedCardAbilityAction"]] = relationship(back_populates="ability", cascade="all, delete-orphan")


class GeneratedCardAbilityAction(Base):
    """Actions performed by card abilities"""
    __tablename__ = "generated_card_ability_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ability_id: Mapped[int] = mapped_column(ForeignKey("generated_card_abilities.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ability: Mapped[GeneratedCardAbility] = relationship(back_populates="actions")


class CardArtGeneration(Base):
    """Tracking for ComfyUI art generation"""
    __tablename__ = "card_art_generations"
    __table_args__ = (
        Index("ix_card_art_generations_card", "card_id"),
        Index("ix_card_art_generations_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("generated_cards.id", ondelete="CASCADE"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    comfyui_prompt_id: Mapped[Optional[str]] = mapped_column(String(100))
    seed: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[ArtGenerationStatus] = mapped_column(SAEnum(ArtGenerationStatus), default=ArtGenerationStatus.PENDING, nullable=False)
    
    # File paths
    raw_art_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to generated artwork
    final_card_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to composed card
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    card: Mapped[GeneratedCard] = relationship(back_populates="art_generations")
