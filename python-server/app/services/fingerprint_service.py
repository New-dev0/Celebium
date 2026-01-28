"""Fingerprint Generation Service"""
import random
from typing import Dict, List


class FingerprintService:
    """Generate realistic browser fingerprints for different platforms"""

    # Common User Agents (keep updated)
    USER_AGENTS = {
        "Chrome 120 Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Chrome 119 Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Chrome 120 Mac": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Edge 120 Windows": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    }

    # Common Screen Resolutions
    RESOLUTIONS = [
        "1920x1080",  # Most common (Full HD)
        "1366x768",   # Laptop standard
        "1536x864",   # Laptop
        "1440x900",   # MacBook
        "1600x900",   # Common
        "2560x1440",  # 2K
        "1280x1024",  # Old but still used
    ]

    # WebGL Configurations
    WEBGL_VENDORS = {
        "NVIDIA": [
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0)"),
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"),
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)"),
            ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA GeForce GTX 1660 Super Direct3D11 vs_5_0 ps_5_0)"),
        ],
        "AMD": [
            ("Google Inc. (AMD)", "ANGLE (AMD Radeon RX 6750 XT Direct3D11 vs_5_0 ps_5_0)"),
            ("Google Inc. (AMD)", "ANGLE (AMD Radeon RX 7900 XT Direct3D11 vs_5_0 ps_5_0)"),
            ("Google Inc. (AMD)", "ANGLE (AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)"),
        ],
        "Intel": [
            ("Google Inc. (Intel)", "ANGLE (Intel UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"),
            ("Google Inc. (Intel)", "ANGLE (Intel Iris Xe Graphics Direct3D11 vs_5_0 ps_5_0)"),
        ],
        "Apple": [
            ("Apple", "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)"),
            ("Apple", "ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)"),
        ]
    }

    # Language Configurations
    LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
    ]

    # Timezones
    TIMEZONES_US = [
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
    ]

    @staticmethod
    def generate_windows_fingerprint() -> Dict:
        """
        Generate realistic Windows 10/11 fingerprint.

        Returns:
            Dict with os, browser, user_agent, screen, CPU, memory, WebGL, language, timezone
        """
        # Pick GPU vendor
        vendor = random.choice(["NVIDIA", "AMD", "Intel"])
        webgl_vendor, webgl_renderer = random.choice(FingerprintService.WEBGL_VENDORS[vendor])

        return {
            "os": "Windows 10",
            "browser": "Chrome 120.0.0.0",
            "user_agent": FingerprintService.USER_AGENTS["Chrome 120 Windows"],
            "screen_resolution": random.choice(FingerprintService.RESOLUTIONS),
            "language": random.choice(FingerprintService.LANGUAGES),
            "timezone": random.choice(FingerprintService.TIMEZONES_US),
            "cpu_cores": random.choice([4, 6, 8, 12, 16]),
            "memory_gb": random.choice([8, 16, 32]),
            "webgl_vendor": webgl_vendor,
            "webgl_renderer": webgl_renderer,
            "webrtc_mode": "altered",
            "canvas_mode": "noise",
            "audio_mode": "noise"
        }

    @staticmethod
    def generate_mac_fingerprint() -> Dict:
        """
        Generate realistic macOS fingerprint.

        Returns:
            Dict with os, browser, user_agent, screen, CPU, memory, WebGL, language, timezone
        """
        webgl_vendor, webgl_renderer = random.choice(FingerprintService.WEBGL_VENDORS["Apple"])

        return {
            "os": "Mac OS X 14.7.2",
            "browser": "Chrome 120.0.0.0",
            "user_agent": FingerprintService.USER_AGENTS["Chrome 120 Mac"],
            "screen_resolution": random.choice(["1920x1080", "2560x1440", "2880x1800"]),
            "language": random.choice(FingerprintService.LANGUAGES),
            "timezone": "America/Los_Angeles",
            "cpu_cores": random.choice([8, 10]),
            "memory_gb": random.choice([8, 16, 32, 64]),
            "webgl_vendor": webgl_vendor,
            "webgl_renderer": webgl_renderer,
            "webrtc_mode": "altered",
            "canvas_mode": "noise",
            "audio_mode": "noise"
        }

    @staticmethod
    def generate_random() -> Dict:
        """
        Generate random realistic fingerprint (Windows or Mac).

        Returns:
            Dict with complete fingerprint configuration
        """
        os_type = random.choice(["Windows", "Mac"])

        if os_type == "Windows":
            return FingerprintService.generate_windows_fingerprint()
        else:
            return FingerprintService.generate_mac_fingerprint()

    @staticmethod
    def get_predefined_configs() -> Dict:
        """
        Return a dictionary of predefined configurations (templates)
        
        Returns:
            Dict { config_id: { details... } }
        """
        return {
            "1839115": {
                "browser": "Chrome 120.0.0.0",
                "os": "Windows 10",
                "screen": "1920x1080",
                "useragent": FingerprintService.USER_AGENTS["Chrome 120 Windows"],
                "webgl": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)"
            },
            "1839116": {
                "browser": "Chrome 120.0.0.0",
                "os": "Mac OS X 14.7.2",
                "screen": "2880x1800",
                "useragent": FingerprintService.USER_AGENTS["Chrome 120 Mac"],
                "webgl": "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)"
            },
            "1839117": {
                "browser": "Edge 120.0.0.0",
                "os": "Windows 10",
                "screen": "1536x864",
                "useragent": FingerprintService.USER_AGENTS["Edge 120 Windows"],
                "webgl": "ANGLE (Intel, Intel Iris Xe Graphics Direct3D11 vs_5_0 ps_5_0)"
            }
        }

    @staticmethod
    def get_user_agent_by_browser(os: str, browser: str, version: str) -> str:
        """
        Get user agent string for specific OS/browser combination.

        Args:
            os: Operating system (e.g., "Windows 10", "Mac OS X")
            browser: Browser name (e.g., "Chrome", "Edge")
            version: Browser version (e.g., "120.0.0.0")

        Returns:
            User agent string
        """
        # Simplified - in production, maintain comprehensive database
        if "Windows" in os:
            if "Edge" in browser:
                return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}"
            else:
                return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        elif "Mac" in os:
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        else:
            return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
