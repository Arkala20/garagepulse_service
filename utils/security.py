"""
utils/security.py

Security utilities for GaragePulse.
Handles password hashing/verification and secure token generation.
"""

from __future__ import annotations

import hashlib
import secrets

import bcrypt

from config.settings import settings


class Security:
    """
    Security helper methods for password and token operations.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt hashed password as UTF-8 string
        """
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a plain text password against a stored bcrypt hash.
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a secure random URL-safe token.
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token using SHA-256 for safer storage or comparisons.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()