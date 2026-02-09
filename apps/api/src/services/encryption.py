"""
Encryption service for secure token storage using Fernet (AES-256-GCM)
"""
import base64
from cryptography.fernet import Fernet
from typing import Optional
import structlog

from ..config import settings

logger = structlog.get_logger()


class EncryptionService:
    """Service for encrypting and decrypting sensitive data like OAuth tokens"""

    def __init__(self):
        """Initialize encryption service with key from environment"""
        self._cipher = self._get_cipher()

    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher instance with proper key handling"""
        try:
            # In production, use a proper 32-byte Fernet key
            if settings.ENCRYPTION_KEY.startswith("dev-"):
                # Development key - generate a proper Fernet key
                key = Fernet.generate_key()
                logger.warning("Using generated encryption key for development")
            else:
                # Production - decode base64 key
                key = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY.encode())

            return Fernet(key)
        except Exception as e:
            logger.error("Failed to initialize encryption cipher", error=str(e))
            raise RuntimeError(f"Encryption initialization failed: {e}")

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token for secure storage

        Args:
            token: Plain text token to encrypt

        Returns:
            Base64 encoded encrypted token
        """
        if not token:
            raise ValueError("Token cannot be empty")

        try:
            encrypted_bytes = self._cipher.encrypt(token.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error("Token encryption failed", error=str(e))
            raise RuntimeError(f"Token encryption failed: {e}")

    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a token from storage

        Args:
            encrypted_token: Base64 encoded encrypted token

        Returns:
            Plain text token
        """
        if not encrypted_token:
            raise ValueError("Encrypted token cannot be empty")

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error("Token decryption failed", error=str(e))
            raise RuntimeError(f"Token decryption failed: {e}")

    def encrypt_json_field(self, data: Optional[str]) -> Optional[str]:
        """
        Encrypt a JSON string field (like refresh_token)

        Args:
            data: JSON string to encrypt

        Returns:
            Encrypted JSON string or None if input is None
        """
        if data is None:
            return None
        return self.encrypt_token(data)

    def decrypt_json_field(self, encrypted_data: Optional[str]) -> Optional[str]:
        """
        Decrypt a JSON string field

        Args:
            encrypted_data: Encrypted JSON string

        Returns:
            Decrypted JSON string or None if input is None
        """
        if encrypted_data is None:
            return None
        return self.decrypt_token(encrypted_data)


# Singleton instance
encryption_service = EncryptionService()