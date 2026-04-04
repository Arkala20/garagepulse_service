"""
services/session_service.py

Session management for GaragePulse desktop application.
Handles current logged-in user, role checks, and access control.
Uses custom application exceptions for cleaner service/controller handling.
"""

from __future__ import annotations

from typing import Dict, Optional

from utils.exceptions import AuthenticationError, AuthorizationError


class SessionService:
    """
    Singleton-style session manager for desktop app.
    """

    _current_user: Optional[Dict] = None

    @classmethod
    def set_current_user(cls, user: Dict) -> None:
        """
        Set the currently logged-in user.
        """
        cls._current_user = user

    @classmethod
    def get_current_user(cls) -> Optional[Dict]:
        """
        Get the current logged-in user.
        """
        return cls._current_user

    @classmethod
    def clear_session(cls) -> None:
        """
        Clear the current session.
        """
        cls._current_user = None

    @classmethod
    def is_authenticated(cls) -> bool:
        """
        Return True if a user is logged in.
        """
        return cls._current_user is not None

    @classmethod
    def get_role_code(cls) -> Optional[str]:
        """
        Return the role_code of the current user, if available.
        """
        if not cls._current_user:
            return None
        return cls._current_user.get("role_code")

    @classmethod
    def is_owner(cls) -> bool:
        return cls.get_role_code() == "OWNER"

    @classmethod
    def is_admin(cls) -> bool:
        return cls.get_role_code() == "ADMIN"

    @classmethod
    def is_staff(cls) -> bool:
        return cls.get_role_code() == "STAFF"

    @classmethod
    def has_role(cls, *roles: str) -> bool:
        """
        Check whether the current user has one of the given roles.
        """
        role_code = cls.get_role_code()
        return role_code in roles if role_code else False

    @classmethod
    def require_authentication(cls) -> None:
        """
        Ensure a user is logged in.
        Raises AuthenticationError if not authenticated.
        """
        if not cls.is_authenticated():
            raise AuthenticationError("User is not authenticated.")

    @classmethod
    def require_role(cls, *roles: str) -> None:
        """
        Ensure the current user is authenticated and has one of the required roles.
        Raises AuthenticationError or AuthorizationError when access is denied.
        """
        cls.require_authentication()

        if not cls.has_role(*roles):
            allowed = ", ".join(roles)
            raise AuthorizationError(
                f"Access denied. Required role(s): {allowed}."
            )