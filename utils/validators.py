"""
utils/validators.py

Validation utilities used across GaragePulse services and controllers.
"""

import re
from typing import Any, Optional

from utils.exceptions import ValidationError


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^[0-9+\-\s()]{7,20}$")
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
VIN_REGEX = re.compile(r"^[A-HJ-NPR-Z0-9]{11,17}$")
PLATE_REGEX = re.compile(r"^[A-Za-z0-9\- ]{3,15}$")


class Validators:
    """
    Collection of reusable validation helpers.
    """

    # -------------------------------------------------
    # Generic checks
    # -------------------------------------------------

    @staticmethod
    def require(value: Any, field_name: str) -> None:
        """Ensure value is provided."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required")

    @staticmethod
    def max_length(value: str, field_name: str, length: int) -> None:
        if value and len(value) > length:
            raise ValidationError(f"{field_name} must be at most {length} characters")

    @staticmethod
    def min_length(value: str, field_name: str, length: int) -> None:
        if value and len(value) < length:
            raise ValidationError(f"{field_name} must be at least {length} characters")

    # -------------------------------------------------
    # Email
    # -------------------------------------------------

    @staticmethod
    def validate_email(email: str) -> None:
        Validators.require(email, "Email")

        if not EMAIL_REGEX.match(email):
            raise ValidationError("Invalid email format")

    # -------------------------------------------------
    # Phone
    # -------------------------------------------------

    @staticmethod
    def validate_phone(phone: str) -> None:
        Validators.require(phone, "Phone number")

        if not PHONE_REGEX.match(phone):
            raise ValidationError("Invalid phone number")

    # -------------------------------------------------
    # Username
    # -------------------------------------------------

    @staticmethod
    def validate_username(username: str) -> None:
        Validators.require(username, "Username")

        if not USERNAME_REGEX.match(username):
            raise ValidationError(
                "Username must be 3–30 characters and contain only letters, numbers, ., -, _"
            )

    # -------------------------------------------------
    # Password
    # -------------------------------------------------

    @staticmethod
    def validate_password(password: str) -> None:
        Validators.require(password, "Password")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", password):
            raise ValidationError("Password must contain at least one number")

    # -------------------------------------------------
    # Vehicle plate
    # -------------------------------------------------

    @staticmethod
    def validate_plate_number(plate: str) -> None:
        Validators.require(plate, "Vehicle plate number")

        if not PLATE_REGEX.match(plate):
            raise ValidationError("Invalid vehicle plate number")

    # -------------------------------------------------
    # VIN
    # -------------------------------------------------

    @staticmethod
    def validate_vin(vin: Optional[str]) -> None:
        if vin and not VIN_REGEX.match(vin):
            raise ValidationError("Invalid VIN number")

    # -------------------------------------------------
    # Numeric validations
    # -------------------------------------------------

    @staticmethod
    def validate_positive_number(value: Any, field_name: str) -> None:
        try:
            number = float(value)
        except Exception:
            raise ValidationError(f"{field_name} must be a number")

        if number < 0:
            raise ValidationError(f"{field_name} must be positive")

    # -------------------------------------------------
    # Year validation
    # -------------------------------------------------

    @staticmethod
    def validate_vehicle_year(year: Optional[int]) -> None:
        if year is None:
            return

        if year < 1900 or year > 2100:
            raise ValidationError("Vehicle year must be between 1900 and 2100")