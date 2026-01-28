"""Profile SQLAlchemy model"""
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Profile(Base):
    """Browser profile model with fingerprint and privacy settings"""

    __tablename__ = "profiles"

    # Primary Key
    id = Column(String, primary_key=True)

    # Basic Info
    name = Column(String, nullable=False)
    folder = Column(String, default='Default')
    tags = Column(Text)  # JSON array: ["tag1", "tag2"]

    # Browser Configuration
    os = Column(String, nullable=False)  # "Windows 10", "Mac OS X 14.7"
    browser = Column(String, nullable=False)  # "Chrome 120.0.0.0"
    user_agent = Column(String, nullable=False)
    screen_resolution = Column(String, nullable=False)  # "1920x1080"
    language = Column(String, nullable=False)  # "en-US,en;q=0.9"
    timezone = Column(String)  # "America/New_York"
    geolocation = Column(String)  # "40.7128,-74.0060" (lat,long)

    # Hardware Fingerprint
    cpu_cores = Column(Integer, default=8)
    memory_gb = Column(Integer, default=8)
    webgl_vendor = Column(String)
    webgl_renderer = Column(String)

    # Proxy Configuration
    proxy_id = Column(String, ForeignKey('proxies.id'))
    proxy_string = Column(String)  # Direct: "socks5://user:pass@host:port"

    # Privacy Settings
    webrtc_mode = Column(String, default='altered')  # 'altered', 'disabled', 'real'
    canvas_mode = Column(String, default='noise')  # 'noise', 'block', 'off'
    audio_mode = Column(String, default='noise')

    # Storage
    cookies = Column(Text)  # JSON array of cookie objects
    local_storage = Column(Text)  # JSON object
    notes = Column(Text)

    # Profile Type and Tier
    type = Column(String, default='local')  # 'local', 'cloud'
    stealth_tier = Column(String, default='standard')  # 'standard', 'elite'
    config_id = Column(String)  # Reference to fingerprint template

    # Advanced Features
    adblock_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String)  # Encrypted TOTP secret

    # Runtime Status
    status = Column(String, default='available')  # 'available', 'running', 'locked'
    debug_port = Column(Integer)  # Port when running
    websocket_url = Column(String)  # WebSocket endpoint when running
    pid = Column(Integer)  # Chrome process ID when running

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_used_at = Column(TIMESTAMP)

    def __repr__(self) -> str:
        return f"<Profile(id='{self.id}', name='{self.name}', status='{self.status}')>"
