"""
services/auth_service.py

Authentication service for GaragePulse.
Handles login using email or username, account checks,
and returns role-aware user data for session management.
"""

from __future__ import annotations

import logging

from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from utils.response import ServiceResponse
from utils.security import Security
from utils.validators import Validators


logger = logging.getLogger(__name__)


class AuthService:
    """
    Service responsible for authentication logic.
    """

    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()

    def login(self, identifier: str, password: str) -> ServiceResponse:
        """
        Login using email OR username.

        Returns session-safe user data including role_code and role_name.
        """
        try:
            identifier = (identifier or "").strip()
            password = password or ""

            Validators.require(identifier, "Email or Username")
            Validators.require(password, "Password")

            user = self.user_repo.get_by_email_or_username(identifier)
            if not user:
                return ServiceResponse.error_response(
                    message="Invalid email/username or password."
                )

            if user.get("is_deleted"):
                return ServiceResponse.error_response(
                    message="This account is no longer available."
                )

            if not user.get("is_active"):
                return ServiceResponse.error_response(
                    message="Account is inactive. Contact the owner/admin."
                )

            password_hash = user.get("password_hash")
            if not password_hash or not Security.verify_password(password, password_hash):
                return ServiceResponse.error_response(
                    message="Invalid email/username or password."
                )

            role = self.role_repo.get_by_id(user["role_id"])
            if not role:
                return ServiceResponse.error_response(
                    message="User role is invalid. Contact administrator."
                )

            self.user_repo.update_last_login(user["id"])

            session_user = {
                "id": user["id"],
                "role_id": user["role_id"],
                "role_code": role["role_code"],
                "role_name": role["role_name"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "full_name": f"{user['first_name']} {user['last_name']}".strip(),
                "username": user["username"],
                "email": user["email"],
                "phone": user.get("phone"),
                "is_active": user["is_active"],
                "last_login_at": user.get("last_login_at"),
            }

            logger.info(
                "Login successful: user_id=%s, username=%s, role=%s",
                user["id"],
                user["username"],
                role["role_code"],
            )

            return ServiceResponse.success_response(
                message="Login successful.",
                data=session_user,
            )

        except Exception as exc:
            logger.exception("Login failed: %s", exc)
            return ServiceResponse.error_response(
                message="Login failed."
            )

    def validate_credentials(self, identifier: str, password: str) -> bool:
        """
        Quick credential validation helper.
        """
        try:
            identifier = (identifier or "").strip()
            password = password or ""

            if not identifier or not password:
                return False

            user = self.user_repo.get_by_email_or_username(identifier)
            if not user:
                return False

            if user.get("is_deleted") or not user.get("is_active"):
                return False

            return Security.verify_password(password, user["password_hash"])

        except Exception:
            return False