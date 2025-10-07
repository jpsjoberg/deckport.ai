"""
Enhanced Console Models
Adds location tracking, version management, and health monitoring to console system
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, BigInteger, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

from .base import Base, utcnow


class LocationSource(str, Enum):
    """Source of location data"""
    manual = "manual"      # Manually entered by admin
    gps = "gps"           # GPS coordinates from device
    ip = "ip"             # Estimated from IP address
    network = "network"   # Network-based location


class HealthStatus(str, Enum):
    """Console health status"""
    healthy = "healthy"     # All systems normal
    warning = "warning"     # Minor issues detected
    critical = "critical"   # Major issues requiring attention
    unknown = "unknown"     # Status not determined


class UpdateStatus(str, Enum):
    """Update status for version tracking"""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class VersionType(str, Enum):
    """Type of version being tracked"""
    software = "software"
    hardware = "hardware"
    firmware = "firmware"


class UpdateMethod(str, Enum):
    """Method used for update"""
    automatic = "automatic"
    manual = "manual"
    forced = "forced"


class ProductCategory(Base):
    """Product category for shop organization"""
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_product_categories_slug"),
        Index("ix_product_categories_slug", "slug"),
        Index("ix_product_categories_parent", "parent_id"),
        Index("ix_product_categories_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_categories.id", ondelete="CASCADE"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    banner_url: Mapped[Optional[str]] = mapped_column(String(500))
    category_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    parent: Mapped[Optional["ProductCategory"]] = relationship("ProductCategory", remote_side=[id], back_populates="children")
    children: Mapped[List["ProductCategory"]] = relationship("ProductCategory", back_populates="parent")
    # Note: products relationship will be added when ShopProduct model is updated with category_id


class ConsoleLocationHistory(Base):
    """History of console location changes"""
    __tablename__ = "console_location_history"
    __table_args__ = (
        Index("ix_console_location_history_console", "console_id"),
        Index("ix_console_location_history_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    console_id: Mapped[int] = mapped_column(ForeignKey("consoles.id", ondelete="CASCADE"), nullable=False)
    location_name: Mapped[Optional[str]] = mapped_column(String(255))
    location_address: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=8))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(precision=11, scale=8))
    source: Mapped[LocationSource] = mapped_column(String(50), nullable=False)
    accuracy_meters: Mapped[Optional[float]] = mapped_column(Float)
    changed_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"))
    change_reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    console: Mapped["Console"] = relationship()
    changed_by_admin: Mapped[Optional["Admin"]] = relationship()


class ConsoleVersionHistory(Base):
    """History of console version updates"""
    __tablename__ = "console_version_history"
    __table_args__ = (
        Index("ix_console_version_history_console", "console_id"),
        Index("ix_console_version_history_status", "update_status"),
        Index("ix_console_version_history_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    console_id: Mapped[int] = mapped_column(ForeignKey("consoles.id", ondelete="CASCADE"), nullable=False)
    version_type: Mapped[VersionType] = mapped_column(String(20), nullable=False)
    old_version: Mapped[Optional[str]] = mapped_column(String(50))
    new_version: Mapped[str] = mapped_column(String(50), nullable=False)
    update_method: Mapped[UpdateMethod] = mapped_column(String(20), nullable=False)
    update_status: Mapped[UpdateStatus] = mapped_column(String(20), nullable=False)
    update_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    update_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    initiated_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"))
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    console: Mapped["Console"] = relationship()
    initiated_by_admin: Mapped[Optional["Admin"]] = relationship()


# Enhanced Console model fields (to be added to existing Console class)
class ConsoleEnhancements:
    """Mixin for enhanced Console fields - add these to the main Console model"""
    
    # Location tracking
    location_name: Mapped[Optional[str]] = mapped_column(String(255))
    location_address: Mapped[Optional[str]] = mapped_column(Text)
    location_latitude: Mapped[Optional[float]] = mapped_column(Numeric(precision=10, scale=8))
    location_longitude: Mapped[Optional[float]] = mapped_column(Numeric(precision=11, scale=8))
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    location_source: Mapped[Optional[LocationSource]] = mapped_column(String(50))
    
    # Version management
    software_version: Mapped[Optional[str]] = mapped_column(String(50))
    hardware_version: Mapped[Optional[str]] = mapped_column(String(50))
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50))
    last_update_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    update_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_update_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Health and activity monitoring
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    health_status: Mapped[HealthStatus] = mapped_column(String(20), default=HealthStatus.unknown, nullable=False)
    uptime_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    memory_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    disk_usage_percent: Mapped[Optional[float]] = mapped_column(Float)
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float)
    network_latency_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Additional indexes for enhanced fields
    __table_args__ = (
        Index("ix_consoles_location", "location_latitude", "location_longitude"),
        Index("ix_consoles_health", "health_status"),
        Index("ix_consoles_version", "software_version"),
        Index("ix_consoles_heartbeat", "last_heartbeat"),
    )

    # Additional relationships for enhanced features
    location_history: Mapped[List[ConsoleLocationHistory]] = relationship(back_populates="console")
    version_history: Mapped[List[ConsoleVersionHistory]] = relationship(back_populates="console")


# Enhanced ShopProduct fields (to be added to existing ShopProduct model)
class ShopProductEnhancements:
    """Mixin for enhanced ShopProduct fields"""
    
    # Category relationship
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_categories.id", ondelete="SET NULL"))
    
    # Relationship
    category: Mapped[Optional[ProductCategory]] = relationship(back_populates="products")
    
    # Additional index
    __table_args__ = (
        Index("ix_shop_products_category", "category_id"),
    )
