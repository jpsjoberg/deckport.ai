"""
Enhanced NFC Trading System Models for SQLAlchemy 2.0+
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

class TradeStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"


class TradeType(str, Enum):
    DIRECT = "direct"  # Direct player-to-player trade
    AUCTION = "auction"  # Auction-style trade
    MARKETPLACE = "marketplace"  # Marketplace listing


class AuctionStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class MarketplaceListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


# === MODELS ===

class EnhancedNFCCard(Base):
    """Enhanced NFC card with trading capabilities"""
    __tablename__ = "enhanced_nfc_cards"
    __table_args__ = (
        UniqueConstraint("nfc_uid", name="uq_enhanced_nfc_cards_uid"),
        Index("ix_enhanced_nfc_cards_owner", "owner_player_id"),
        Index("ix_enhanced_nfc_cards_template", "card_template_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic card info
    nfc_uid: Mapped[str] = mapped_column(String(32), nullable=False)
    card_template_id: Mapped[int] = mapped_column(ForeignKey("card_catalog.id"), nullable=False)
    
    # Ownership
    owner_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    
    # Card state
    is_tradeable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Locked during trades
    
    # Trading history
    trade_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_traded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Condition and rarity
    condition_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)  # 0-100
    serial_number: Mapped[Optional[int]] = mapped_column(Integer)  # For limited editions
    
    # Timestamps
    minted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    owner_player: Mapped[Optional["Player"]] = relationship()
    card_template: Mapped["CardCatalog"] = relationship()
    trade_offers_sent: Mapped[List["TradeOffer"]] = relationship(foreign_keys="TradeOffer.offered_card_id", back_populates="offered_card")
    trade_offers_requested: Mapped[List["TradeOffer"]] = relationship(foreign_keys="TradeOffer.requested_card_id", back_populates="requested_card")
    auction_listings: Mapped[List["CardAuction"]] = relationship(back_populates="card")
    marketplace_listings: Mapped[List["MarketplaceListing"]] = relationship(back_populates="card")
    
    # Complete NFC system fields
    product_sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='provisioned')
    security_level: Mapped[str] = mapped_column(String(20), default='NTAG424_DNA')
    issuer_key_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provisioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Cryptographic security fields (for maximum security mode)
    auth_key_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    enc_key_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mac_key_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Usage tracking fields
    tap_counter: Mapped[int] = mapped_column(Integer, default=0)
    auth_counter: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    public_page: Mapped[Optional["CardPublicPage"]] = relationship(back_populates="nfc_card")


class CardPublicPage(Base):
    """Public card pages for sharing card information"""
    __tablename__ = "card_public_pages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfc_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("enhanced_nfc_cards.id"), nullable=False)
    
    # Public Access
    public_slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Statistics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Display Settings
    show_owner: Mapped[bool] = mapped_column(Boolean, default=True)
    show_stats: Mapped[bool] = mapped_column(Boolean, default=True)
    show_history: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    nfc_card: Mapped["EnhancedNFCCard"] = relationship(back_populates="public_page")


class CardUpgrade(Base):
    """Card upgrade history tracking"""
    __tablename__ = "card_upgrades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfc_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("enhanced_nfc_cards.id"), nullable=False)
    
    # Upgrade Details
    upgrade_type: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # Before/After States
    old_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    old_stats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_stats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Upgrade Context
    upgrade_cost: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    trigger_event: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    match_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    upgraded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    nfc_card: Mapped["EnhancedNFCCard"] = relationship()


class NFCSecurityLog(Base):
    """Security event logging for NFC cards"""
    __tablename__ = "nfc_security_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfc_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("enhanced_nfc_cards.id"), nullable=False)
    
    # Event Details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default='info')
    
    # Context
    console_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    player_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("players.id"), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Technical Data
    auth_challenge: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_response: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    nfc_card: Mapped["EnhancedNFCCard"] = relationship()
    player: Mapped[Optional["Player"]] = relationship()


class TradeOffer(Base):
    """Direct trading offers between players"""
    __tablename__ = "trade_offers"
    __table_args__ = (
        Index("ix_trade_offers_sender", "sender_player_id"),
        Index("ix_trade_offers_receiver", "receiver_player_id"),
        Index("ix_trade_offers_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Players involved
    sender_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    receiver_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Cards involved
    offered_card_id: Mapped[int] = mapped_column(ForeignKey("enhanced_nfc_cards.id", ondelete="CASCADE"), nullable=False)
    requested_card_id: Mapped[Optional[int]] = mapped_column(ForeignKey("enhanced_nfc_cards.id", ondelete="CASCADE"))
    
    # Additional terms
    additional_credits: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[TradeStatus] = mapped_column(SAEnum(TradeStatus), default=TradeStatus.PENDING, nullable=False)
    trade_type: Mapped[TradeType] = mapped_column(SAEnum(TradeType), default=TradeType.DIRECT, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    sender_player: Mapped["Player"] = relationship(foreign_keys=[sender_player_id])
    receiver_player: Mapped["Player"] = relationship(foreign_keys=[receiver_player_id])
    offered_card: Mapped["EnhancedNFCCard"] = relationship(foreign_keys=[offered_card_id], back_populates="trade_offers_sent")
    requested_card: Mapped[Optional["EnhancedNFCCard"]] = relationship(foreign_keys=[requested_card_id], back_populates="trade_offers_requested")


class CardAuction(Base):
    """Auction-style trading for cards"""
    __tablename__ = "card_auctions"
    __table_args__ = (
        Index("ix_card_auctions_seller", "seller_player_id"),
        Index("ix_card_auctions_card", "card_id"),
        Index("ix_card_auctions_status", "status"),
        Index("ix_card_auctions_ends", "ends_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Auction details
    seller_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("enhanced_nfc_cards.id", ondelete="CASCADE"), nullable=False)
    
    # Pricing
    starting_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reserve_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    current_bid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    
    # Bidding
    current_bidder_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    bid_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    status: Mapped[AuctionStatus] = mapped_column(SAEnum(AuctionStatus), default=AuctionStatus.ACTIVE, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    seller_player: Mapped["Player"] = relationship(foreign_keys=[seller_player_id])
    card: Mapped["EnhancedNFCCard"] = relationship(back_populates="auction_listings")
    current_bidder: Mapped[Optional["Player"]] = relationship(foreign_keys=[current_bidder_id])
    bids: Mapped[List["AuctionBid"]] = relationship(back_populates="auction")


class AuctionBid(Base):
    """Individual bids on card auctions"""
    __tablename__ = "auction_bids"
    __table_args__ = (
        Index("ix_auction_bids_auction", "auction_id"),
        Index("ix_auction_bids_bidder", "bidder_player_id"),
        Index("ix_auction_bids_timestamp", "bid_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey("card_auctions.id", ondelete="CASCADE"), nullable=False)
    bidder_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Bid details
    bid_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_winning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    bid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    auction: Mapped["CardAuction"] = relationship(back_populates="bids")
    bidder_player: Mapped["Player"] = relationship()


class MarketplaceListing(Base):
    """Fixed-price marketplace listings"""
    __tablename__ = "marketplace_listings"
    __table_args__ = (
        Index("ix_marketplace_listings_seller", "seller_player_id"),
        Index("ix_marketplace_listings_card", "card_id"),
        Index("ix_marketplace_listings_status", "status"),
        Index("ix_marketplace_listings_price", "price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Listing details
    seller_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("enhanced_nfc_cards.id", ondelete="CASCADE"), nullable=False)
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Status
    status: Mapped[MarketplaceListingStatus] = mapped_column(SAEnum(MarketplaceListingStatus), default=MarketplaceListingStatus.ACTIVE, nullable=False)
    
    # Purchase info
    buyer_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    
    # Timestamps
    listed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    seller_player: Mapped["Player"] = relationship(foreign_keys=[seller_player_id])
    card: Mapped["EnhancedNFCCard"] = relationship(back_populates="marketplace_listings")
    buyer_player: Mapped[Optional["Player"]] = relationship(foreign_keys=[buyer_player_id])


class TradingHistory(Base):
    """Complete trading history for analytics"""
    __tablename__ = "trading_history"
    __table_args__ = (
        Index("ix_trading_history_card", "card_id"),
        Index("ix_trading_history_seller", "seller_player_id"),
        Index("ix_trading_history_buyer", "buyer_player_id"),
        Index("ix_trading_history_timestamp", "traded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Trade details
    card_id: Mapped[int] = mapped_column(ForeignKey("enhanced_nfc_cards.id", ondelete="CASCADE"), nullable=False)
    seller_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    buyer_player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Transaction details
    trade_type: Mapped[TradeType] = mapped_column(SAEnum(TradeType), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # References
    trade_offer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trade_offers.id", ondelete="SET NULL"))
    auction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("card_auctions.id", ondelete="SET NULL"))
    marketplace_listing_id: Mapped[Optional[int]] = mapped_column(ForeignKey("marketplace_listings.id", ondelete="SET NULL"))
    
    # Timestamps
    traded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    card: Mapped["EnhancedNFCCard"] = relationship()
    seller_player: Mapped["Player"] = relationship(foreign_keys=[seller_player_id])
    buyer_player: Mapped["Player"] = relationship(foreign_keys=[buyer_player_id])

class SecurityLevel(str, Enum):
    NTAG424_DNA = "NTAG424_DNA"
    NTAG215 = "NTAG215"
    BASIC = "BASIC"

class NFCCardStatus(str, Enum):
    provisioned = "provisioned"
    activated = "activated"
    locked = "locked"
    expired = "expired"

class CardActivationCode(Base):
    __tablename__ = 'card_activation_codes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nfc_card_id: Mapped[int] = mapped_column(Integer, ForeignKey('enhanced_nfc_cards.id'), nullable=False)
    activation_code: Mapped[str] = mapped_column(String(16), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    nfc_card: Mapped[EnhancedNFCCard] = relationship('EnhancedNFCCard', back_populates='activation_codes')

# Add activation codes relationship to EnhancedNFCCard
EnhancedNFCCard.activation_codes = relationship('CardActivationCode', back_populates='nfc_card')



