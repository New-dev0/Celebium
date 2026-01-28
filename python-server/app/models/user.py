"""User SQLAlchemy model for authentication"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """Local user model for API authentication"""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP)

    def __repr__(self) -> str:
        return f"<User(username='{self.username}')>"
