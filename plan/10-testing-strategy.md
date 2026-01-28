# Testing & Quality Assurance Strategy

## Testing Pyramid

```
       /\
      /  \      E2E Tests (10%)
     /____\     - Full user workflows
    /      \    Integration Tests (30%)
   /________\   - API + Database + Browser
  /          \  Unit Tests (60%)
 /____________\ - Individual functions
```

---

## 1. Unit Tests (Python Backend)

### Framework: pytest

**File Structure:**
```
python-server/tests/
├── conftest.py               # Fixtures
├── test_profile_service.py   # Profile CRUD logic
├── test_fingerprint.py       # Fingerprint generation
├── test_proxy_service.py     # Proxy management
└── test_database.py          # Database operations
```

### Example: Profile Service Tests

**File: `tests/test_profile_service.py`**

```python
import pytest
from app.services.profile_service import ProfileService
from app.schemas.profile import ProfileCreate

@pytest.fixture
def db_session():
    """Create in-memory test database"""
    from app.core.database import Base, engine
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_create_profile(db_session):
    """Test profile creation"""
    service = ProfileService(db_session)

    profile_data = ProfileCreate(
        name="Test Profile",
        os="Windows 10",
        browser="Chrome 120.0.0.0",
        user_agent="Mozilla/5.0...",
        screen_resolution="1920x1080",
        language="en-US"
    )

    profile = service.create(profile_data)

    assert profile.id is not None
    assert profile.name == "Test Profile"
    assert profile.status == "available"

def test_get_profile_by_id(db_session):
    """Test profile retrieval"""
    service = ProfileService(db_session)

    # Create profile
    profile = service.create(ProfileCreate(...))

    # Retrieve
    retrieved = service.get_by_id(profile.id)

    assert retrieved.id == profile.id
    assert retrieved.name == profile.name

def test_update_profile(db_session):
    """Test profile update"""
    service = ProfileService(db_session)

    profile = service.create(ProfileCreate(...))

    # Update
    updated = service.update(profile.id, ProfileUpdate(name="New Name"))

    assert updated.name == "New Name"
    assert updated.id == profile.id

def test_delete_profile(db_session):
    """Test profile deletion"""
    service = ProfileService(db_session)

    profile = service.create(ProfileCreate(...))
    profile_id = profile.id

    # Delete
    success = service.delete(profile_id)
    assert success is True

    # Verify deletion
    deleted = service.get_by_id(profile_id)
    assert deleted is None
```

### Example: Fingerprint Tests

**File: `tests/test_fingerprint.py`**

```python
from app.services.fingerprint_service import FingerprintService

def test_generate_windows_fingerprint():
    """Test Windows fingerprint generation"""
    fingerprint = FingerprintService.generate_windows_fingerprint()

    assert fingerprint["os"] == "Windows 10"
    assert "Chrome" in fingerprint["browser"]
    assert fingerprint["cpu_cores"] in [4, 6, 8, 12, 16]
    assert fingerprint["memory_gb"] in [8, 16, 32]
    assert "x" in fingerprint["screen_resolution"]

def test_generate_mac_fingerprint():
    """Test macOS fingerprint generation"""
    fingerprint = FingerprintService.generate_mac_fingerprint()

    assert "Mac OS X" in fingerprint["os"]
    assert "Apple" in fingerprint["webgl_vendor"]
```

### Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_profile_service.py

# Run specific test
pytest tests/test_profile_service.py::test_create_profile
```

**Coverage Target:** > 80%

---

## 2. Integration Tests (API + SeleniumBase)

### API Integration Tests

**File: `tests/test_api_integration.py`**

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_server_status():
    """Test /status endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["code"] == 0

def test_list_profiles():
    """Test profile listing"""
    response = client.get("/list")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_create_and_delete_profile():
    """Test full profile lifecycle"""
    # Create
    profile_data = {
        "name": "Test Profile",
        "os": "Windows 10",
        "browser": "Chrome 120.0.0.0",
        "user_agent": "Mozilla/5.0...",
        "screen_resolution": "1920x1080",
        "language": "en-US"
    }

    response = client.post("/profile/create", json=profile_data)
    assert response.status_code == 200
    profile_id = response.json()["data"]["profile_id"]

    # Verify exists
    response = client.get(f"/profile/getinfo/{profile_id}")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Test Profile"

    # Delete
    response = client.get(f"/profile/delete/{profile_id}")
    assert response.status_code == 200
```

### SeleniumBase Integration Tests

**File: `tests/test_selenium_integration.py`**

```python
import pytest
from app.services.selenium_manager import SeleniumManager
from app.models.profile import Profile

@pytest.fixture
def test_profile():
    """Create test profile"""
    return Profile(
        id="test-profile-123",
        name="Test Profile",
        os="Windows 10",
        browser="Chrome 120.0.0.0",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        screen_resolution="1920x1080",
        language="en-US",
        cpu_cores=8,
        memory_gb=8
    )

def test_start_profile(test_profile):
    """Test browser launch"""
    manager = SeleniumManager()

    result = manager.start_profile(test_profile)

    assert "debug_port" in result
    assert "websocket_link" in result
    assert "pid" in result
    assert result["debug_port"] > 0

    # Cleanup
    manager.stop_profile(test_profile.id)

def test_fingerprint_override(test_profile):
    """Test fingerprint injection"""
    manager = SeleniumManager()

    result = manager.start_profile(test_profile)

    # Connect and verify fingerprints
    from seleniumbase import SB
    sb = SB()
    sb.connect_to_existing(port=result["debug_port"])

    # Check User Agent
    user_agent = sb.execute_script("return navigator.userAgent")
    assert user_agent == test_profile.user_agent

    # Check CPU cores
    cpu_cores = sb.execute_script("return navigator.hardwareConcurrency")
    assert cpu_cores == test_profile.cpu_cores

    # Cleanup
    sb.quit()
    manager.stop_profile(test_profile.id)

def test_multiple_profiles():
    """Test running multiple profiles simultaneously"""
    manager = SeleniumManager()

    profiles = [
        Profile(id=f"profile-{i}", name=f"Profile {i}", ...)
        for i in range(3)
    ]

    # Start all profiles
    for profile in profiles:
        result = manager.start_profile(profile)
        assert result["debug_port"] > 0

    # Verify all running
    stats = manager.get_stats()
    assert stats["running_count"] == 3

    # Stop all
    for profile in profiles:
        manager.stop_profile(profile.id)
```

---

## 3. Bot Detection Tests

### Test Sites

**File: `tests/test_bot_detection.py`**

```python
import pytest
from seleniumbase import SB

@pytest.mark.slow
def test_cloudflare_turnstile():
    """Test Cloudflare Turnstile bypass"""
    with SB(uc=True) as sb:
        sb.open("https://seleniumbase.io/apps/turnstile")
        sb.sleep(2)

        # Should automatically bypass
        sb.assert_element("img#captcha-success", timeout=10)

@pytest.mark.slow
def test_nowsecure_detection():
    """Test bot detection site"""
    with SB(uc=True) as sb:
        sb.open("https://nowsecure.nl/")
        sb.sleep(3)

        # Check for bot detection
        page_source = sb.get_page_source()
        assert "BOT" not in page_source.upper()

@pytest.mark.slow
def test_bot_sannysoft():
    """Test comprehensive bot detection"""
    with SB(uc=True) as sb:
        sb.open("https://bot.sannysoft.com/")
        sb.sleep(3)

        # Should show green checks, not red
        red_count = sb.execute_script("""
            return document.querySelectorAll('.failed').length;
        """)

        assert red_count < 5, f"Too many red flags: {red_count}"
```

### Detection Metrics

```python
# Calculate bypass success rate
def calculate_bypass_rate(test_results):
    """
    Test on 10 different protected sites
    Count successes vs failures
    """
    sites = [
        "https://gitlab.com/users/sign_in",
        "https://www.walmart.com/",
        "https://www.nike.com/",
        # ... more sites
    ]

    successes = 0
    for site in sites:
        if test_site(site):
            successes += 1

    return (successes / len(sites)) * 100

# Target: > 95% success rate
```

---

## 4. E2E Tests (Electron App)

### Framework: Playwright

**File: `electron-app/tests/e2e/app.spec.ts`**

```typescript
import { test, expect } from '@playwright/test';
import { _electron as electron } from 'playwright';

test.describe('Celebium E2E', () => {
  let electronApp;
  let window;

  test.beforeAll(async () => {
    electronApp = await electron.launch({ args: ['.'] });
    window = await electronApp.firstWindow();
  });

  test.afterAll(async () => {
    await electronApp.close();
  });

  test('app launches successfully', async () => {
    await window.waitForLoadState('domcontentloaded');

    const title = await window.title();
    expect(title).toBe('Celebium');
  });

  test('create new profile', async () => {
    // Click "New Profile" button
    await window.click('button:has-text("New Profile")');

    // Fill form
    await window.fill('input[name="name"]', 'E2E Test Profile');
    await window.selectOption('select[name="os"]', 'Windows 10');

    // Submit
    await window.click('button:has-text("Create")');

    // Verify profile appears in list
    await window.waitForSelector('text=E2E Test Profile');
  });

  test('start and stop profile', async () => {
    // Start profile
    await window.click('button:has-text("Start")');

    // Wait for status change
    await window.waitForSelector('text=Running', { timeout: 10000 });

    // Stop profile
    await window.click('button:has-text("Stop")');

    // Verify stopped
    await window.waitForSelector('text=Stopped');
  });
});
```

---

## 5. Manual Testing Checklist

### Pre-Release Checklist

**Installation:**
- [ ] Installer runs on clean Windows 10
- [ ] Installer runs on clean Windows 11
- [ ] App launches after install
- [ ] Desktop shortcut works
- [ ] Start menu shortcut works

**Profile Management:**
- [ ] Create profile with all fields
- [ ] Create profile with minimal fields
- [ ] Edit existing profile
- [ ] Delete profile
- [ ] Duplicate profile
- [ ] Search profiles
- [ ] Filter by folder/tags

**Browser Launch:**
- [ ] Start single profile
- [ ] Start multiple profiles (3+)
- [ ] Stop running profile
- [ ] Profile persists after restart
- [ ] Debug port is accessible
- [ ] WebSocket URL works

**Fingerprints:**
- [ ] User agent applied correctly
- [ ] Screen resolution correct
- [ ] CPU cores override works
- [ ] Memory override works
- [ ] WebGL vendor/renderer correct
- [ ] Canvas fingerprint randomized

**Proxy:**
- [ ] HTTP proxy works
- [ ] HTTPS proxy works
- [ ] SOCKS5 proxy works
- [ ] Proxy with auth works
- [ ] IP detection shows proxy IP
- [ ] Profile without proxy uses real IP

**Bot Detection:**
- [ ] Bypasses Cloudflare Turnstile
- [ ] Bypasses nowsecure.nl
- [ ] Bypasses bot.sannysoft.com
- [ ] No console errors on protected sites

**Performance:**
- [ ] Profile launches in < 5s
- [ ] UI responsive with 10 profiles
- [ ] Memory usage < 500MB per profile
- [ ] No memory leaks (24h test)

**Edge Cases:**
- [ ] Kill browser externally (profile status updates)
- [ ] Start same profile twice (error handling)
- [ ] Delete running profile (stopped first)
- [ ] Invalid proxy (clear error message)
- [ ] Network offline (graceful degradation)

---

## 6. Performance Testing

### Load Testing

```python
# Simulate 10 concurrent profile launches
import concurrent.futures
import time

def launch_profile(profile_id):
    start = time.time()
    # Launch profile via API
    response = requests.get(f"http://127.0.0.1:25325/profile/start/{profile_id}")
    duration = time.time() - start
    return duration

# Test
profile_ids = [f"profile-{i}" for i in range(10)]

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    durations = list(executor.map(launch_profile, profile_ids))

avg_duration = sum(durations) / len(durations)
print(f"Average launch time: {avg_duration:.2f}s")

# Target: < 5s per profile
```

### Memory Profiling

```python
import psutil
import time

def profile_memory_usage():
    """Monitor memory over 1 hour"""
    process = psutil.Process()

    samples = []
    for _ in range(60):  # 60 minutes
        memory_mb = process.memory_info().rss / (1024 * 1024)
        samples.append(memory_mb)
        time.sleep(60)

    print(f"Average memory: {sum(samples) / len(samples):.2f} MB")
    print(f"Max memory: {max(samples):.2f} MB")

# Target: < 500MB per profile
```

---

## 7. Security Testing

### Checklist

- [ ] No credentials stored in plaintext (proxy passwords)
- [ ] API only accessible on localhost (not 0.0.0.0)
- [ ] No SQL injection vulnerabilities
- [ ] Profile data encrypted at rest (optional)
- [ ] Code signed (Windows SmartScreen bypass)
- [ ] No known CVEs in dependencies

### Dependency Scanning

```bash
# Python
pip install safety
safety check

# Node.js
npm audit
```

---

## 8. Regression Testing

### After Each Change

```bash
# Run full test suite
pytest
npm test

# Manual smoke test
1. Launch app
2. Create profile
3. Start profile
4. Open protected site
5. Stop profile
```

### Pre-Release

```bash
# Full regression suite
pytest --cov=app
npm run test:e2e
# + Full manual checklist
```

---

## 9. Bug Tracking

### Issue Template

```markdown
**Description:**
Clear description of the bug

**Steps to Reproduce:**
1. Go to...
2. Click on...
3. See error

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: Windows 10/11
- Version: v1.0.0
- Python version: 3.10
- SeleniumBase version: 4.26.0

**Logs:**
Attach error logs or screenshots
```

---

## 10. Continuous Testing

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd python-server
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd python-server
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  test-electron:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd electron-app
          npm install

      - name: Run tests
        run: |
          cd electron-app
          npm test
```

---

## Success Criteria

**Before v1.0.0 Release:**
- [ ] All unit tests passing (> 80% coverage)
- [ ] All integration tests passing
- [ ] Bot detection bypass rate > 95%
- [ ] Manual checklist 100% complete
- [ ] Zero critical bugs
- [ ] Performance targets met

**Quality Gates:**
- Code coverage: > 80%
- Bot bypass rate: > 95%
- Profile launch time: < 5s
- Memory per profile: < 500MB
- Zero security vulnerabilities

## Conclusion

Comprehensive testing ensures Celebium is production-ready, reliable, and delivers on its promise of undetectable browser automation. The combination of automated tests, manual validation, and real-world bot detection testing provides confidence in the product's quality.
