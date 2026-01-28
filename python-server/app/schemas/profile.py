"""Pydantic schemas for Profile API validation"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProfileBase(BaseModel):
    """Base profile schema with common fields"""

    name: str = Field(..., min_length=1, max_length=100)
    folder: str = "Default"
    tags: Optional[List[str]] = []

    # Browser Configuration
    os: str
    browser: str
    user_agent: str
    screen_resolution: str
    language: str = "en-US,en;q=0.9"
    timezone: Optional[str] = None
    geolocation: Optional[str] = None

    # Hardware Fingerprint
    cpu_cores: int = 8
    memory_gb: int = 8
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None

    # Proxy Configuration
    proxy_id: Optional[str] = None
    proxy_string: Optional[str] = None
    proxy: Optional[str] = None # For compatibility with Undetectable API (can be ID or string)

    # Privacy Settings
    webrtc_mode: str = "altered"
    canvas_mode: str = "noise"
    audio_mode: str = "noise"

    # Additional Fields
    notes: Optional[str] = None
    type: str = "local"
    stealth_tier: str = "standard"
    config_id: Optional[str] = None
    adblock_enabled: bool = False
    mfa_secret: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile"""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile (all fields optional)"""

    name: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    proxy_id: Optional[str] = None
    proxy_string: Optional[str] = None
    proxy: Optional[str] = None
    notes: Optional[str] = None
    timezone: Optional[str] = None
    geolocation: Optional[str] = None
    stealth_tier: Optional[str] = None
    adblock_enabled: Optional[bool] = None
    mfa_secret: Optional[str] = None


class ProfileResponse(ProfileBase):
    """Schema for profile responses (includes runtime fields)"""

    id: str
    status: str
    debug_port: Optional[int] = None
    websocket_url: Optional[str] = None
    pid: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
