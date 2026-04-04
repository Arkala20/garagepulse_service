"""
utils/date_utils.py

Date and time utility functions for GaragePulse.
Handles formatting, current timestamps, and expiry calculations.
"""

from datetime import datetime, timedelta
from typing import Optional

from config.constants import DateFormats


class DateUtils:
    """
    Utility class for date and time operations.
    """

    # -------------------------------------------------
    # Current time helpers
    # -------------------------------------------------

    @staticmethod
    def now() -> datetime:
        """Return current datetime."""
        return datetime.now()

    @staticmethod
    def today() -> datetime:
        """Return current date (midnight time)."""
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # -------------------------------------------------
    # Formatting
    # -------------------------------------------------

    @staticmethod
    def format_date(date: datetime, fmt: str = DateFormats.DATE) -> str:
        """Format date to string."""
        if not date:
            return ""
        return date.strftime(fmt)

    @staticmethod
    def format_datetime(dt: datetime, fmt: str = DateFormats.DATETIME) -> str:
        """Format datetime to string."""
        if not dt:
            return ""
        return dt.strftime(fmt)

    # -------------------------------------------------
    # Parsing
    # -------------------------------------------------

    @staticmethod
    def parse_date(date_str: str, fmt: str = DateFormats.DATE) -> Optional[datetime]:
        """Parse string to date."""
        if not date_str:
            return None
        return datetime.strptime(date_str, fmt)

    @staticmethod
    def parse_datetime(
        dt_str: str, fmt: str = DateFormats.DATETIME
    ) -> Optional[datetime]:
        """Parse string to datetime."""
        if not dt_str:
            return None
        return datetime.strptime(dt_str, fmt)

    # -------------------------------------------------
    # Expiry handling
    # -------------------------------------------------

    @staticmethod
    def minutes_from_now(minutes: int) -> datetime:
        """Return datetime after given minutes."""
        return datetime.now() + timedelta(minutes=minutes)

    @staticmethod
    def is_expired(expiry_time: datetime) -> bool:
        """Check if a datetime is expired."""
        if not expiry_time:
            return True
        return datetime.now() > expiry_time

    # -------------------------------------------------
    # Comparisons
    # -------------------------------------------------

    @staticmethod
    def is_today(dt: datetime) -> bool:
        """Check if given datetime is today."""
        if not dt:
            return False
        return dt.date() == datetime.now().date()

    @staticmethod
    def days_between(start: datetime, end: datetime) -> int:
        """Return number of days between two dates."""
        if not start or not end:
            return 0
        return (end - start).days

    # -------------------------------------------------
    # Timestamp helpers
    # -------------------------------------------------

    @staticmethod
    def to_timestamp(dt: datetime) -> int:
        """Convert datetime to Unix timestamp."""
        if not dt:
            return 0
        return int(dt.timestamp())

    @staticmethod
    def from_timestamp(ts: int) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(ts)