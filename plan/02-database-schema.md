# Database Schema & Models

## Database Choice: SQLite

**Why SQLite:**
- Zero configuration, single file
- Perfect for local-first apps
- Supports concurrent reads
- Fast for < 100k profiles
- Easy backup (copy .db file)

**File Location:** `database/celebium.db`

---

## Schema Design

### Table: `profiles`

**Purpose:** Store browser profile configurations

```sql
CREATE TABLE profiles (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL,
    folder TEXT DEFAULT 'Default',
    tags TEXT,  -- JSON array: ["tag1", "tag2"]

    -- Browser Config
    os TEXT NOT NULL,  -- "Windows 10", "Mac OS X 14.7", etc.
    browser TEXT NOT NULL,  -- "Chrome 120.0.0.0", "Edge 114.0", etc.
    user_agent TEXT NOT NULL,
    screen_resolution TEXT NOT NULL,  -- "1920x1080"
    language TEXT NOT NULL,  -- "en-US,en;q=0.9"
    timezone TEXT,  -- "America/New_York"
    geolocation TEXT,  -- "40.7128,-74.0060" (lat,long)

    -- Hardware Fingerprint
    cpu_cores INTEGER DEFAULT 8,
    memory_gb INTEGER DEFAULT 8,
    webgl_vendor TEXT,
    webgl_renderer TEXT,

    -- Proxy Config
    proxy_id TEXT,  -- Foreign key to proxies table
    proxy_string TEXT,  -- Direct proxy: "socks5://user:pass@host:port"

    -- Privacy Settings
    webrtc_mode TEXT DEFAULT 'altered',  -- 'altered', 'disabled', 'real'
    canvas_mode TEXT DEFAULT 'noise',  -- 'noise', 'block', 'off'
    audio_mode TEXT DEFAULT 'noise',

    -- Storage
    cookies TEXT,  -- JSON array of cookie objects
    local_storage TEXT,  -- JSON object
    notes TEXT,

    -- Profile Type
    type TEXT DEFAULT 'local',  -- 'local', 'cloud' (future)
    config_id TEXT,  -- Reference to fingerprint template

    -- Status
    status TEXT DEFAULT 'available',  -- 'available', 'running', 'locked'
    debug_port INTEGER,  -- Port when running
    websocket_url TEXT,  -- WS endpoint when running
    pid INTEGER,  -- Chrome process ID when running

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,

    FOREIGN KEY (proxy_id) REFERENCES proxies(id)
);

CREATE INDEX idx_profiles_folder ON profiles(folder);
CREATE INDEX idx_profiles_status ON profiles(status);
CREATE INDEX idx_profiles_name ON profiles(name);
```

---

### Table: `proxies`

**Purpose:** Centralized proxy management (like Undetectable)

```sql
CREATE TABLE proxies (
    id TEXT PRIMARY KEY,  -- UUID
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'http', 'https', 'socks5'
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    username TEXT,
    password TEXT,

    -- Mobile Proxy Support
    change_ip_url TEXT,  -- URL to trigger IP rotation

    -- Status
    last_checked_at TIMESTAMP,
    last_ip TEXT,  -- Last detected IP
    is_working BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX idx_proxies_type ON proxies(type);
```

---

### Table: `fingerprint_configs`

**Purpose:** Reusable fingerprint templates (like Undetectable configs)

```sql
CREATE TABLE fingerprint_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,  -- "Windows 10 - Chrome 120"

    -- Browser
    os TEXT NOT NULL,
    browser TEXT NOT NULL,
    user_agent TEXT NOT NULL,

    -- Screen
    screen_resolution TEXT NOT NULL,
    screen_depth INTEGER DEFAULT 24,

    -- Hardware
    cpu_cores INTEGER,
    memory_gb INTEGER,
    webgl_vendor TEXT,
    webgl_renderer TEXT,

    -- Languages
    language TEXT,
    timezone TEXT,

    -- Metadata
    category TEXT,  -- "Desktop", "Mobile", "Tablet"
    popularity INTEGER DEFAULT 0,  -- Usage count
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_configs_category ON fingerprint_configs(category);
CREATE INDEX idx_configs_os ON fingerprint_configs(os);
```

---

### Table: `folders`

**Purpose:** Organize profiles into folders

```sql
CREATE TABLE folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_id TEXT,  -- For nested folders (future)
    color TEXT,  -- Hex color for UI
    icon TEXT,  -- Icon name

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES folders(id)
);

INSERT INTO folders (id, name, color) VALUES
    ('default', 'Default', '#3B82F6'),
    ('work', 'Work', '#10B981'),
    ('personal', 'Personal', '#F59E0B');
```

---

### Table: `tags`

**Purpose:** Tag profiles for filtering

```sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for many-to-many
CREATE TABLE profile_tags (
    profile_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,

    PRIMARY KEY (profile_id, tag_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

---

### Table: `app_settings`

**Purpose:** Application configuration

```sql
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT DEFAULT 'string',  -- 'string', 'number', 'boolean', 'json'

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default settings
INSERT INTO app_settings (key, value, type) VALUES
    ('api_port', '25325', 'number'),
    ('max_concurrent_profiles', '10', 'number'),
    ('auto_close_on_exit', 'true', 'boolean'),
    ('check_updates', 'true', 'boolean'),
    ('theme', 'light', 'string'),
    ('profiles_directory', './profiles', 'string');
```

---

### Table: `logs`

**Purpose:** Activity and error logging

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,  -- 'info', 'warning', 'error'
    category TEXT NOT NULL,  -- 'profile', 'proxy', 'system', 'selenium'
    message TEXT NOT NULL,
    details TEXT,  -- JSON with extra data
    profile_id TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_created_at ON logs(created_at);
CREATE INDEX idx_logs_profile_id ON logs(profile_id);
```

---

## SQLAlchemy Models (Python)

**File: `python-server/app/models/profile.py`**

```python
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    folder = Column(String, default='Default')
    tags = Column(Text)  # JSON string

    # Browser Config
    os = Column(String, nullable=False)
    browser = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)
    screen_resolution = Column(String, nullable=False)
    language = Column(String, nullable=False)
    timezone = Column(String)
    geolocation = Column(String)

    # Hardware
    cpu_cores = Column(Integer, default=8)
    memory_gb = Column(Integer, default=8)
    webgl_vendor = Column(String)
    webgl_renderer = Column(String)

    # Proxy
    proxy_id = Column(String, ForeignKey('proxies.id'))
    proxy_string = Column(String)

    # Privacy
    webrtc_mode = Column(String, default='altered')
    canvas_mode = Column(String, default='noise')
    audio_mode = Column(String, default='noise')

    # Storage
    cookies = Column(Text)
    local_storage = Column(Text)
    notes = Column(Text)

    # Type
    type = Column(String, default='local')
    config_id = Column(String)

    # Status
    status = Column(String, default='available')
    debug_port = Column(Integer)
    websocket_url = Column(String)
    pid = Column(Integer)

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_used_at = Column(TIMESTAMP)


class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String)
    password = Column(String)
    change_ip_url = Column(String)

    last_checked_at = Column(TIMESTAMP)
    last_ip = Column(String)
    is_working = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    notes = Column(Text)


class FingerprintConfig(Base):
    __tablename__ = "fingerprint_configs"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    os = Column(String, nullable=False)
    browser = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)
    screen_resolution = Column(String, nullable=False)
    screen_depth = Column(Integer, default=24)

    cpu_cores = Column(Integer)
    memory_gb = Column(Integer)
    webgl_vendor = Column(String)
    webgl_renderer = Column(String)

    language = Column(String)
    timezone = Column(String)

    category = Column(String)
    popularity = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
```

---

## Pydantic Schemas (API Validation)

**File: `python-server/app/schemas/profile.py`**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    folder: str = "Default"
    tags: Optional[List[str]] = []

    os: str
    browser: str
    user_agent: str
    screen_resolution: str
    language: str = "en-US,en;q=0.9"
    timezone: Optional[str] = None
    geolocation: Optional[str] = None

    cpu_cores: int = 8
    memory_gb: int = 8
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None

    proxy_id: Optional[str] = None
    proxy_string: Optional[str] = None

    webrtc_mode: str = "altered"
    canvas_mode: str = "noise"
    audio_mode: str = "noise"

    notes: Optional[str] = None
    type: str = "local"
    config_id: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    proxy_id: Optional[str] = None
    proxy_string: Optional[str] = None
    notes: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: str
    status: str
    debug_port: Optional[int] = None
    websocket_url: Optional[str] = None
    pid: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

---

## Database Initialization Script

**File: `python-server/app/core/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_PATH = os.getenv("DB_PATH", "./database/celebium.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Sample Data Seeds

**File: `python-server/seeds/initial_data.py`**

```python
import uuid
from app.models import FingerprintConfig, Folder

def seed_fingerprint_configs(db):
    """Add common browser fingerprints"""
    configs = [
        {
            "name": "Windows 10 - Chrome 120",
            "os": "Windows 10",
            "browser": "Chrome 120.0.0.0",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "screen_resolution": "1920x1080",
            "cpu_cores": 8,
            "memory_gb": 8,
            "webgl_vendor": "Google Inc. (NVIDIA)",
            "webgl_renderer": "ANGLE (NVIDIA GeForce GTX 1060 6GB)",
            "language": "en-US,en;q=0.9",
            "timezone": "America/New_York",
            "category": "Desktop"
        },
        {
            "name": "Mac OS X - Safari 17",
            "os": "Mac OS X 14.7.2",
            "browser": "Safari 17.6",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
            "screen_resolution": "1920x1080",
            "cpu_cores": 8,
            "memory_gb": 16,
            "webgl_vendor": "Apple",
            "webgl_renderer": "Apple M1",
            "language": "en-US,en;q=0.9",
            "timezone": "America/Los_Angeles",
            "category": "Desktop"
        }
    ]

    for config_data in configs:
        config = FingerprintConfig(id=str(uuid.uuid4()), **config_data)
        db.add(config)

    db.commit()
```

---

## Migration Strategy

For future schema changes, use **Alembic** (SQLAlchemy migration tool):

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head
```

---

## Performance Considerations

1. **Indexes**: Created on frequently queried columns (folder, status, name)
2. **Connection Pooling**: SQLite doesn't need it, but SQLAlchemy handles it
3. **Concurrent Writes**: SQLite handles well for < 100 concurrent profiles
4. **Backup**: Simple file copy, can be automated

## Next: See `03-fastapi-backend.md` for API implementation
