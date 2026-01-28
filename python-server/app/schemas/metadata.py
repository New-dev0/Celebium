"""Folder and Configuration Schemas"""
from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime


class FolderBase(BaseModel):
    name: str

class FolderCreate(FolderBase):
    pass

class FolderResponse(FolderBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigBase(BaseModel):
    name: str
    os: str
    browser: str
    user_agent: str
    screen_resolution: str
    language: str
    cpu_cores: int = 8
    memory_gb: int = 8
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None

class ConfigurationCreate(ConfigBase):
    pass

class ConfigurationResponse(ConfigBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
