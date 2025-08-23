"""
Card Template Models - Raw card designs and sets
SQLAlchemy models for AI-generated card templates that serve as blueprints for NFC cards
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


# Enums for card template system
class TemplateCategory(str, Enum):
    CREATURE = "CREATURE"
    STRUCTURE = "STRUCTURE"
    ACTION = "ACTION"
    SPECIAL = "SPECIAL"
    EQUIPMENT = "EQUIPMENT"


class TemplateRarity(str, Enum):
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


class CardSet(Base):
    """Card sets - collections of related card templates"""
    __tablename__ = "card_sets"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_card_sets_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by_admin: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    templates: Mapped[List["CardTemplate"]] = relationship(back_populates="card_set", cascade="all, delete-orphan")


class CardTemplate(Base):
    """Raw card templates - the base designs that NFC cards are created from"""
    __tablename__ = "card_templates"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_card_templates_slug"),
        Index("ix_card_templates_category", "category"),
        Index("ix_card_templates_rarity", "rarity"),
        Index("ix_card_templates_color", "primary_color"),
        Index("ix_card_templates_set", "card_set_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_sets.id", ondelete="SET NULL"))
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[TemplateCategory] = mapped_column(SAEnum(TemplateCategory), nullable=False)
    rarity: Mapped[TemplateRarity] = mapped_column(SAEnum(TemplateRarity), nullable=False)
    legendary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primary_color: Mapped[ManaColor] = mapped_column(SAEnum(ManaColor), nullable=False)
    energy_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    equipment_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(String(500))  # Comma-separated keywords
    
    # Template description and lore
    description: Mapped[Optional[str]] = mapped_column(Text)
    flavor_text: Mapped[Optional[str]] = mapped_column(Text)
    
    # Template status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Ready for NFC production
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    created_by_admin: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    card_set: Mapped[Optional[CardSet]] = relationship(back_populates="templates")
    base_stats: Mapped[Optional["CardTemplateStats"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    mana_costs: Mapped[List["CardTemplateManaCost"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    targeting: Mapped[Optional["CardTemplateTargeting"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    limits: Mapped[Optional["CardTemplateLimits"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    effects: Mapped[List["CardTemplateEffect"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    abilities: Mapped[List["CardTemplateAbility"]] = relationship(back_populates="template", cascade="all, delete-orphan")
    art_generations: Mapped[List["CardTemplateArtGeneration"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class CardTemplateStats(Base):
    """Base combat and gameplay stats for creature/structure templates"""
    __tablename__ = "card_template_stats"

    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), primary_key=True)
    attack: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    health: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    base_energy_per_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    template: Mapped[CardTemplate] = relationship(back_populates="base_stats")


class CardTemplateManaCost(Base):
    """Mana costs per color for templates (supports multi-color cards)"""
    __tablename__ = "card_template_mana_costs"
    __table_args__ = (
        Index("ix_card_template_mana_costs_template", "template_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), nullable=False)
    color: Mapped[ManaColor] = mapped_column(SAEnum(ManaColor), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    template: Mapped[CardTemplate] = relationship(back_populates="mana_costs")


class CardTemplateTargeting(Base):
    """Targeting rules for card templates"""
    __tablename__ = "card_template_targeting"

    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), primary_key=True)
    target_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_enemy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_self: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    template: Mapped[CardTemplate] = relationship(back_populates="targeting")


class CardTemplateLimits(Base):
    """Usage limits and charge rules for templates"""
    __tablename__ = "card_template_limits"

    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), primary_key=True)
    max_uses_per_match: Mapped[Optional[int]] = mapped_column(Integer)
    charges_max: Mapped[Optional[int]] = mapped_column(Integer)
    charge_rule: Mapped[Optional[dict]] = mapped_column(JSONB)

    template: Mapped[CardTemplate] = relationship(back_populates="limits")


class CardTemplateEffect(Base):
    """Base effects for card templates"""
    __tablename__ = "card_template_effects"
    __table_args__ = (
        Index("ix_card_template_effects_template", "template_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), nullable=False)
    trigger: Mapped[EffectTrigger] = mapped_column(SAEnum(EffectTrigger), nullable=False)
    speed: Mapped[ActionSpeed] = mapped_column(SAEnum(ActionSpeed), default=ActionSpeed.SLOW, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    template: Mapped[CardTemplate] = relationship(back_populates="effects")
    conditions: Mapped[List["CardTemplateEffectCondition"]] = relationship(back_populates="effect", cascade="all, delete-orphan")
    actions: Mapped[List["CardTemplateEffectAction"]] = relationship(back_populates="effect", cascade="all, delete-orphan")


class CardTemplateEffectCondition(Base):
    """Conditions for template effects"""
    __tablename__ = "card_template_effect_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effect_id: Mapped[int] = mapped_column(ForeignKey("card_template_effects.id", ondelete="CASCADE"), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    effect: Mapped[CardTemplateEffect] = relationship(back_populates="conditions")


class CardTemplateEffectAction(Base):
    """Actions performed by template effects"""
    __tablename__ = "card_template_effect_actions"
    __table_args__ = (
        Index("ix_card_template_effect_actions_effect", "effect_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effect_id: Mapped[int] = mapped_column(ForeignKey("card_template_effects.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    effect: Mapped[CardTemplateEffect] = relationship(back_populates="actions")


class CardTemplateAbility(Base):
    """Base abilities for card templates including ultimates"""
    __tablename__ = "card_template_abilities"
    __table_args__ = (
        Index("ix_card_template_abilities_template", "template_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_ultimate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    charges_max: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    charge_rule: Mapped[Optional[dict]] = mapped_column(JSONB)
    trigger: Mapped[Optional[EffectTrigger]] = mapped_column(SAEnum(EffectTrigger))
    speed: Mapped[ActionSpeed] = mapped_column(SAEnum(ActionSpeed), default=ActionSpeed.FAST, nullable=False)

    template: Mapped[CardTemplate] = relationship(back_populates="abilities")
    actions: Mapped[List["CardTemplateAbilityAction"]] = relationship(back_populates="ability", cascade="all, delete-orphan")


class CardTemplateAbilityAction(Base):
    """Actions performed by template abilities"""
    __tablename__ = "card_template_ability_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ability_id: Mapped[int] = mapped_column(ForeignKey("card_template_abilities.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ability: Mapped[CardTemplateAbility] = relationship(back_populates="actions")


class CardTemplateArtGeneration(Base):
    """Tracking for ComfyUI art generation for templates"""
    __tablename__ = "card_template_art_generations"
    __table_args__ = (
        Index("ix_card_template_art_generations_template", "template_id"),
        Index("ix_card_template_art_generations_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), nullable=False)
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

    template: Mapped[CardTemplate] = relationship(back_populates="art_generations")

