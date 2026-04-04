"""
utils/response.py

Standard response wrapper for GaragePulse services.
Ensures consistent structure for success/failure handling.
"""

from typing import Any, Optional


class ServiceResponse:
    """
    Standard response object returned by service layer.
    """

    def __init__(
        self,
        success: bool,
        message: str = "",
        data: Optional[Any] = None,
        errors: Optional[Any] = None,
    ):
        self.success = success
        self.message = message
        self.data = data
        self.errors = errors

    def to_dict(self) -> dict:
        """
        Convert response to dictionary (useful for logging/debugging).
        """
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
        }

    @staticmethod
    def success_response(message: str = "", data: Any = None) -> "ServiceResponse":
        return ServiceResponse(
            success=True,
            message=message,
            data=data,
            errors=None,
        )

    @staticmethod
    def error_response(message: str = "", errors: Any = None) -> "ServiceResponse":
        return ServiceResponse(
            success=False,
            message=message,
            data=None,
            errors=errors,
        )