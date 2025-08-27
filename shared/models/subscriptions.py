"""
Subscription Models for Deckport.ai
Handles recurring payments, subscription management, and subscription revenue tracking
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, 
    Numeric, String, Text, UniqueConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# === ENUMS ===

class SubscriptionStatus(str, Enum):
    """Subscription status values"""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class SubscriptionPlan(str, Enum):
    """Available subscription plans"""
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingInterval(str, Enum):
    """Billing frequency"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentStatus(str, Enum):
    """Payment status for subscription invoices"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


# === MODELS ===

class Subscription(Base):
    """Player subscriptions for premium features"""
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("stripe_subscription_id", name="uq_subscriptions_stripe_id"),
        Index("ix_subscriptions_player", "player_id"),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_plan", "plan"),
        Index("ix_subscriptions_current_period", "current_period_start", "current_period_end"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Player and external references
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    stripe_subscription_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_customer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Subscription details
    plan: Mapped[SubscriptionPlan] = mapped_column(SAEnum(SubscriptionPlan), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(SAEnum(SubscriptionStatus), nullable=False)
    billing_interval: Mapped[BillingInterval] = mapped_column(SAEnum(BillingInterval), nullable=False)
    
    # Pricing
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Amount per billing cycle
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Billing periods
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Trial information
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Cancellation
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Extra data
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    player: Mapped["Player"] = relationship()
    invoices: Mapped[List["SubscriptionInvoice"]] = relationship(back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionInvoice(Base):
    """Subscription billing invoices and payments"""
    __tablename__ = "subscription_invoices"
    __table_args__ = (
        UniqueConstraint("stripe_invoice_id", name="uq_subscription_invoices_stripe_id"),
        Index("ix_subscription_invoices_subscription", "subscription_id"),
        Index("ix_subscription_invoices_status", "payment_status"),
        Index("ix_subscription_invoices_period", "period_start", "period_end"),
        Index("ix_subscription_invoices_due_date", "due_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # References
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    stripe_invoice_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Invoice details
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Billing period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Payment status and timing
    payment_status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Attempt tracking
    payment_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_payment_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(String(500))
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship(back_populates="invoices")


class SubscriptionUsage(Base):
    """Track subscription feature usage for analytics and billing"""
    __tablename__ = "subscription_usage"
    __table_args__ = (
        Index("ix_subscription_usage_subscription", "subscription_id"),
        Index("ix_subscription_usage_feature", "feature_name"),
        Index("ix_subscription_usage_date", "usage_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # References
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    
    # Usage details
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "premium_cards", "tournaments", "storage"
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Extra data
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship()


class SubscriptionDiscount(Base):
    """Discounts applied to subscriptions (coupons, promotions)"""
    __tablename__ = "subscription_discounts"
    __table_args__ = (
        Index("ix_subscription_discounts_subscription", "subscription_id"),
        Index("ix_subscription_discounts_code", "discount_code"),
        Index("ix_subscription_discounts_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # References
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    
    # Discount details
    discount_code: Mapped[str] = mapped_column(String(50), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "percent", "fixed_amount"
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Validity
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Usage limits
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)  # NULL = unlimited
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship()
