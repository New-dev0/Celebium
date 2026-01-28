"""Configuration (Fingerprint Template) SQLAlchemy model"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Configuration(Base):
    """Configuration model - acts as a template for fingerprints"""

    __tablename__ = "configurations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    
    # Fingerprint Data
    os = Column(String, nullable=False)
    browser = Column(String, nullable=False)
    user_agent = Column(Text, nullable=False)
    screen_resolution = Column(String, nullable=False)
    language = Column(String, nullable=False)
    
    # Hardware
    cpu_cores = Column(Integer, default=8)
    memory_gb = Column(Integer, default=8)
    webgl_vendor = Column(String)
    webgl_renderer = Column(String)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Configuration(id='{self.id}', name='{self.name}')>"
