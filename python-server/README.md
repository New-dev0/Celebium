# Celebium Python Backend

FastAPI-based REST API server for browser profile management with SeleniumBase integration.

## Structure

```
python-server/
├── app/
│   ├── api/              # API endpoints
│   │   ├── profiles.py   # Profile management
│   │   └── system.py     # System endpoints
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   └── database.py   # SQLAlchemy setup
│   ├── models/           # Database models
│   │   ├── profile.py    # Profile model
│   │   └── proxy.py      # Proxy model
│   ├── schemas/          # Pydantic schemas
│   │   ├── profile.py    # Profile schemas
│   │   └── response.py   # Response schemas
│   ├── services/         # Business logic
│   │   └── profile_service.py  # Profile CRUD
│   └── main.py           # FastAPI app
├── database/             # SQLite database (created on first run)
├── profiles/             # Browser profile data (created dynamically)
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and adjust settings if needed:

```bash
cp .env.example .env
```

Default settings:
```env
API_PORT=25325
DATABASE_PATH=./database/celebium.db
PROFILES_DIR=./profiles
MAX_CONCURRENT_PROFILES=10
```

### 3. Run Server

```bash
# Development mode (with auto-reload)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --host 127.0.0.1 --port 25325 --reload
```

Server will start on `http://127.0.0.1:25325`

API Documentation available at:
- Swagger UI: `http://127.0.0.1:25325/docs`
- ReDoc: `http://127.0.0.1:25325/redoc`

## API Endpoints

### System
- `GET /` - API information
- `GET /status` - Server status check
- `GET /close` - Shutdown server
- `GET /timezoneslist` - List all timezones
- `GET /folderslist` - List profile folders

### Profiles
- `GET /list` - List all profiles
- `GET /profile/getinfo/{profile_id}` - Get profile details
- `POST /profile/create` - Create new profile
- `POST /profile/update/{profile_id}` - Update profile
- `GET /profile/delete/{profile_id}` - Delete profile
- `GET /profile/start/{profile_id}` - Start browser profile (TODO)
- `GET /profile/stop/{profile_id}` - Stop browser profile (TODO)
- `GET /profile/clearcache/{profile_id}` - Clear cache
- `GET /profile/cleardata/{profile_id}` - Clear all data

## Response Format

All endpoints return Undetectable-compatible responses:

**Success:**
```json
{
  "code": 0,
  "status": "success",
  "data": {...}
}
```

**Error:**
```json
{
  "code": 1,
  "status": "error",
  "data": {"error": "Error message"}
}
```

## Development Status

### ✅ Completed
- FastAPI application setup
- Database models (Profile, Proxy)
- Profile CRUD operations
- API endpoints structure
- Configuration management
- Response schemas

### 🚧 In Progress
- SeleniumBase integration
- Browser launch/stop functionality
- Fingerprint override system

### 📋 Todo
- Proxy management endpoints
- Cookie import/export
- Fingerprint configuration templates
- Testing suite

## Testing

```bash
# Test imports
python test_imports.py

# Run pytest (when tests are implemented)
pytest

# Run with coverage
pytest --cov=app tests/
```

## Database

SQLite database is automatically created on first run at `./database/celebium.db`.

Tables:
- `profiles` - Browser profiles with fingerprints
- `proxies` - Proxy configurations
- `fingerprint_configs` - Reusable fingerprint templates (TODO)
- `folders` - Profile folders (TODO)

## Next Steps

1. Implement SeleniumBase integration (`app/services/selenium_manager.py`)
2. Complete profile start/stop endpoints
3. Add fingerprint override system
4. Implement proxy management
5. Add tests
6. Build Electron frontend
