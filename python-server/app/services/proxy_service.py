"""Proxy service - Business logic for proxy management"""
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.proxy import Proxy
from app.schemas.proxy import ProxyCreate, ProxyUpdate


class ProxyService:
    """Handle proxy CRUD operations and business logic"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Proxy]:
        """Get all proxies"""
        return self.db.query(Proxy).all()

    def get_by_id(self, proxy_id: str) -> Optional[Proxy]:
        """Get proxy by ID"""
        return self.db.query(Proxy).filter(Proxy.id == proxy_id).first()

    def create(self, proxy_data: ProxyCreate) -> Proxy:
        """Create a new proxy"""
        proxy = Proxy(
            id=str(uuid.uuid4().int % 1000000000),  # Matches the integer-like ID format in the JSON
            **proxy_data.model_dump()
        )
        self.db.add(proxy)
        self.db.commit()
        self.db.refresh(proxy)
        return proxy

    def update(self, proxy_id: str, proxy_data: ProxyUpdate) -> Optional[Proxy]:
        """Update an existing proxy"""
        proxy = self.get_by_id(proxy_id)
        if not proxy:
            return None

        update_data = proxy_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(proxy, key, value)

        self.db.commit()
        self.db.refresh(proxy)
        return proxy

    def delete(self, proxy_id: str) -> bool:
        """Delete a proxy"""
        proxy = self.get_by_id(proxy_id)
        if not proxy:
            return False

        self.db.delete(proxy)
        self.db.commit()
        return True

    def check_connection(self, proxy_id: str) -> dict:
        """
        Check proxy connection (stub)
        In a real scenario, this would perform an HTTP request via the proxy
        """
        proxy = self.get_by_id(proxy_id)
        if not proxy:
            return {"error": "Proxy not found"}
        
        # Stub result
        return {"ip": proxy.host if proxy.host != "127.0.0.1" else "84.22.11.5", "working": True}
