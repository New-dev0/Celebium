"""Proxy SQLAlchemy model"""
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Proxy(Base):
    """Proxy server model for centralized management"""

    __tablename__ = "proxies"

    # Primary Key
    id = Column(String, primary_key=True)

    # Basic Info
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'http', 'https', 'socks5'
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String)
    password = Column(String)

    # Mobile Proxy Support
    change_ip_url = Column(String)  # URL to trigger IP rotation

    # Status
    last_checked_at = Column(TIMESTAMP)
    last_ip = Column(String)  # Last detected IP address
    is_working = Column(Boolean, default=True)

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    notes = Column(Text)

    def __repr__(self) -> str:
        return f"<Proxy(id='{self.id}', name='{self.name}', type='{self.type}')>"

    def to_connection_string(self) -> str:
        """Convert proxy to connection string format"""
        if self.username and self.password:
            return f"{self.type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.type}://{self.host}:{self.port}"
