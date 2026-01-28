# API Documentation

## Base URL
```
http://127.0.0.1:25325
```

## Response Format

All responses follow Undetectable-compatible format:

```json
{
  "code": 0,         // 0 = success, 1 = error
  "status": "success", // "success" or "error"
  "data": {}         // Response data or error object
}
```

---

## Endpoints

### System

#### GET `/status`
Check if server is running

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {}
}
```

#### GET `/close`
Shutdown server

---

### Profiles

#### GET `/list`
Get all profiles

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "profile-id-1": {
      "name": "Profile 1",
      "status": "available",
      "debug_port": "",
      "websocket_link": "",
      "folder": "Work",
      "tags": ["tag1", "tag2"],
      "creation_date": 1706745600,
      "modify_date": 1706745600
    }
  }
}
```

#### GET `/profile/getinfo/:profileID`
Get detailed profile info

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "id": "profile-id",
    "name": "Profile 1",
    "folder": "Work",
    "os": "Windows 10",
    "browser": "Chrome 120.0.0.0",
    "user_agent": "Mozilla/5.0...",
    "screen_resolution": "1920x1080",
    "language": "en-US,en;q=0.9",
    "timezone": "America/New_York",
    "cpu_cores": 8,
    "memory_gb": 8,
    "proxy_string": "socks5://...",
    "status": "available",
    "created_at": "2024-02-01T12:00:00",
    "updated_at": "2024-02-01T12:00:00"
  }
}
```

#### POST `/profile/create`
Create new profile

**Request Body:**
```json
{
  "name": "New Profile",
  "folder": "Work",
  "tags": ["automation", "testing"],
  "os": "Windows 10",
  "browser": "Chrome 120.0.0.0",
  "user_agent": "Mozilla/5.0...",
  "screen_resolution": "1920x1080",
  "language": "en-US,en;q=0.9",
  "timezone": "America/New_York",
  "cpu_cores": 8,
  "memory_gb": 8,
  "proxy_string": "socks5://user:pass@host:port",
  "webrtc_mode": "altered",
  "canvas_mode": "noise",
  "notes": "Test profile"
}
```

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "profile_id": "abc123",
    "name": "New Profile"
  }
}
```

#### POST `/profile/update/:profileID`
Update profile

**Request Body:** (all fields optional)
```json
{
  "name": "Updated Name",
  "folder": "Personal",
  "proxy_string": "socks5://...",
  "notes": "Updated notes"
}
```

#### GET `/profile/delete/:profileID`
Delete profile

#### GET `/profile/start/:profileID?chrome_flags=&start_pages=`
Start browser profile

**Query Parameters:**
- `chrome_flags` (optional): URL-encoded Chrome flags
- `start_pages` (optional): Comma-separated URLs

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "name": "Profile 1",
    "debug_port": 9222,
    "websocket_link": "ws://127.0.0.1:9222/devtools/browser/abc123",
    "folder": "Work",
    "tags": ["tag1"]
  }
}
```

#### GET `/profile/stop/:profileID`
Stop browser profile

#### GET `/profile/checkconnection/:profileID`
Check proxy connection and get IP

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "ip": "123.45.67.89"
  }
}
```

#### GET `/profile/cookies/:profileID`
Get profile cookies

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "cookies": [
      {
        "name": "session_id",
        "value": "abc123",
        "domain": "example.com",
        "path": "/",
        "secure": true,
        "httpOnly": true
      }
    ]
  }
}
```

#### GET `/profile/clearcache/:profileID`
Clear profile cache

#### GET `/profile/cleardata/:profileID`
Clear all profile data (cookies, cache, history)

---

### Proxies

#### GET `/proxies/list`
Get all proxies

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "proxy-id-1": {
      "name": "US Proxy",
      "type": "socks5",
      "host": "proxy.example.com",
      "port": 1080,
      "username": "user",
      "password": "pass"
    }
  }
}
```

#### POST `/proxies/add`
Add new proxy

**Request Body:**
```json
{
  "name": "US Proxy",
  "type": "socks5",
  "host": "proxy.example.com",
  "port": 1080,
  "username": "user",
  "password": "pass",
  "change_ip_url": "https://api.example.com/rotate"
}
```

#### GET `/proxies/delete/:proxyID`
Delete proxy

#### POST `/proxies/update/:proxyID`
Update proxy

---

### Configs

#### GET `/configslist`
Get fingerprint configurations

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "config-id-1": {
      "browser": "Chrome 120.0.0.0",
      "os": "Windows 10",
      "screen": "1920x1080",
      "useragent": "Mozilla/5.0...",
      "webgl": "ANGLE (NVIDIA...)"
    }
  }
}
```

---

### Other

#### GET `/timezoneslist`
Get all timezones

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": {
    "America/New_York": "GMT-5:00",
    "Europe/London": "GMT+0:00",
    ...
  }
}
```

#### GET `/folderslist`
Get all folders

**Response:**
```json
{
  "code": 0,
  "status": "success",
  "data": ["Default", "Work", "Personal"]
}
```

---

## Error Responses

```json
{
  "code": 1,
  "status": "error",
  "data": {
    "error": "Profile not found"
  }
}
```

**Common Error Codes:**
- Profile not found
- Profile already running
- Invalid proxy format
- Maximum concurrent profiles reached
- Failed to start browser
- Database error

---

## Usage Examples

### Python (requests)

```python
import requests

API_URL = "http://127.0.0.1:25325"

# List profiles
response = requests.get(f"{API_URL}/list")
profiles = response.json()["data"]

# Start profile
profile_id = list(profiles.keys())[0]
result = requests.get(f"{API_URL}/profile/start/{profile_id}")
websocket_url = result.json()["data"]["websocket_link"]

# Connect with SeleniumBase
from seleniumbase import SB
sb = SB()
sb.connect_to_existing(websocket_url)
```

### JavaScript (Puppeteer)

```javascript
const axios = require('axios');
const puppeteer = require('puppeteer');

const API_URL = 'http://127.0.0.1:25325';

async function main() {
  // Start profile
  const response = await axios.get(`${API_URL}/profile/start/profile-id`);
  const { websocket_link } = response.data.data;

  // Connect Puppeteer
  const browser = await puppeteer.connect({
    browserWSEndpoint: websocket_link,
  });

  const page = await browser.newPage();
  await page.goto('https://example.com');
}
```

### cURL

```bash
# List profiles
curl http://127.0.0.1:25325/list

# Create profile
curl -X POST http://127.0.0.1:25325/profile/create \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","os":"Windows 10","browser":"Chrome 120","user_agent":"...","screen_resolution":"1920x1080","language":"en-US"}'

# Start profile
curl http://127.0.0.1:25325/profile/start/abc123

# Stop profile
curl http://127.0.0.1:25325/profile/stop/abc123
```

---

## Rate Limiting

No rate limiting on localhost. If exposing on LAN:
- 100 requests per minute per IP
- 10 concurrent profile operations

---

## WebSocket Connection

After starting a profile, connect automation tools:

**Format:**
```
ws://127.0.0.1:{debug_port}/devtools/browser/{browser_id}
```

**Example:**
```
ws://127.0.0.1:9222/devtools/browser/d294f1fb-bce4-46c4-b556-1f26a4c40dbt
```

This URL works with:
- Puppeteer: `puppeteer.connect({ browserWSEndpoint })`
- Playwright: `playwright.chromium.connectOverCDP(wsEndpoint)`
- Selenium: Use debug port with remote debugging
- SeleniumBase: `sb.connect_to_existing(port=9222)`

## Next: See `08-build-packaging.md` for distribution setup
