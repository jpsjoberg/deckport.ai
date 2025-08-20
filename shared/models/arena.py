"""
Arena models for Deckport.ai
Defines arena system with storytelling, advantages, and video integration
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class ArenaClipType(str, Enum):
    intro = "intro"                    # Arena introduction video
    ambient = "ambient"               # Background loop during match
    advantage = "advantage"           # When player gets arena advantage
    victory = "victory"               # Arena-specific victory
    hazard_trigger = "hazard_trigger" # When arena hazard activates
    objective_complete = "objective_complete" # When arena objective completed

class Arena(Base):
    __tablename__ = "arenas"
    __table_args__ = (
        Index("ix_arenas_mana_color", "mana_color"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mana_color: Mapped[str] = mapped_column(String(20), nullable=False)  # CRIMSON, AZURE, etc.
    
    # Arena mechanics
    passive_effect: Mapped[Optional[dict]] = mapped_column(JSONB)  # Ongoing arena effect
    objective: Mapped[Optional[dict]] = mapped_column(JSONB)       # Arena objective for rewards
    hazard: Mapped[Optional[dict]] = mapped_column(JSONB)          # Arena hazard/danger
    
    # Storytelling
    story_text: Mapped[Optional[str]] = mapped_column(Text)        # Arena lore and description
    flavor_text: Mapped[Optional[str]] = mapped_column(Text)       # Short atmospheric description
    
    # Visual/Audio
    background_music: Mapped[Optional[str]] = mapped_column(String(255))  # Background music file
    ambient_sounds: Mapped[Optional[str]] = mapped_column(String(255))    # Ambient sound effects
    
    # Gameplay settings
    special_rules: Mapped[Optional[dict]] = mapped_column(JSONB)   # Arena-specific rule modifications
    difficulty_rating: Mapped[int] = mapped_column(Integer, default=1)    # 1-5 difficulty scale
    
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    
    # Relationships
    clips: Mapped[List[ArenaClip]] = relationship(back_populates="arena", cascade="all, delete-orphan")
    matches: Mapped[List["Match"]] = relationship(back_populates="arena")

class ArenaClip(Base):
    __tablename__ = "arena_clips"
    __table_args__ = (
        Index("ix_arena_clips_type", "clip_type"),
        Index("ix_arena_clips_arena", "arena_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    arena_id: Mapped[int] = mapped_column(ForeignKey("arenas.id", ondelete="CASCADE"), nullable=False)
    
    clip_type: Mapped[ArenaClipType] = mapped_column(nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)  # Relative to assets/videos/
    
    # Trigger conditions
    trigger_condition: Mapped[Optional[dict]] = mapped_column(JSONB)  # When to play this clip
    
    # Clip metadata
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    resolution: Mapped[Optional[str]] = mapped_column(String(20))     # "1920x1080", etc.
    file_size_mb: Mapped[Optional[float]] = mapped_column()           # For storage planning
    
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    
    # Relationships
    arena: Mapped[Arena] = relationship(back_populates="clips")

class MatchTurn(Base):
    __tablename__ = "match_turns"
    __table_args__ = (
        Index("ix_match_turns_match", "match_id"),
        Index("ix_match_turns_number", "turn_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    current_player_team: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 or 1
    phase: Mapped[str] = mapped_column(String(20), nullable=False)  # start, main, attack, end
    
    # Timing
    phase_start_at: Mapped[datetime] = mapped_column(nullable=False)
    phase_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Actions taken during this turn/phase
    actions_taken: Mapped[Optional[list]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

class MatchCardAction(Base):
    __tablename__ = "match_card_actions"
    __table_args__ = (
        Index("ix_match_actions_match", "match_id"),
        Index("ix_match_actions_player", "player_id"),
        Index("ix_match_actions_turn", "turn_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    turn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("match_turns.id", ondelete="SET NULL"))
    
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    nfc_card_id: Mapped[int] = mapped_column(ForeignKey("nfc_cards.id", ondelete="CASCADE"), nullable=False)
    
    # Action details
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # summon, cast, equip, activate
    action_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Performance metrics
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)  # Time from NFC scan to action
    
    timestamp: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
