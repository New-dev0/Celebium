"""Folder SQLAlchemy model"""
from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class Folder(Base):
    """Folder model for organizing profiles"""

    __tablename__ = "folders"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Folder(id='{self.id}', name='{self.name}')>"
