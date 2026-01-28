"""System API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.response import StandardResponse
import os
import signal

from app.api.auth import get_current_user
from app.services.metadata_service import MetadataService
from app.schemas.metadata import FolderCreate, ConfigurationCreate

router = APIRouter()


@router.get("/status")
def get_status():
    """Check if server is running"""
    return StandardResponse(
        code=0,
        status="success",
        data={}
    )


@router.get("/close")
def close_server():
    """Shutdown server gracefully"""
    # This will be called by Electron on quit
    os.kill(os.getpid(), signal.SIGTERM)

    return StandardResponse(
        code=0,
        status="success",
        data={"message": "Server shutting down"}
    )


@router.get("/timezoneslist")
def get_timezones(current_user=Depends(get_current_user)):
    """Return list of all timezones"""
    import pytz
    from datetime import datetime

    timezones = {}
    for tz in pytz.all_timezones:
        try:
            tz_obj = pytz.timezone(tz)
            offset = datetime.now(tz_obj).strftime('%z')
            # Format as GMT+X:XX
            if offset:
                hours = int(offset[:3])
                minutes = offset[3:]
                timezones[tz] = f"GMT{'+' if hours >= 0 else ''}{hours}:{minutes}"
            else:
                timezones[tz] = "GMT+0:00"
        except:
            timezones[tz] = "GMT+0:00"

    return StandardResponse(
        code=0,
        status="success",
        data=timezones
    )


@router.get("/folderslist")
def get_folders(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return list of profile folders from DB"""
    service = MetadataService(db)
    folders = service.get_all_folders()
    return StandardResponse(
        code=0,
        status="success",
        data=[f.name for f in folders] or ["Default"]
    )


@router.post("/folders/add")
def add_folder(folder_data: FolderCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Add a new profile folder"""
    service = MetadataService(db)
    folder = service.create_folder(folder_data)
    return StandardResponse(code=0, status="success", data={"id": folder.id})


@router.get("/groupslist")
def get_groups(current_user=Depends(get_current_user)):
    """Returns a list of Groups (Cloud folders stub)"""
    groups = ["Main Group"]
    return StandardResponse(
        code=0,
        status="success",
        data={"groups": groups}
    )


@router.get("/configslist")
def get_configs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Returns a list of configurations (templates) from DB"""
    service = MetadataService(db)
    configs = service.get_all_configs()
    
    # Format for Undetectable
    data = {}
    for c in configs:
        data[c.id] = {
            "browser": c.browser,
            "os": c.os,
            "screen": c.screen_resolution,
            "useragent": c.user_agent,
            "webgl": c.webgl_renderer or ""
        }
    
    # If empty, provide some defaults from FingerprintService
    if not data:
        from app.services.fingerprint_service import FingerprintService
        data = FingerprintService.get_predefined_configs()
        
    return StandardResponse(code=0, status="success", data=data)


@router.post("/configs/add")
def add_config(config_data: ConfigurationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Save a new fingerprint configuration template"""
    service = MetadataService(db)
    config = service.create_config(config_data)
    return StandardResponse(code=0, status="success", data={"id": config.id})


@router.get("/list")
def list_all_profiles(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Global list endpoint"""
    from app.api.profiles import list_profiles
    return list_profiles(db, current_user)
