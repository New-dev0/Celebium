"""Profile management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.schemas.response import StandardResponse
from app.services.profile_service import ProfileService

from app.services.selenium_manager import SeleniumManager
from app.api.auth import get_current_user

router = APIRouter()
selenium_manager = SeleniumManager()


@router.get("/list")
def list_profiles(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Get all profiles in Undetectable-compatible format

    Returns:
        Dictionary of profile_id -> profile data
    """
    service = ProfileService(db)
    profiles = service.get_all()

    # Convert to Undetectable format
    profiles_dict = {}
    for profile in profiles:
        # Check if actually running to sync status
        real_status = profile.status
        if profile.status == "running" and not selenium_manager.is_running(profile.id):
            real_status = "available"
            service.update_status(profile.id, status=real_status)

        profiles_dict[profile.id] = {
            "name": profile.name,
            "status": real_status.capitalize(),
            "debug_port": profile.debug_port or "",
            "websocket_link": profile.websocket_url or "",
            "folder": profile.folder,
            "tags": profile.tags or [],
            "creation_date": int(profile.created_at.timestamp()) if profile.created_at else 0,
            "modify_date": int(profile.updated_at.timestamp()) if profile.updated_at else 0
        }

    return StandardResponse(
        code=0,
        status="success",
        data=profiles_dict
    )


@router.get("/getinfo/{profile_id}")
def get_profile_info(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get detailed profile information"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": "Profile not found"}
        )

    # Sync status
    if profile.status == "running" and not selenium_manager.is_running(profile_id):
        profile.status = "available"
        service.update_status(profile_id, status="available")

    # Return full profile data
    return StandardResponse(
        code=0,
        status="success",
        data={
            "id": profile.id,
            "name": profile.name,
            "folder": profile.folder,
            "tags": profile.tags or [],
            "os": profile.os,
            "browser": profile.browser,
            "user_agent": profile.user_agent,
            "screen_resolution": profile.screen_resolution,
            "language": profile.language,
            "timezone": profile.timezone,
            "geolocation": profile.geolocation,
            "cpu_cores": profile.cpu_cores,
            "memory_gb": profile.memory_gb,
            "webgl_vendor": profile.webgl_vendor,
            "webgl_renderer": profile.webgl_renderer,
            "proxy_id": profile.proxy_id,
            "proxy_string": profile.proxy_string,
            "webrtc_mode": profile.webrtc_mode,
            "canvas_mode": profile.canvas_mode,
            "audio_mode": profile.audio_mode,
            "notes": profile.notes,
            "type": profile.type,
            "status": profile.status.capitalize(),
            "debug_port": profile.debug_port,
            "websocket_url": profile.websocket_url,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
    )


@router.post("/create")
def create_profile(profile_data: ProfileCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Create a new profile"""
    service = ProfileService(db)

    try:
        profile = service.create(profile_data)

        return StandardResponse(
            code=0,
            status="success",
            data={
                "profile_id": profile.id,
                "name": profile.name
            }
        )
    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.post("/update/{profile_id}")
def update_profile(
    profile_id: str,
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update an existing profile"""
    service = ProfileService(db)

    try:
        profile = service.update(profile_id, profile_data)

        if not profile:
            return StandardResponse(
                code=1,
                status="error",
                data={"error": "Profile not found"}
            )

        return StandardResponse(code=0, status="success", data={})

    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.get("/delete/{profile_id}")
def delete_profile(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Delete a profile"""
    service = ProfileService(db)

    # Stop profile if running
    if selenium_manager.is_running(profile_id):
        try:
            selenium_manager.stop_profile(profile_id)
        except:
            pass

    success = service.delete(profile_id)

    if success:
        return StandardResponse(code=0, status="success", data={})
    else:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": "Profile not found"}
        )


@router.get("/start/{profile_id}")
def start_profile(
    profile_id: str,
    chrome_flags: Optional[str] = "",
    start_pages: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Start a browser profile

    Args:
        profile_id: Profile ID to start
        chrome_flags: Optional Chrome flags (space separated)
        start_pages: Optional comma-separated URLs to open
    """
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": "Profile not found"}
        )

    try:
        # Launch with SeleniumBase
        result = selenium_manager.start_profile(
            profile=profile,
            chrome_flags=chrome_flags.split() if chrome_flags else [],
            start_pages=start_pages.split(',') if start_pages else []
        )

        # Update profile status
        service.update_status(
            profile_id,
            status="running",
            debug_port=result["debug_port"],
            websocket_url=result["websocket_link"],
            pid=result["pid"]
        )

        return StandardResponse(
            code=0,
            status="success",
            data={
                "name": profile.name,
                "debug_port": result["debug_port"],
                "websocket_link": result["websocket_link"],
                "folder": profile.folder,
                "tags": profile.tags
            }
        )
    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.get("/stop/{profile_id}")
def stop_profile(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Stop a running profile"""
    service = ProfileService(db)
    
    if not selenium_manager.is_running(profile_id):
        # Even if not in manager, update DB if it says running
        service.update_status(
            profile_id,
            status="available",
            debug_port=None,
            websocket_url=None,
            pid=None
        )
        return StandardResponse(code=0, status="success", data={})

    try:
        selenium_manager.stop_profile(profile_id)

        service.update_status(
            profile_id,
            status="available",
            debug_port=None,
            websocket_url=None,
            pid=None
        )

        return StandardResponse(code=0, status="success", data={})
    except Exception as e:
        return StandardResponse(code=1, status="error", data={"error": str(e)})


@router.get("/clearcache/{profile_id}")
def clear_cache(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Clear profile browser cache"""
    import shutil
    import os
    from app.core.config import settings

    profile_dir = os.path.join(settings.PROFILES_DIR, f"profile_{profile_id}")
    cache_dir = os.path.join(profile_dir, "Default", "Cache")

    try:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)

        return StandardResponse(code=0, status="success", data={})
    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.get("/cleardata/{profile_id}")
def clear_data(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Clear all profile data (cookies, cache, history)"""
    import shutil
    import os
    from app.core.config import settings

    profile_dir = os.path.join(settings.PROFILES_DIR, f"profile_{profile_id}")

    try:
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir)

        # Clear cookies in database
        service = ProfileService(db)
        service.update(profile_id, ProfileUpdate(cookies=None, notes=None))

        return StandardResponse(code=0, status="success", data={})
    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.get("/getinfo/{profile_id}")
def get_profile_info_undetectable(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get detailed profile information in Undetectable format"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(code=1, status="error", data={"error": "Profile not found"})

    # Check if actually running
    real_status = profile.status
    if profile.status == "running" and not selenium_manager.is_running(profile.id):
        real_status = "available"
        service.update_status(profile.id, status=real_status)

    data = {
        "name": profile.name,
        "status": real_status.capitalize(),
        "debug_port": str(profile.debug_port) if profile.debug_port else "",
        "websocket_link": profile.websocket_url or "",
        "configid": profile.config_id or "id",
        "cloud_id": "",
        "type": profile.type,
        "stealth_tier": profile.stealth_tier,
        "adblock_enabled": profile.adblock_enabled,
        "proxy": profile.proxy_string or "",
        "folder": profile.folder,
        "tags": profile.tags or [],
        "notes": profile.notes or "",
        "useragent": profile.user_agent,
        "browser": profile.browser,
        "os": profile.os,
        "screen": profile.screen_resolution,
        "language": profile.language,
        "cpu": profile.cpu_cores,
        "memory": profile.memory_gb,
        "creation_date": int(profile.created_at.timestamp()) if profile.created_at else 0,
        "modify_date": int(profile.updated_at.timestamp()) if profile.updated_at else 0
    }

    return StandardResponse(code=0, status="success", data=data)


@router.get("/mfa/{profile_id}")
def get_mfa_code(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get current TOTP code for the profile"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(code=1, status="error", data={"error": "Profile not found"})

    if not profile.mfa_secret:
        return StandardResponse(code=1, status="error", data={"error": "No MFA secret configured"})

    from app.services.mfa_service import MFAService
    code = MFAService.generate_totp(profile.mfa_secret)
    
    if not code:
        return StandardResponse(code=1, status="error", data={"error": "Invalid MFA secret"})

    return StandardResponse(code=0, status="success", data={"code": code})


@router.get("/click/{profile_id}")
def cdp_click(profile_id: str, selector: str, current_user=Depends(get_current_user)):
    """Perform a trusted click via CDP"""
    if not selenium_manager.is_running(profile_id):
        return StandardResponse(code=1, status="error", data={"error": "Profile is not running"})
    
    try:
        selenium_manager.cdp_click(profile_id, selector)
        return StandardResponse(code=0, status="success", data={})
    except Exception as e:
        return StandardResponse(code=1, status="error", data={"error": str(e)})


@router.get("/type/{profile_id}")
def cdp_type(profile_id: str, selector: str, text: str, current_user=Depends(get_current_user)):
    """Perform trusted typing via CDP"""
    if not selenium_manager.is_running(profile_id):
        return StandardResponse(code=1, status="error", data={"error": "Profile is not running"})
    
    try:
        selenium_manager.cdp_type(profile_id, selector, text)
        return StandardResponse(code=0, status="success", data={})
    except Exception as e:
        return StandardResponse(code=1, status="error", data={"error": str(e)})


@router.get("/updatebrowser/{profile_id}")
def update_browser(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Update profile browser version (stub)"""
    return StandardResponse(code=0, status="success", data={})


@router.get("/cookies/{profile_id}")
def get_cookies(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Get profile cookies"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(code=1, status="error", data={"error": "Profile not found"})

    import json
    cookies_list = []
    if profile.cookies:
        try:
            cookies_list = json.loads(profile.cookies)
        except:
            pass

    return StandardResponse(code=0, status="success", data={"cookies": cookies_list})


@router.get("/clearcookies/{profile_id}")
def clear_cookies(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Clear only cookies for the profile"""
    service = ProfileService(db)
    service.update(profile_id, ProfileUpdate(cookies=None))
    
    # Also need to delete cookies from the browser profile directory if it exists
    import os
    from app.core.config import settings
    profile_dir = os.path.join(settings.PROFILES_DIR, f"profile_{profile_id}")
    cookies_file = os.path.join(profile_dir, "Default", "Cookies")
    
    if os.path.exists(cookies_file):
        try:
            os.remove(cookies_file)
        except:
            pass

    return StandardResponse(code=0, status="success", data={})


@router.get("/checkconnection/{profile_id}")
def check_connection(profile_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Check proxy connection in profile"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(code=1, status="error", data={"error": "Profile not found"})

    if not profile.proxy_string and not profile.proxy_id:
        return StandardResponse(code=1, status="error", data={"error": "No proxy configured"})

    # Simple stub for connection check
    return StandardResponse(code=0, status="success", data={"ip": "127.0.0.1"})


@router.post("/import")
def import_profiles(data: dict, current_user=Depends(get_current_user)):
    """Import profiles (stub)"""
    return StandardResponse(code=0, status="success", data={})


@router.post("/export")
def export_profiles(data: dict, current_user=Depends(get_current_user)):
    """Export profiles (stub)"""
    return StandardResponse(code=0, status="success", data={})
