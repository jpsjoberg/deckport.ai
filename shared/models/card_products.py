"""
Card Products Model
Represents the production/catalog layer of the 3-tier card system
"""

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
):
    return datetime.now(timezone.utc)

class CardProduct(Base):
    """
    TIER 2: Card Products (Production/Catalog Layer)
    Final cards with generated graphics - THIS IS THE CARD CATALOG
    """
    __tablename__ = "card_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("card_templates.id", ondelete="RESTRICT"))
    card_set_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("card_sets.id", ondelete="CASCADE"))
    
    # Product Identity
    product_sku: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    flavor_text: Mapped[Optional[str]] = mapped_column(Text)
    display_label: Mapped[Optional[str]] = mapped_column(String(40))
    
    # Final Card Properties
    rarity: Mapped[Optional[str]] = mapped_column(String(20), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=False)
    color_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Final Game Mechanics
    base_stats: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    attachment_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    duration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    token_spec: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    reveal_trigger: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Generated Assets
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    art_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    # Production Status
    is_published: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_printable: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    print_quality_approved: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    # Catalog Info
    release_date: Mapped[Optional[Any]] = mapped_column(Date)
    retirement_date: Mapped[Optional[Any]] = mapped_column(Date)
    print_run_size: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    # Relationships (using string references to avoid circular imports)
    # template: Mapped[""CardTemplate", back_populates="products"CardTemplate", back_populates="products"CardSet", back_populates="products"CardSet", back_populates="products"NFCCard", back_populates="product"NFCCard", back_populates="product""Card Sets/Collections"""
    __tablename__ = "card_sets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    release_date: Mapped[Optional[Any]] = mapped_column(Date)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    # Relationships
    # templates: Mapped[""CardTemplate", back_populates="card_set"CardTemplate", back_populates="card_set"CardProduct", back_populates="card_set"CardProduct", back_populates="card_set")
