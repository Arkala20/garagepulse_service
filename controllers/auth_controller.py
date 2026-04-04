"""
controllers/auth_controller.py

Authentication controller for GaragePulse.
Bridges UI actions with authentication/session services.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.auth_service import AuthService
from services.password_reset_service import PasswordResetService
from services.session_service import SessionService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class AuthController:
    """
    Controller for authentication-related UI actions.
    """

    def __init__(self) -> None:
        self.auth_service = AuthService()
        self.password_reset_service = PasswordResetService()

    def login(self, identifier: str, password: str) -> ServiceResponse:
        """
        Authenticate user and initialize session.
        """
        response = self.auth_service.login(identifier, password)

        if response.success and response.data:
            SessionService.set_current_user(response.data)
            logger.info(
                "Session started for user_id=%s",
                response.data.get("id"),
            )

        return response

    def logout(self) -> ServiceResponse:
        """
        Clear current session.
        """
        current_user = SessionService.get_current_user()
        SessionService.clear_session()

        logger.info(
            "Session cleared for user_id=%s",
            current_user.get("id") if current_user else None,
        )

        return ServiceResponse.success_response(
            message="Logged out successfully."
        )

    def get_current_session_user(self) -> ServiceResponse:
        """
        Return currently logged-in user.
        """
        user = SessionService.get_current_user()

        if not user:
            return ServiceResponse.error_response(
                message="No active session found."
            )

        return ServiceResponse.success_response(
            message="Current session retrieved successfully.",
            data=user,
        )

    def request_password_reset(self, identifier: str) -> ServiceResponse:
        """
        Start forgot password flow.
        """
        return self.password_reset_service.request_password_reset(identifier)

    def validate_reset_token(self, reset_token: str) -> ServiceResponse:
        """
        Validate reset token before showing reset form.
        """
        return self.password_reset_service.validate_reset_token(reset_token)

    def reset_password(
        self,
        reset_token: str,
        new_password: str,
        confirm_password: str,
    ) -> ServiceResponse:
        """
        Complete password reset flow.
        """
        return self.password_reset_service.reset_password(
            reset_token=reset_token,
            new_password=new_password,
            confirm_password=confirm_password,
        )

    def is_authenticated(self) -> bool:
        """
        Simple helper for UI guards.
        """
        return SessionService.is_authenticated()

    def get_role_code(self) -> Optional[str]:
        """
        Return current role code for route/sidebar decisions.
        """
        return SessionService.get_role_code()