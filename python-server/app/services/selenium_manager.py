"""SeleniumBase Manager - Browser launch and control"""
from seleniumbase import Driver, SB
from typing import Dict, List, Optional
import os
import psutil
import requests
from datetime import datetime


class SeleniumManager:
    """
    Manages SeleniumBase browser instances for profiles.

    Handles:
    - Browser launching with UC Mode
    - Fingerprint injection via CDP
    - Process management
    - Multiple concurrent profiles
    """

    def __init__(self):
        self.running_profiles: Dict[str, Dict] = {}
        # Structure: {
        #   "profile_id": {
        #       "sb_context": <SB context manager>,
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
        Launch browser with profile configuration using SeleniumBase UC Mode.

        Args:
            profile: Profile database model
            chrome_flags: Additional Chrome flags
            start_pages: URLs to open on startup

        Returns:
            Dict with debug_port, websocket_link, pid
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
            # Initialize SB context
            sb_context = SB(
                uc=True,  # Undetected Chrome mode
                headless=False,
                user_data_dir=user_data_dir,
                chromium_arg=",".join(chrome_options),
                # Apply fingerprint overrides
                locale=profile.language.split(',')[0] if profile.language else "en-US",
            )
            
            # Enter the context to get the sb instance (BaseCase)
            sb = sb_context.__enter__()
            driver = sb.driver

            # Start the browser at blank page
            driver.get("about:blank")

            # Get debug info
            debug_port = self._get_debug_port(driver)
            websocket_url = self._get_websocket_url(driver, debug_port)
            
            # Get PID
            pid = None
            if hasattr(driver, "service") and driver.service.process:
                pid = driver.service.process.pid
            elif hasattr(driver, "browser_pid"):
                pid = driver.browser_pid

            # Apply advanced fingerprint overrides via CDP
            self._apply_fingerprint_overrides(sb, profile)

            # Open start pages if specified
            if start_pages:
                for idx, page_url in enumerate(start_pages):
                    if idx == 0:
                        driver.get(page_url)
                    else:
                        driver.execute_script(f"window.open('{page_url}', '_blank');")

            # Store running instance
            self.running_profiles[profile_id] = {
                "sb_context": sb_context,
                "sb": sb,
                "driver": driver,
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
        """
        Stop and cleanup profile browser.

        Args:
            profile_id: Profile ID to stop

        Raises:
            Exception if profile not running
        """
        if profile_id not in self.running_profiles:
            raise Exception(f"Profile {profile_id} is not running")

        profile_data = self.running_profiles[profile_id]

        try:
            # Close browser gracefully via context exit
            sb_context = profile_data["sb_context"]
            sb_context.__exit__(None, None, None)

        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")

            # Force kill if needed
            try:
                pid = profile_data["pid"]
                if pid:
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=5)
            except:
                pass

        finally:
            # Remove from running profiles
            if profile_id in self.running_profiles:
                del self.running_profiles[profile_id]

    def close_all(self):
        """Close all running profiles (called on app shutdown)"""
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
        """
        Build Chrome launch arguments based on profile config.

        Args:
            profile: Profile model
            user_data_dir: Path to Chrome user data directory
            extra_flags: Additional flags from API request

        Returns:
            List of Chrome flags
        """
        options = []

        # Window size
        if profile.screen_resolution:
            width, height = profile.screen_resolution.split('x')
            options.append(f"--window-size={width},{height}")

        # Proxy
        if profile.proxy_string:
            options.append(f"--proxy-server={profile.proxy_string}")

        # WebRTC mode
        if profile.webrtc_mode == 'disabled':
            options.append("--disable-webrtc")

        # Additional flags
        options.extend(extra_flags)

        return options

    def _get_debug_port(self, driver) -> int:
        """Extract Chrome DevTools debug port from driver"""
        try:
            # Check if it was explicitly set or can be found in service
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

        return 9222 # Default Chrome debug port

    def _get_websocket_url(self, driver, debug_port: int) -> str:
        """Get WebSocket debugger URL"""
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
        Apply fingerprint overrides via Chrome DevTools Protocol (CDP).

        Overrides:
        - User Agent
        - Platform (OS)
        - Hardware Concurrency (CPU cores)
        - Device Memory
        - WebGL Vendor/Renderer
        - Canvas fingerprint (add noise)
        Apply fingerprint overrides via Chrome DevTools Protocol (CDP)
        """
        try:
            # Activate CDP mode
            sb.activate_cdp_mode("about:blank")
            driver = sb.driver

            # Enable Elite Stealth Utilities
            is_elite = profile.stealth_tier == 'elite'
            
            # Ad-blocking via CDP
            if profile.adblock_enabled:
                try:
                    driver.execute_cdp_cmd('Network.setBlockedURLs', {
                        'urls': [
                            "*.googlesyndication.com*", "*.googletagmanager.com*",
                            "*.google-analytics.com*", "*.amazon-adsystem.com*",
                            "*.doubleclick.net*", "*.adsafeprotected.com*",
                            "*.facebook.net/en_US/fbevents.js*"
                        ]
                    })
                except:
                    pass

            # Override User Agent
            if profile.user_agent:
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    'userAgent': profile.user_agent
                })

            # Platform and Hardware metrics
            platform = self._get_platform_from_os(profile.os)
            
            # Use stable noise seeds per profile session for better trust score
            import random
            noise_seed = random.randint(1, 1000)

            injection_script = f"""
                // Navigator Spoofing
                Object.defineProperty(navigator, 'platform', {{ get: () => '{platform}' }});
                Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {profile.cpu_cores or 8} }});
                Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {profile.memory_gb or 8} }});
                
                // Stable Noise Injection (Non-random per pixel to avoid detection)
                const NOISE_SEED = {noise_seed};
            """
            
            # WebGL Vendor/Renderer and Parameters
            if profile.webgl_vendor and profile.webgl_renderer:
                injection_script += f"""
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        if (parameter === 37445) return '{profile.webgl_vendor}';
                        if (parameter === 37446) return '{profile.webgl_renderer}';
                        // Add some common WebGL limits for better consistency
                        if (parameter === 3379) return 16384; // MAX_TEXTURE_SIZE
                        return getParameter.apply(this, arguments);
                    }};
                """

            # Improved Canvas Noise (Session-based stable offset)
            if profile.canvas_mode == 'noise':
                injection_script += """
                    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                        const imageData = getImageData.apply(this, arguments);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            // Stable noise based on pixel index and session seed
                            imageData.data[i] = (imageData.data[i] + (NOISE_SEED % 2)) % 256;
                        }
                        return imageData;
                    };
                """

            # Improved Audio Noise
            if profile.audio_mode == 'noise':
                injection_script += """
                    const originalChannelData = AudioBuffer.prototype.getChannelData;
                    AudioBuffer.prototype.getChannelData = function() {
                        const buffer = originalChannelData.apply(this, arguments);
                        const offset = (NOISE_SEED / 1000000);
                        for (let i = 0; i < buffer.length; i += 100) {
                            buffer[i] += offset;
                        }
                        return buffer;
                    };
                """

            # Extra Elite Mode Protections
            if is_elite:
                injection_script += """
                    // Disable Automation detection flags
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    
                    // Spoof Client Hints
                    if (navigator.userAgentData) {
                        const originalGetHighEntropyValues = navigator.userAgentData.getHighEntropyValues;
                        navigator.userAgentData.getHighEntropyValues = function(hints) {
                            return Promise.resolve({
                                brands: [
                                    {brand: 'Not A(Brand', version: '99'},
                                    {brand: 'Google Chrome', version: '120'},
                                    {brand: 'Chromium', version: '120'}
                                ],
                                mobile: false,
                                platform: 'Windows'
                            });
                        };
                    }
                """

            # Add script to evaluate on new document
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': injection_script
            })

            # Timezone & Geolocation
            if profile.timezone:
                driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                    'timezoneId': profile.timezone
                })

            if profile.geolocation and ',' in profile.geolocation:
                try:
                    lat, lon = map(float, profile.geolocation.split(','))
                    driver.execute_cdp_cmd('Browser.grantPermissions', {
                        'permissions': ['geolocation'],
                    })
                    driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
                        'latitude': lat,
                        'longitude': lon,
                        'accuracy': 100
                    })
                except: pass

            # Reconnect
            sb.reconnect()

        except Exception as e:
            print(f"⚠️ Error applying fingerprint overrides: {e}")

    def _get_platform_from_os(self, os_name: str) -> str:
        """Map OS name to navigator.platform value"""
        os_lower = os_name.lower()
        if 'windows' in os_lower: return 'Win32'
        if 'mac' in os_lower: return 'MacIntel'
        if 'linux' in os_lower: return 'Linux x86_64'
        if 'android' in os_lower: return 'Linux armv8l'
        if 'iphone' in os_lower or 'ipad' in os_lower: return 'iPhone'
        return 'Win32'

    def is_running(self, profile_id: str) -> bool:
        """Check if profile is currently running"""
        return profile_id in self.running_profiles

    def get_running_profile(self, profile_id: str) -> Optional[Dict]:
        """Get running profile data"""
        return self.running_profiles.get(profile_id)

    def cdp_click(self, profile_id: str, selector: str):
        """Perform a trusted click via CDP (bypasses most detection)"""
        data = self.get_running_profile(profile_id)
        if not data: return
        
        sb = data["sb"]
        # Use CDP mode to find element and click
        sb.activate_cdp_mode(sb.get_current_url())
        sb.cdp.click(selector)
        sb.reconnect()

    def cdp_type(self, profile_id: str, selector: str, text: str):
        """Perform trusted typing via CDP"""
        data = self.get_running_profile(profile_id)
        if not data: return
        
        sb = data["sb"]
        sb.activate_cdp_mode(sb.get_current_url())
        sb.cdp.type(selector, text)
        sb.reconnect()

    def get_stats(self) -> Dict:
        """
        Get statistics about running profiles.

        Returns:
            Dict with running_count, total_memory_mb, profiles list
        """
        total_memory = 0
        for profile_id, data in self.running_profiles.items():
            try:
                pid = data["pid"]
                if pid:
                    process = psutil.Process(pid)
                    total_memory += process.memory_info().rss / (1024 * 1024)  # MB
            except:
                pass

        return {
            "running_count": len(self.running_profiles),
            "total_memory_mb": round(total_memory, 2),
            "profiles": list(self.running_profiles.keys())
        }
