"""
Card Template System Models for SQLAlchemy 2.0+
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

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
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# === ENUMS ===

class TemplateCategory(str, Enum):
    CREATURE = "CREATURE"
    STRUCTURE = "STRUCTURE"
    ACTION_FAST = "ACTION_FAST"
    ACTION_SLOW = "ACTION_SLOW"
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
    GOLDEN = "GOLDEN"
    SHADOW = "SHADOW"
    AETHER = "AETHER"


class EffectTrigger(str, Enum):
    ON_PLAY = "on_play"
    ON_DEATH = "on_death"
    ON_DAMAGE = "on_damage"
    ON_HEAL = "on_heal"
    START_TURN = "start_turn"
    END_TURN = "end_turn"
    START_PHASE = "start_phase"
    END_PHASE = "end_phase"


class ActionSpeed(str, Enum):
    FAST = "FAST"
    SLOW = "SLOW"


class ArtGenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# === MODELS ===

class CardSet(Base):
    """Card sets - collections of related card templates"""
    __tablename__ = "card_sets"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_card_sets_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    templates: Mapped[List["CardTemplate"]] = relationship(back_populates="card_set")


class CardTemplate(Base):
    """Raw card templates - the base designs that NFC cards are created from"""
    __tablename__ = "card_templates"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_card_templates_slug"),
        Index("ix_card_templates_category", "category"),
        Index("ix_card_templates_rarity", "rarity"),
        Index("ix_card_templates_set", "card_set_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Classification
    category: Mapped[TemplateCategory] = mapped_column(SAEnum(TemplateCategory), nullable=False)
    rarity: Mapped[TemplateRarity] = mapped_column(SAEnum(TemplateRarity), nullable=False)
    card_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_sets.id", ondelete="SET NULL"))
    
    # Game mechanics
    mana_cost_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Art and presentation
    flavor_text: Mapped[Optional[str]] = mapped_column(Text)
    rules_text: Mapped[Optional[str]] = mapped_column(Text)
    artwork_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_playable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    card_set: Mapped[Optional["CardSet"]] = relationship(back_populates="templates")
    base_stats: Mapped[List["CardTemplateStats"]] = relationship(back_populates="template")
    mana_costs: Mapped[List["CardTemplateManaCost"]] = relationship(back_populates="template")
    targeting: Mapped[Optional["CardTemplateTargeting"]] = relationship(back_populates="template")
    limits: Mapped[Optional["CardTemplateLimits"]] = relationship(back_populates="template")
    effects: Mapped[List["CardTemplateEffect"]] = relationship(back_populates="template")
    abilities: Mapped[List["CardTemplateAbility"]] = relationship(back_populates="template")
    art_generations: Mapped[List["CardTemplateArtGeneration"]] = relationship(back_populates="template")


class CardTemplateStats(Base):
    """Base combat and gameplay stats for creature/structure templates"""
    __tablename__ = "card_template_stats"

    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), primary_key=True)
    
    # Combat stats
    attack: Mapped[Optional[int]] = mapped_column(Integer)
    defense: Mapped[Optional[int]] = mapped_column(Integer)
    health: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Special stats
    speed: Mapped[Optional[int]] = mapped_column(Integer)
    range_value: Mapped[Optional[int]] = mapped_column(Integer)  # 'range' is reserved
    
    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="base_stats")


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

    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="mana_costs")


class CardTemplateTargeting(Base):
    """Targeting rules for card templates"""
    __tablename__ = "card_template_targeting"

    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), primary_key=True)
    target_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_enemy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_self: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    target_structures: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_creatures: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_targets: Mapped[Optional[int]] = mapped_column(Integer)
    min_targets: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="targeting")


class CardTemplateLimits(Base):
    """Usage limits and charge rules for templates"""
    __tablename__ = "card_template_limits"

    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), primary_key=True)
    max_uses_per_match: Mapped[Optional[int]] = mapped_column(Integer)
    charges_max: Mapped[Optional[int]] = mapped_column(Integer)
    charges_start: Mapped[Optional[int]] = mapped_column(Integer)
    cooldown_turns: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="limits")


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
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="effects")
    conditions: Mapped[List["CardTemplateEffectCondition"]] = relationship(back_populates="effect")
    actions: Mapped[List["CardTemplateEffectAction"]] = relationship(back_populates="effect")


class CardTemplateEffectCondition(Base):
    """Conditions for template effects"""
    __tablename__ = "card_template_effect_conditions"
    __table_args__ = (
        Index("ix_card_template_effect_conditions_effect", "effect_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effect_id: Mapped[int] = mapped_column(ForeignKey("card_template_effects.id", ondelete="CASCADE"), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(100), nullable=False)
    condition_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # Relationships
    effect: Mapped["CardTemplateEffect"] = relationship(back_populates="conditions")


class CardTemplateEffectAction(Base):
    """Actions performed by template effects"""
    __tablename__ = "card_template_effect_actions"
    __table_args__ = (
        Index("ix_card_template_effect_actions_effect", "effect_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effect_id: Mapped[int] = mapped_column(ForeignKey("card_template_effects.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    effect: Mapped["CardTemplateEffect"] = relationship(back_populates="actions")


class CardTemplateAbility(Base):
    """Base abilities for card templates including ultimates"""
    __tablename__ = "card_template_abilities"
    __table_args__ = (
        Index("ix_card_template_abilities_template", "template_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("card_templates.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Ability mechanics
    is_ultimate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mana_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cooldown_turns: Mapped[Optional[int]] = mapped_column(Integer)
    speed: Mapped[ActionSpeed] = mapped_column(SAEnum(ActionSpeed), default=ActionSpeed.FAST, nullable=False)

    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="abilities")
    actions: Mapped[List["CardTemplateAbilityAction"]] = relationship(back_populates="ability")


class CardTemplateAbilityAction(Base):
    """Actions performed by template abilities"""
    __tablename__ = "card_template_ability_actions"
    __table_args__ = (
        Index("ix_card_template_ability_actions_ability", "ability_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ability_id: Mapped[int] = mapped_column(ForeignKey("card_template_abilities.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    ability: Mapped["CardTemplateAbility"] = relationship(back_populates="actions")


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
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text)
    
    # Generation details
    status: Mapped[ArtGenerationStatus] = mapped_column(SAEnum(ArtGenerationStatus), default=ArtGenerationStatus.PENDING, nullable=False)
    comfyui_workflow_id: Mapped[Optional[str]] = mapped_column(String(100))
    generated_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    template: Mapped["CardTemplate"] = relationship(back_populates="art_generations")