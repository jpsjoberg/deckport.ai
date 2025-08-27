"""
Shop System Models for SQLAlchemy 2.0+
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

class ProductType(str, Enum):
    CARD_PACK = "card_pack"
    SINGLE_CARD = "single_card"
    PREMIUM_SUBSCRIPTION = "premium_subscription"
    TOURNAMENT_ENTRY = "tournament_entry"
    COSMETIC = "cosmetic"
    CURRENCY = "currency"


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD_OUT = "sold_out"
    DISCONTINUED = "discontinued"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    WALLET_CREDITS = "wallet_credits"
    GIFT_CARD = "gift_card"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BUY_X_GET_Y = "buy_x_get_y"


# === MODELS ===

class ShopProduct(Base):
    """Products available in the shop"""
    __tablename__ = "shop_products"
    __table_args__ = (
        UniqueConstraint("sku", name="uq_shop_products_sku"),
        Index("ix_shop_products_type", "product_type"),
        Index("ix_shop_products_status", "status"),
        Index("ix_shop_products_price", "price"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Product info
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    compare_at_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))  # For sale pricing
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default='USD', nullable=False)
    
    # Inventory
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer)  # NULL = unlimited
    low_stock_threshold: Mapped[Optional[int]] = mapped_column(Integer)
    track_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_backorder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default='active', nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Content and metadata
    card_skus: Mapped[Optional[List[str]]] = mapped_column(JSON)  # Card SKUs for packs
    digital_assets: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Digital content
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # Product tags
    slug: Mapped[Optional[str]] = mapped_column(String(200))  # URL slug
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    meta_title: Mapped[Optional[str]] = mapped_column(String(200))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Physical attributes
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    length: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    width: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    height: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    
    # Additional flags
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    gallery_images: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Media
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    # thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))  # Not in DB schema
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    order_items: Mapped[List["ShopOrderItem"]] = relationship(back_populates="product")
    discounts: Mapped[List["ProductDiscount"]] = relationship(back_populates="product")


class ShopOrder(Base):
    """Customer orders"""
    __tablename__ = "shop_orders"
    __table_args__ = (
        UniqueConstraint("order_number", name="uq_shop_orders_number"),
        Index("ix_shop_orders_customer", "customer_id"),
        Index("ix_shop_orders_status", "order_status"),
        Index("ix_shop_orders_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Order info
    order_number: Mapped[str] = mapped_column(String(20), nullable=False)  # Human-readable order number
    customer_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Pricing
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Payment
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))  # External payment ID
    
    # Status
    order_status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    
    # Additional fields from database schema
    payment_status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    shipping_status: Mapped[Optional[str]] = mapped_column(String(50))
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100))
    shipping_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Addresses and contact
    customer_name: Mapped[Optional[str]] = mapped_column(String(200))
    customer_email: Mapped[Optional[str]] = mapped_column(String(200))
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50))
    billing_address: Mapped[Optional[str]] = mapped_column(Text)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text)
    
    # Fulfillment and shipping
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Additional fields
    currency: Mapped[str] = mapped_column(String(3), default='USD', nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    is_gift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_shipping: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    customer: Mapped["Player"] = relationship(foreign_keys=[customer_id])
    order_items: Mapped[List["ShopOrderItem"]] = relationship(back_populates="order")


class ShopOrderItem(Base):
    """Individual items within an order"""
    __tablename__ = "shop_order_items"
    __table_args__ = (
        Index("ix_shop_order_items_order", "order_id"),
        Index("ix_shop_order_items_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("shop_products.id"), nullable=False)
    
    # Item details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Price at time of purchase
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Product info (stored at time of purchase)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(50), nullable=False)
    product_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Fulfillment
    is_fulfilled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fulfilled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fulfillment_notes: Mapped[Optional[str]] = mapped_column(Text)
    delivery_method: Mapped[Optional[str]] = mapped_column(String(50))
    digital_assets_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    order: Mapped["ShopOrder"] = relationship(back_populates="order_items")
    product: Mapped["ShopProduct"] = relationship(back_populates="order_items")


class ProductDiscount(Base):
    """Discounts and promotions for products"""
    __tablename__ = "product_discounts"
    __table_args__ = (
        Index("ix_product_discounts_product", "product_id"),
        Index("ix_product_discounts_code", "discount_code"),
        Index("ix_product_discounts_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shop_products.id", ondelete="CASCADE"))  # NULL = applies to all
    
    # Discount info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discount_code: Mapped[Optional[str]] = mapped_column(String(20))  # NULL = automatic discount
    
    # Discount rules
    discount_type: Mapped[DiscountType] = mapped_column(SAEnum(DiscountType), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Percentage or amount
    
    # Usage limits
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)  # NULL = unlimited
    uses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_uses_per_player: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Conditions
    minimum_purchase_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    product: Mapped[Optional["ShopProduct"]] = relationship(back_populates="discounts")
    usage_history: Mapped[List["DiscountUsage"]] = relationship(back_populates="discount")


class DiscountUsage(Base):
    """Track discount code usage"""
    __tablename__ = "discount_usage"
    __table_args__ = (
        Index("ix_discount_usage_discount", "discount_id"),
        Index("ix_discount_usage_player", "player_id"),
        Index("ix_discount_usage_order", "order_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discount_id: Mapped[int] = mapped_column(ForeignKey("product_discounts.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False)
    
    # Usage details
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    discount: Mapped["ProductDiscount"] = relationship(back_populates="usage_history")
    player: Mapped["Player"] = relationship()
    order: Mapped["ShopOrder"] = relationship()


class GiftCard(Base):
    """Gift cards for the shop"""
    __tablename__ = "gift_cards"
    __table_args__ = (
        UniqueConstraint("code", name="uq_gift_cards_code"),
        Index("ix_gift_cards_recipient", "recipient_player_id"),
        Index("ix_gift_cards_purchaser", "purchaser_player_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Gift card info
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    initial_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Players
    purchaser_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    recipient_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_redeemed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    purchaser_player: Mapped[Optional["Player"]] = relationship(foreign_keys=[purchaser_player_id])
    recipient_player: Mapped[Optional["Player"]] = relationship(foreign_keys=[recipient_player_id])
    usage_history: Mapped[List["GiftCardUsage"]] = relationship(back_populates="gift_card")


class GiftCardUsage(Base):
    """Track gift card usage"""
    __tablename__ = "gift_card_usage"
    __table_args__ = (
        Index("ix_gift_card_usage_gift_card", "gift_card_id"),
        Index("ix_gift_card_usage_order", "order_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gift_card_id: Mapped[int] = mapped_column(ForeignKey("gift_cards.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("shop_orders.id", ondelete="CASCADE"), nullable=False)
    
    # Usage details
    amount_used: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Timestamps
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    gift_card: Mapped["GiftCard"] = relationship(back_populates="usage_history")
    order: Mapped["ShopOrder"] = relationship()