"""Database setup and connection management"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app.core.config import settings


# Create database URL
DATABASE_PATH = settings.DATABASE_PATH
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db() -> None:
    """Initialize database and create all tables"""
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Import all models here so they are registered with Base
    from app.models.profile import Profile
    from app.models.proxy import Proxy
    from app.models.user import User
    from app.models.folder import Folder
    from app.models.configuration import Configuration

    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency for FastAPI routes to get database session.

    Usage:
        @app.get("/profiles")
        def list_profiles(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
