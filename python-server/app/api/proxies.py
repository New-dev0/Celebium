"""Proxy API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.core.database import get_db
from app.services.proxy_service import ProxyService
from app.schemas.proxy import ProxyCreate, ProxyUpdate
from app.schemas.response import StandardResponse

from app.api.auth import get_current_user

router = APIRouter()

@router.get("/list")
def list_proxies(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Returns a list of proxies in the format expected by the JSON reference"""
    service = ProxyService(db)
    proxies = service.get_all()
    
    # Format according to undetectable_api.json
    data = {}
    for p in proxies:
        data[p.id] = {
            "host": p.host,
            "login": p.username or "",
            "name": p.name,
            "password": p.password or "",
            "port": p.port,
            "type": p.type,
            "ipchangelink": p.change_ip_url or ""
        }
    
    return StandardResponse(code=0, status="success", data=data)

@router.post("/add")
def add_proxy(proxy_data: ProxyCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add a new proxy"""
    service = ProxyService(db)
    proxy = service.create(proxy_data)
    
    return StandardResponse(
        code=0, 
        status="success", 
        data={"proxy_id": proxy.id}
    )

@router.get("/delete/{proxy_id}")
def delete_proxy(proxy_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete a proxy by ID"""
    service = ProxyService(db)
    success = service.delete(proxy_id)
    
    if not success:
        return StandardResponse(code=1, status="error", data={"error": "Invalid proxy id!"})
        
    return StandardResponse(code=0, status="success", data={})

@router.post("/update/{proxy_id}")
def update_proxy(proxy_id: str, proxy_data: ProxyUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update proxy information"""
    service = ProxyService(db)
    proxy = service.update(proxy_id, proxy_data)
    
    if not proxy:
        return StandardResponse(code=1, status="error", data={"error": "Invalid proxy id!"})
        
    return StandardResponse(code=0, status="success", data={})
