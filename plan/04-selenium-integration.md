# SeleniumBase Integration & Browser Management

## Core Manager: SeleniumManager

**File: `app/services/selenium_manager.py`**

```python
from seleniumbase import Driver, SB
from typing import Dict, List, Optional
import os
import psutil
from datetime import datetime

class SeleniumManager:
    """
    Manages SeleniumBase browser instances for profiles
    """

    def __init__(self):
        self.running_profiles: Dict[str, Dict] = {}
        # Structure: {
        #   "profile_id": {
        #       "sb": <SB instance>,
        #       "driver": <driver>,
        #       "pid": <process_id>,
        #       "debug_port": <port>,
        #       "websocket_url": <ws_url>,
        #       "started_at": <timestamp>
        #   }
        # }

    def start_profile(
        self,
        profile,
        chrome_flags: List[str] = [],
        start_pages: List[str] = []
    ) -> Dict:
        """
        Launch browser with profile configuration using SeleniumBase UC Mode
        """
        profile_id = profile.id

        # Check if already running
        if profile_id in self.running_profiles:
            raise Exception(f"Profile {profile.name} is already running")

        # Prepare Chrome user data directory
        user_data_dir = os.path.abspath(f"./profiles/profile_{profile_id}")
        os.makedirs(user_data_dir, exist_ok=True)

        # Build Chrome arguments
        chrome_options = self._build_chrome_options(
            profile=profile,
            user_data_dir=user_data_dir,
            extra_flags=chrome_flags
        )

        try:
            # Launch SeleniumBase in UC Mode
            sb = SB(
                uc=True,  # Undetected Chrome mode
                headless=False,
                user_data_dir=user_data_dir,
                chromium_arg=",".join(chrome_options),
                # Apply fingerprint overrides
                locale=profile.language.split(',')[0] if profile.language else "en-US",
            )

            # Start the browser
            sb.open("about:blank")

            # Get debug info
            debug_port = self._get_debug_port(sb.driver)
            websocket_url = self._get_websocket_url(sb.driver, debug_port)
            pid = sb.driver.service.process.pid

            # Apply advanced fingerprint overrides via CDP
            self._apply_fingerprint_overrides(sb, profile)

            # Open start pages if specified
            if start_pages:
                for page_url in start_pages:
                    sb.open_new_tab()
                    sb.open(page_url)

            # Store running instance
            self.running_profiles[profile_id] = {
                "sb": sb,
                "driver": sb.driver,
                "pid": pid,
                "debug_port": debug_port,
                "websocket_url": websocket_url,
                "started_at": datetime.now()
            }

            return {
                "debug_port": debug_port,
                "websocket_link": websocket_url,
                "pid": pid
            }

        except Exception as e:
            print(f"❌ Failed to start profile {profile.name}: {e}")
            raise

    def stop_profile(self, profile_id: str):
        """Stop and cleanup profile browser"""
        if profile_id not in self.running_profiles:
            raise Exception(f"Profile {profile_id} is not running")

        profile_data = self.running_profiles[profile_id]

        try:
            # Close browser gracefully
            sb = profile_data["sb"]
            sb.driver.quit()

        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")

            # Force kill if needed
            try:
                pid = profile_data["pid"]
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
            except:
                pass

        finally:
            # Remove from running profiles
            del self.running_profiles[profile_id]

    def close_all(self):
        """Close all running profiles (on app shutdown)"""
        profile_ids = list(self.running_profiles.keys())

        for profile_id in profile_ids:
            try:
                self.stop_profile(profile_id)
            except:
                pass

    def _build_chrome_options(
        self,
        profile,
        user_data_dir: str,
        extra_flags: List[str]
    ) -> List[str]:
        """Build Chrome launch arguments"""
        options = []

        # User data directory (for profile isolation)
        options.append(f"--user-data-dir={user_data_dir}")

        # Window size
        if profile.screen_resolution:
            width, height = profile.screen_resolution.split('x')
            options.append(f"--window-size={width},{height}")

        # Language
        if profile.language:
            lang = profile.language.split(',')[0]
            options.append(f"--lang={lang}")

        # Proxy
        if profile.proxy_string:
            options.append(f"--proxy-server={profile.proxy_string}")

        # User Agent (applied via CDP, not here)

        # WebRTC mode
        if profile.webrtc_mode == 'disabled':
            options.append("--disable-webrtc")

        # Geolocation (applied via CDP)

        # Additional flags
        options.extend(extra_flags)

        return options

    def _get_debug_port(self, driver) -> int:
        """Extract Chrome DevTools debug port"""
        # SeleniumBase UC Mode exposes debug port
        try:
            if hasattr(driver, 'service') and hasattr(driver.service, 'port'):
                return driver.service.port

            # Fallback: parse from capabilities
            capabilities = driver.capabilities
            if 'goog:chromeOptions' in capabilities:
                debug_addr = capabilities['goog:chromeOptions'].get('debuggerAddress', '')
                if ':' in debug_addr:
                    return int(debug_addr.split(':')[1])

        except:
            pass

        # Default fallback
        return 9222

    def _get_websocket_url(self, driver, debug_port: int) -> str:
        """Get WebSocket debugger URL"""
        import requests

        try:
            response = requests.get(
                f"http://127.0.0.1:{debug_port}/json/version",
                timeout=5
            )
            data = response.json()
            return data.get('webSocketDebuggerUrl', '')

        except:
            return f"ws://127.0.0.1:{debug_port}/devtools/browser"

    def _apply_fingerprint_overrides(self, sb, profile):
        """
        Apply fingerprint overrides via Chrome DevTools Protocol (CDP)
        """
        try:
            # Activate CDP mode
            sb.activate_cdp_mode("about:blank")

            # Override User Agent
            if profile.user_agent:
                sb.cdp.execute_script(f"""
                    Object.defineProperty(navigator, 'userAgent', {{
                        get: () => '{profile.user_agent}'
                    }});
                """)

            # Override Platform
            if profile.os:
                platform = self._get_platform_from_os(profile.os)
                sb.cdp.execute_script(f"""
                    Object.defineProperty(navigator, 'platform', {{
                        get: () => '{platform}'
                    }});
                """)

            # Override Hardware Concurrency (CPU cores)
            if profile.cpu_cores:
                sb.cdp.execute_script(f"""
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: () => {profile.cpu_cores}
                    }});
                """)

            # Override Memory (deviceMemory)
            if profile.memory_gb:
                sb.cdp.execute_script(f"""
                    Object.defineProperty(navigator, 'deviceMemory', {{
                        get: () => {profile.memory_gb}
                    }});
                """)

            # Override WebGL Vendor/Renderer
            if profile.webgl_vendor and profile.webgl_renderer:
                sb.cdp.execute_script(f"""
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        if (parameter === 37445) {{
                            return '{profile.webgl_vendor}';
                        }}
                        if (parameter === 37446) {{
                            return '{profile.webgl_renderer}';
                        }}
                        return getParameter.apply(this, arguments);
                    }};
                """)

            # Override Geolocation
            if profile.geolocation:
                lat, lon = profile.geolocation.split(',')
                sb.cdp.execute_script(f"""
                    navigator.geolocation.getCurrentPosition = function(success) {{
                        const position = {{
                            coords: {{
                                latitude: {lat},
                                longitude: {lon},
                                accuracy: 10
                            }}
                        }};
                        success(position);
                    }};
                """)

            # Canvas Fingerprint Noise
            if profile.canvas_mode == 'noise':
                sb.cdp.execute_script("""
                    const toBlob = HTMLCanvasElement.prototype.toBlob;
                    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                    const getImageData = CanvasRenderingContext2D.prototype.getImageData;

                    HTMLCanvasElement.prototype.toBlob = function() {
                        // Add random noise to canvas
                        const context = this.getContext('2d');
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                        }
                        context.putImageData(imageData, 0, 0);
                        return toBlob.apply(this, arguments);
                    };
                """)

            # Audio Fingerprint Noise
            if profile.audio_mode == 'noise':
                sb.cdp.execute_script("""
                    const audioContext = AudioContext.prototype.createAnalyser;
                    AudioContext.prototype.createAnalyser = function() {
                        const analyser = audioContext.apply(this, arguments);
                        const getFloatFrequencyData = analyser.getFloatFrequencyData;
                        analyser.getFloatFrequencyData = function(array) {
                            getFloatFrequencyData.apply(this, arguments);
                            for (let i = 0; i < array.length; i++) {
                                array[i] += Math.random() * 0.01;
                            }
                        };
                        return analyser;
                    };
                """)

            # Timezone override
            if profile.timezone:
                sb.cdp.set_locale(profile.timezone)

            # Reconnect WebDriver (CDP mode disconnects it)
            sb.reconnect()

        except Exception as e:
            print(f"⚠️ Error applying fingerprint overrides: {e}")
            # Continue anyway, basic profile will still work

    def _get_platform_from_os(self, os_name: str) -> str:
        """Map OS name to navigator.platform value"""
        os_lower = os_name.lower()

        if 'windows' in os_lower:
            return 'Win32'
        elif 'mac' in os_lower:
            return 'MacIntel'
        elif 'linux' in os_lower:
            return 'Linux x86_64'
        elif 'android' in os_lower:
            return 'Linux armv8l'
        elif 'iphone' in os_lower or 'ipad' in os_lower:
            return 'iPhone'
        else:
            return 'Win32'  # Default

    def get_running_profile(self, profile_id: str) -> Optional[Dict]:
        """Get running profile data"""
        return self.running_profiles.get(profile_id)

    def is_running(self, profile_id: str) -> bool:
        """Check if profile is running"""
        return profile_id in self.running_profiles

    def get_stats(self) -> Dict:
        """Get statistics about running profiles"""
        total_memory = 0

        for profile_id, data in self.running_profiles.items():
            try:
                pid = data["pid"]
                process = psutil.Process(pid)
                total_memory += process.memory_info().rss / (1024 * 1024)  # MB
            except:
                pass

        return {
            "running_count": len(self.running_profiles),
            "total_memory_mb": round(total_memory, 2),
            "profiles": list(self.running_profiles.keys())
        }
```

---

## Profile Service (Business Logic)

**File: `app/services/profile_service.py`**

```python
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate

class ProfileService:
    """Profile CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Profile]:
        """Get all profiles"""
        return self.db.query(Profile).all()

    def get_by_id(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID"""
        return self.db.query(Profile).filter(Profile.id == profile_id).first()

    def get_by_folder(self, folder: str) -> List[Profile]:
        """Get profiles in a folder"""
        return self.db.query(Profile).filter(Profile.folder == folder).all()

    def create(self, profile_data: ProfileCreate) -> Profile:
        """Create new profile"""
        profile = Profile(
            id=str(uuid.uuid4()),
            **profile_data.dict()
        )

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    def update(self, profile_id: str, profile_data: ProfileUpdate) -> Optional[Profile]:
        """Update profile"""
        profile = self.get_by_id(profile_id)

        if not profile:
            return None

        # Update only provided fields
        update_data = profile_data.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(profile, key, value)

        profile.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def update_status(
        self,
        profile_id: str,
        status: str,
        debug_port: Optional[int] = None,
        websocket_url: Optional[str] = None,
        pid: Optional[int] = None
    ):
        """Update profile runtime status"""
        profile = self.get_by_id(profile_id)

        if profile:
            profile.status = status
            profile.debug_port = debug_port
            profile.websocket_url = websocket_url
            profile.pid = pid

            if status == "running":
                profile.last_used_at = datetime.now()

            self.db.commit()

    def delete(self, profile_id: str) -> bool:
        """Delete profile"""
        profile = self.get_by_id(profile_id)

        if not profile:
            return False

        self.db.delete(profile)
        self.db.commit()

        # Also delete profile directory
        import shutil
        import os
        profile_dir = f"./profiles/profile_{profile_id}"
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir)

        return True

    def search(self, query: str) -> List[Profile]:
        """Search profiles by name, folder, or tags"""
        return self.db.query(Profile).filter(
            Profile.name.contains(query) |
            Profile.folder.contains(query) |
            Profile.tags.contains(query)
        ).all()
```

---

## Fingerprint Generator Service

**File: `app/services/fingerprint_service.py`**

```python
import random
from typing import Dict, List

class FingerprintService:
    """Generate realistic browser fingerprints"""

    # Common User Agents
    USER_AGENTS = {
        "Chrome 120 Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Chrome 119 Mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Edge 120 Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    }

    # Common Resolutions
    RESOLUTIONS = [
        "1920x1080", "1366x768", "1536x864",
        "1440x900", "1600x900", "2560x1440"
    ]

    # WebGL Vendors
    WEBGL_VENDORS = {
        "NVIDIA": [
            "ANGLE (NVIDIA GeForce GTX 1060 6GB)",
            "ANGLE (NVIDIA GeForce RTX 3060)",
            "ANGLE (NVIDIA GeForce RTX 4070)"
        ],
        "AMD": [
            "ANGLE (AMD Radeon RX 6750 XT)",
            "ANGLE (AMD Radeon RX 7900 XT)"
        ],
        "Intel": [
            "ANGLE (Intel UHD Graphics 630)",
            "ANGLE (Intel Iris Xe Graphics)"
        ],
        "Apple": [
            "ANGLE (Apple M1)",
            "ANGLE (Apple M2)"
        ]
    }

    @staticmethod
    def generate_windows_fingerprint() -> Dict:
        """Generate Windows 10/11 fingerprint"""
        vendor = random.choice(["NVIDIA", "AMD", "Intel"])

        return {
            "os": "Windows 10",
            "browser": "Chrome 120.0.0.0",
            "user_agent": FingerprintService.USER_AGENTS["Chrome 120 Windows"],
            "screen_resolution": random.choice(FingerprintService.RESOLUTIONS),
            "language": "en-US,en;q=0.9",
            "timezone": "America/New_York",
            "cpu_cores": random.choice([4, 6, 8, 12]),
            "memory_gb": random.choice([8, 16, 32]),
            "webgl_vendor": f"Google Inc. ({vendor})",
            "webgl_renderer": random.choice(FingerprintService.WEBGL_VENDORS[vendor])
        }

    @staticmethod
    def generate_mac_fingerprint() -> Dict:
        """Generate macOS fingerprint"""
        return {
            "os": "Mac OS X 14.7.2",
            "browser": "Chrome 119.0.0.0",
            "user_agent": FingerprintService.USER_AGENTS["Chrome 119 Mac"],
            "screen_resolution": random.choice(["1920x1080", "2560x1440", "2880x1800"]),
            "language": "en-US,en;q=0.9",
            "timezone": "America/Los_Angeles",
            "cpu_cores": random.choice([8, 10]),
            "memory_gb": random.choice([8, 16, 32]),
            "webgl_vendor": "Apple",
            "webgl_renderer": random.choice(FingerprintService.WEBGL_VENDORS["Apple"])
        }

    @staticmethod
    def generate_random() -> Dict:
        """Generate random realistic fingerprint"""
        os_type = random.choice(["Windows", "Mac"])

        if os_type == "Windows":
            return FingerprintService.generate_windows_fingerprint()
        else:
            return FingerprintService.generate_mac_fingerprint()
```

---

## Testing SeleniumBase Integration

**File: `tests/test_selenium.py`**

```python
import pytest
from app.services.selenium_manager import SeleniumManager
from app.models.profile import Profile

def test_start_profile():
    manager = SeleniumManager()

    # Create test profile
    profile = Profile(
        id="test123",
        name="Test Profile",
        os="Windows 10",
        browser="Chrome 120.0.0.0",
        user_agent="Mozilla/5.0...",
        screen_resolution="1920x1080",
        language="en-US",
        cpu_cores=8,
        memory_gb=8
    )

    # Start profile
    result = manager.start_profile(profile)

    assert "debug_port" in result
    assert "websocket_link" in result
    assert "pid" in result
    assert result["debug_port"] > 0

    # Stop profile
    manager.stop_profile("test123")

    assert not manager.is_running("test123")
```

## Next: See `05-electron-frontend.md` for desktop UI implementation
