"""
Simple SQLAlchemy 1.4 compatible player moderation models
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
    """Player account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING_VERIFICATION = "pending_verification"
    DEACTIVATED = "deactivated"

class BanType(str, Enum):
    """Types of bans"""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    SHADOW = "shadow"
    CHAT_ONLY = "chat_only"
    TOURNAMENT_ONLY = "tournament_only"

class BanReason(str, Enum):
    """Standard ban reasons"""
    CHEATING = "cheating"
    HARASSMENT = "harassment"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM = "spam"
    MULTIPLE_ACCOUNTS = "multiple_accounts"
    PAYMENT_FRAUD = "payment_fraud"
    TERMS_VIOLATION = "terms_violation"
    ADMIN_DISCRETION = "admin_discretion"
    AUTOMATED_DETECTION = "automated_detection"

class WarningType(str, Enum):
    """Types of warnings"""
    VERBAL = "verbal"
    WRITTEN = "written"
    FINAL = "final"
    AUTOMATIC = "automatic"

class ActivityType(str, Enum):
    """Player activity types for logging"""
    LOGIN = "login"
    LOGOUT = "logout"
    GAME_START = "game_start"
    GAME_END = "game_end"
    PURCHASE = "purchase"
    CARD_TRADE = "card_trade"
    TOURNAMENT_JOIN = "tournament_join"
    TOURNAMENT_LEAVE = "tournament_leave"
    CHAT_MESSAGE = "chat_message"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
    EMAIL_CHANGE = "email_change"
    FRIEND_ADD = "friend_add"
    FRIEND_REMOVE = "friend_remove"
    REPORT_SUBMITTED = "report_submitted"
    SUPPORT_TICKET = "support_ticket"

class PlayerLogLevel(str, Enum):
    """Log levels for player activities"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"
    ADMIN = "admin"

# === MODELS ===

class PlayerBan(Base):
    """Player ban tracking and management"""
    __tablename__ = "player_bans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Ban details
    ban_type: Mapped[Optional[str]] = mapped_column(SQLEnum(BanType), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(SQLEnum(BanReason), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Duration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # None for permanent
    
    # Admin context
    banned_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"), nullable=False)
    unbanned_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"))
    unbanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    unban_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Additional restrictions
    restrictions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Custom restrictions
    
    # Appeal system
    appeal_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    appeal_text: Mapped[Optional[str]] = mapped_column(Text)
    appeal_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    appeal_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    appeal_approved: Mapped[Optional[bool]] = mapped_column(Boolean)
    appeal_reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"))
    appeal_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    appeal_response: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    player: Mapped[""Player", foreign_keys=[player_id]"] = relationship("Player", foreign_keys=[player_id])
    banned_by: Mapped[""Admin", foreign_keys=[banned_by_admin_id]"] = relationship("Admin", foreign_keys=[banned_by_admin_id])
    unbanned_by: Mapped[""Admin", foreign_keys=[unbanned_by_admin_id]"] = relationship("Admin", foreign_keys=[unbanned_by_admin_id])
    appeal_reviewer: Mapped[""Admin", foreign_keys=[appeal_reviewed_by]"] = relationship("Admin", foreign_keys=[appeal_reviewed_by])

class PlayerWarning(Base):
    """Player warning system"""
    __tablename__ = "player_warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Warning details
    warning_type: Mapped[Optional[str]] = mapped_column(SQLEnum(WarningType), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Admin context
    issued_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"), nullable=False)
    
    # Escalation tracking
    escalation_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    previous_warning_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player_warnings.id"))
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    player: Mapped[""Player""] = relationship("Player")
    issued_by: Mapped[""Admin""] = relationship("Admin")
    previous_warning: Mapped[""PlayerWarning", remote_side=[id]"] = relationship("PlayerWarning", remote_side=[id])

class PlayerActivityLog(Base):
    """Comprehensive player activity logging"""
    __tablename__ = "player_activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    
    # Activity details
    activity_type: Mapped[Optional[str]] = mapped_column(SQLEnum(ActivityType), nullable=False)
    log_level: Mapped[Optional[str]] = mapped_column(SQLEnum(PlayerLogLevel), default=PlayerLogLevel.INFO, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    
    # Context
    session_id: Mapped[Optional[str]] = mapped_column(String(100))  # Session tracking
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv4/IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    device_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Location (if available)
    country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO country code
    region: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Success/failure tracking
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Performance metrics
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)  # Action duration in milliseconds
    
    # Timestamps
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    player: Mapped[""Player""] = relationship("Player")

class PlayerSecurityLog(Base):
    """Security-specific player logging"""
    __tablename__ = "player_security_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))  # Can be null for failed logins
    
    # Security event details
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)  # login_failed, suspicious_activity, etc.
    severity: Mapped[Optional[str]] = mapped_column(String(20), default="low", nullable=False)  # low, medium, high, critical
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    email_attempted: Mapped[Optional[str]] = mapped_column(String(320))  # For failed login attempts
    
    # Detection details
    detection_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)  # manual, automated, rule_based
    rule_triggered: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Response
    action_taken: Mapped[Optional[str]] = mapped_column(String(200))
    admin_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Timestamps
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    player: Mapped[""Player""] = relationship("Player")

class PlayerReport(Base):
    """Player reporting system"""
    __tablename__ = "player_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Report parties
    reported_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    reporter_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))  # Can be anonymous
    
    # Report details
    report_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)  # harassment, cheating, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Screenshots, videos, etc.
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), default="pending", nullable=False)  # pending, investigating, resolved, dismissed
    priority: Mapped[Optional[str]] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high, urgent
    
    # Admin handling
    assigned_to_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"))
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Context
    match_id: Mapped[Optional[str]] = mapped_column(String(100))  # If report is about a specific match
    chat_log_id: Mapped[Optional[str]] = mapped_column(String(100))  # If report is about chat
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    reported_player: Mapped[""Player", foreign_keys=[reported_player_id]"] = relationship("Player", foreign_keys=[reported_player_id])
    reporter_player: Mapped[""Player", foreign_keys=[reporter_player_id]"] = relationship("Player", foreign_keys=[reporter_player_id])
    assigned_admin: Mapped[""Admin""] = relationship("Admin")

# === HELPER FUNCTIONS ===

def log_player_activity(
    player_id: int,
    activity_type: ActivityType,
    description: str,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    log_level: PlayerLogLevel = PlayerLogLevel.INFO,
    success: bool = True,
    duration_ms: Optional[int] = None
):
    """Log player activity - simplified for testing"""
    print(f"LOG: Player {player_id} - {activity_type.value}: {description}")

def log_security_event(
    event_type: str,
    description: str,
    ip_address: str,
    player_id: Optional[int] = None,
    severity: str = "medium",
    user_agent: Optional[str] = None,
    email_attempted: Optional[str] = None,
    detection_method: str = "automated",
    metadata: Optional[Dict[str, Any]] = None
):
    """Log security event - simplified for testing"""
    print(f"SECURITY: {event_type} - {description} from {ip_address}")

def get_player_ban_status(player_id: int) -> Dict[str, Any]:
    """Get current ban status for a player - simplified for testing"""
    return {'is_banned': False}
