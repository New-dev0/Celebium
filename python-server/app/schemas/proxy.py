"""Proxy Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProxyBase(BaseModel):
    """Base proxy schema"""
    name: str = Field(..., description="Proxy name")
    type: str = Field(..., description="Proxy type (http, socks5)")
    host: str = Field(..., description="Proxy host")
    port: int = Field(..., description="Proxy port")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")
    change_ip_url: Optional[str] = Field(None, description="Mobile proxy change IP URL")
    notes: Optional[str] = Field(None, description="Notes")


class ProxyCreate(ProxyBase):
    """Schema for proxy creation"""
    pass


class ProxyUpdate(BaseModel):
    """Schema for proxy update (all fields optional)"""
    name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    change_ip_url: Optional[str] = None
    notes: Optional[str] = None


class ProxyResponse(ProxyBase):
    """Schema for proxy in responses"""
    id: str
    last_checked_at: Optional[datetime] = None
    last_ip: Optional[str] = None
    is_working: bool
    created_at: datetime

    class Config:
        from_attributes = True
