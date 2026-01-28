"""Application configuration using pydantic-settings"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    API_PORT: int = 25325
    API_HOST: str = "127.0.0.1"

    # Database
    DATABASE_PATH: str = "./database/celebium.db"

    # Profiles
    PROFILES_DIR: str = "./profiles"
    MAX_CONCURRENT_PROFILES: int = 10

    # SeleniumBase
    DEFAULT_BROWSER: str = "chrome"
    CHROMEDRIVER_PATH: Optional[str] = None

    # Proxy
    PROXY_CHECK_TIMEOUT: int = 10

    # Security
    SECRET_KEY: str = "super_secret_celebium_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week default

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
