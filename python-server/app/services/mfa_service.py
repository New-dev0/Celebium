"""MFA Service - TOTP generation and management"""
import pyotp
from typing import Optional


class MFAService:
    """Handle 2FA/MFA operations for profiles"""

    @staticmethod
    def generate_totp(secret: str) -> Optional[str]:
        """
        Generate current 6-digit TOTP code from secret
        
        Args:
            secret: Base32 encoded secret key
            
        Returns:
            6-digit code or None if invalid secret
        """
        if not secret:
            return None
            
        try:
            # Clean secret (remove spaces)
            clean_secret = secret.replace(" ", "")
            totp = pyotp.TOTP(clean_secret)
            return totp.now()
        except Exception as e:
            print(f"Error generating TOTP: {e}")
            return None

    @staticmethod
    def is_valid_secret(secret: str) -> bool:
        """Check if a secret is valid Base32"""
        try:
            clean_secret = secret.replace(" ", "")
            pyotp.TOTP(clean_secret).now()
            return True
        except:
            return False
