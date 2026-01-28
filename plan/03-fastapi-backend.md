# FastAPI Backend Architecture

## Server Structure

```
python-server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   ├── profiles.py           # /profile/* endpoints
│   │   ├── proxies.py            # /proxies/* endpoints
│   │   ├── configs.py            # /configs/* endpoints
│   │   └── system.py             # /status, /close, etc.
│   │
│   ├── core/                      # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Settings
│   │   ├── database.py           # DB connection
│   │   └── security.py           # Auth (future)
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   ├── proxy.py
│   │   └── fingerprint.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   ├── proxy.py
│   │   └── response.py
│   │
│   └── services/                  # Business logic
│       ├── __init__.py
│       ├── profile_service.py    # Profile CRUD
│       ├── selenium_manager.py   # SeleniumBase integration
│       ├── fingerprint_service.py
│       └── proxy_service.py
│
├── tests/                         # Pytest tests
│   ├── test_profiles.py
│   ├── test_proxies.py
│   └── test_selenium.py
│
├── requirements.txt
├── pyproject.toml
└── .env
```

---

## Main Application Entry

**File: `app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.core.database import init_db
from app.api import profiles, proxies, configs, system

# Initialize FastAPI app
app = FastAPI(
    title="Celebium API",
    description="Browser Profile Manager with SeleniumBase Integration",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"
)

# CORS middleware (allow Electron app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:25325"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database initialized")
    print(f"🚀 Server running on http://127.0.0.1:25325")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Close all running profiles
    from app.services.selenium_manager import SeleniumManager
    manager = SeleniumManager()
    manager.close_all()
    print("🛑 Server shutting down")

# Include API routes
app.include_router(system.router, prefix="", tags=["System"])
app.include_router(profiles.router, prefix="/profile", tags=["Profiles"])
app.include_router(proxies.router, prefix="/proxies", tags=["Proxies"])
app.include_router(configs.router, prefix="/configs", tags=["Configs"])

# Root endpoint
@app.get("/")
def read_root():
    return {
        "name": "Celebium API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 25325))
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,  # Dev mode only
        log_level="info"
    )
```

---

## API Endpoints

### System Routes

**File: `app/api/system.py`**

```python
from fastapi import APIRouter
from app.schemas.response import StandardResponse

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
    """Shutdown server (called by Electron on quit)"""
    import os
    import signal

    # Graceful shutdown
    os.kill(os.getpid(), signal.SIGTERM)

    return StandardResponse(
        code=0,
        status="success",
        data={"message": "Server closing"}
    )

@router.get("/timezoneslist")
def get_timezones():
    """Return list of timezones"""
    import pytz
    timezones = {tz: f"GMT{datetime.now(pytz.timezone(tz)).strftime('%z')}"
                 for tz in pytz.all_timezones}
    return StandardResponse(code=0, status="success", data=timezones)
```

---

### Profile Routes

**File: `app/api/profiles.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.schemas.response import StandardResponse
from app.services.profile_service import ProfileService
from app.services.selenium_manager import SeleniumManager

router = APIRouter()
selenium_manager = SeleniumManager()


@router.get("/list")
def list_profiles(db: Session = Depends(get_db)):
    """Get all profiles"""
    service = ProfileService(db)
    profiles = service.get_all()

    # Convert to dict format like Undetectable
    profiles_dict = {
        profile.id: {
            "name": profile.name,
            "status": profile.status,
            "debug_port": profile.debug_port or "",
            "websocket_link": profile.websocket_url or "",
            "folder": profile.folder,
            "tags": profile.tags,
            "creation_date": int(profile.created_at.timestamp()),
            "modify_date": int(profile.updated_at.timestamp())
        }
        for profile in profiles
    }

    return StandardResponse(code=0, status="success", data=profiles_dict)


@router.get("/getinfo/{profile_id}")
def get_profile_info(profile_id: str, db: Session = Depends(get_db)):
    """Get detailed profile info"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": "Profile not found"}
        )

    return StandardResponse(
        code=0,
        status="success",
        data=ProfileResponse.from_orm(profile).dict()
    )


@router.post("/create")
def create_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db)
):
    """Create new profile"""
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
    db: Session = Depends(get_db)
):
    """Update profile"""
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
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    """Delete profile"""
    service = ProfileService(db)

    # Stop if running
    if profile_id in selenium_manager.running_profiles:
        selenium_manager.stop_profile(profile_id)

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
    chrome_flags: str = "",
    start_pages: str = "",
    db: Session = Depends(get_db)
):
    """Start browser profile"""
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

        # Update profile status in DB
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
def stop_profile(profile_id: str, db: Session = Depends(get_db)):
    """Stop browser profile"""
    try:
        selenium_manager.stop_profile(profile_id)

        # Update DB status
        service = ProfileService(db)
        service.update_status(
            profile_id,
            status="available",
            debug_port=None,
            websocket_url=None,
            pid=None
        )

        return StandardResponse(code=0, status="success", data={})

    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.get("/checkconnection/{profile_id}")
def check_connection(profile_id: str, db: Session = Depends(get_db)):
    """Check proxy connection and get IP"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile or not profile.proxy_string:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": "No proxy configured"}
        )

    try:
        # Test proxy connection
        import requests
        proxies = {
            "http": profile.proxy_string,
            "https": profile.proxy_string
        }
        response = requests.get(
            "https://api.ipify.org?format=json",
            proxies=proxies,
            timeout=10
        )
        ip = response.json()["ip"]

        return StandardResponse(
            code=0,
            status="success",
            data={"ip": ip}
        )

    except Exception as e:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": str(e)}
        )


@router.get("/cookies/{profile_id}")
def get_cookies(profile_id: str, db: Session = Depends(get_db)):
    """Get profile cookies"""
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        return StandardResponse(
            code=1,
            status="error",
            data={"error": "Profile not found"}
        )

    import json
    cookies = json.loads(profile.cookies) if profile.cookies else []

    return StandardResponse(
        code=0,
        status="success",
        data={"cookies": cookies}
    )


@router.get("/clearcache/{profile_id}")
def clear_cache(profile_id: str, db: Session = Depends(get_db)):
    """Clear profile cache"""
    import shutil
    import os

    profile_dir = f"./profiles/profile_{profile_id}"
    cache_dir = os.path.join(profile_dir, "Default", "Cache")

    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)

    return StandardResponse(code=0, status="success", data={})


@router.get("/cleardata/{profile_id}")
def clear_data(profile_id: str, db: Session = Depends(get_db)):
    """Clear all profile data"""
    import shutil

    profile_dir = f"./profiles/profile_{profile_id}"

    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir)

    # Clear cookies in DB
    service = ProfileService(db)
    service.update(profile_id, ProfileUpdate(cookies=None, notes=None))

    return StandardResponse(code=0, status="success", data={})
```

---

## Standard Response Format

**File: `app/schemas/response.py`**

```python
from pydantic import BaseModel
from typing import Any, Optional

class StandardResponse(BaseModel):
    """Undetectable-compatible response format"""
    code: int  # 0 = success, 1 = error
    status: str  # "success" or "error"
    data: Any  # Response data or error object

    @classmethod
    def success(cls, data: Any = None):
        return cls(code=0, status="success", data=data or {})

    @classmethod
    def error(cls, message: str):
        return cls(code=1, status="error", data={"error": message})
```

---

## Configuration

**File: `app/core/config.py`**

```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API
    API_PORT: int = 25325
    API_HOST: str = "127.0.0.1"

    # Database
    DATABASE_PATH: str = "./database/celebium.db"

    # Profiles
    PROFILES_DIR: str = "./profiles"
    MAX_CONCURRENT_PROFILES: int = 10

    # SeleniumBase
    DEFAULT_BROWSER: str = "chrome"
    CHROMEDRIVER_PATH: str = ""  # Auto-download if empty

    # Proxy
    PROXY_CHECK_TIMEOUT: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**File: `.env`**

```env
API_PORT=25325
DATABASE_PATH=./database/celebium.db
PROFILES_DIR=./profiles
MAX_CONCURRENT_PROFILES=10
```

---

## Dependencies

**File: `requirements.txt`**

```txt
# Web Framework
fastapi==0.110.0
uvicorn[standard]==0.27.1
pydantic==2.6.1
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.27
alembic==1.13.1

# Automation
seleniumbase==4.26.0

# Utilities
python-dotenv==1.0.1
psutil==5.9.8
requests==2.31.0
pytz==2024.1

# Development
pytest==8.0.0
black==24.2.0
mypy==1.8.0
```

---

## Running the Server

```bash
# Development mode (auto-reload)
cd python-server
python -m app.main

# Production mode
uvicorn app.main:app --host 127.0.0.1 --port 25325

# With workers (not needed for SQLite)
uvicorn app.main:app --host 127.0.0.1 --port 25325 --workers 1
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Test specific endpoint
curl http://127.0.0.1:25325/status
```

## Next: See `04-selenium-integration.md` for browser automation details
