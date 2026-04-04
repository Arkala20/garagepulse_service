"""
config/settings.py

Centralized application configuration loader for GaragePulse.
Loads environment variables and exposes them as structured settings.
"""

import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # ============================================
    # Application Settings
    # ============================================
    APP_NAME: str = os.getenv("APP_NAME", "GaragePulse")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "True") == "True"
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    # ============================================
    # Database Settings
    # ============================================
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = os.getenv("DB_NAME", "garagepulse")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # ============================================
    # Security Settings
    # ============================================
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", 12))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "unsafe-secret-key")
    PASSWORD_RESET_TOKEN_EXPIRY_MINUTES: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 30)
    )

    # ============================================
    # Logging Settings
    # ============================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")

    # ============================================
    # Invoice / Business Settings
    # ============================================
    DEFAULT_TAX_RATE: float = float(os.getenv("DEFAULT_TAX_RATE", 8.5))
    CURRENCY: str = os.getenv("CURRENCY", "USD")

    # ============================================
    # Notification Settings
    # ============================================
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False") == "True"
    SMS_ENABLED: bool = os.getenv("SMS_ENABLED", "False") == "True"

    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "")
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "")

    # ============================================
    # Feature Flags
    # ============================================
    ENABLE_REPORTS: bool = os.getenv("ENABLE_REPORTS", "False") == "True"
    ENABLE_USER_MANAGEMENT: bool = os.getenv(
        "ENABLE_USER_MANAGEMENT", "False"
    ) == "True"

    # ============================================
    # Helper Methods
    # ============================================
    @property
    def DATABASE_CONFIG(self) -> dict:
        """Return DB config as dictionary (used by connection layer)."""
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "database": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
        }

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.APP_ENV.lower() == "development"


# Singleton instance to use across project
settings = Settings()