"""
services/password_reset_service.py

Password reset service for GaragePulse.
Handles forgot password and reset password workflows.
Aligned with schema.sql and corrected repository structure.
"""

from __future__ import annotations

import logging

from config.settings import settings
from repositories.password_reset_repository import PasswordResetRepository
from repositories.user_repository import UserRepository
from utils.response import ServiceResponse
from utils.security import Security
from utils.validators import Validators


logger = logging.getLogger(__name__)


class PasswordResetService:
    """
    Service responsible for forgot password and reset password flows.
    """

    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.password_reset_repo = PasswordResetRepository()

    def request_password_reset(self, identifier: str) -> ServiceResponse:
        """
        Create a password reset request using email or username.

        For desktop/dev usage, the token is returned in the response.
        In production, this token should be delivered through email/SMS.
        """
        try:
            identifier = (identifier or "").strip()
            Validators.require(identifier, "Email or Username")

            user = self.user_repo.get_by_email_or_username(identifier)
            if not user:
                return ServiceResponse.error_response(
                    message="No account found for the provided email or username."
                )

            if user.get("is_deleted"):
                return ServiceResponse.error_response(
                    message="This account is no longer available."
                )

            token = Security.generate_token(32)
            expires_at = __import__("datetime").datetime.now() + __import__(
                "datetime"
            ).timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)

            requested_via = "email" if "@" in identifier else "username"

            self.password_reset_repo.invalidate_user_tokens(user["id"])

            self.password_reset_repo.create_reset_request(
                {
                    "user_id": user["id"],
                    "reset_token": token,
                    "requested_via": requested_via,
                    "expires_at": expires_at,
                }
            )

            logger.info(
                "Password reset requested successfully: user_id=%s via=%s",
                user["id"],
                requested_via,
            )

            return ServiceResponse.success_response(
                message="Password reset request created successfully.",
                data={
                    "reset_token": token,
                    "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "user_id": user["id"],
                },
            )

        except Exception as exc:
            logger.exception("Failed to create password reset request: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to create password reset request."
            )

    def validate_reset_token(self, reset_token: str) -> ServiceResponse:
        """
        Validate whether a reset token exists, is unused, and is not expired.
        """
        try:
            reset_token = (reset_token or "").strip()
            Validators.require(reset_token, "Reset token")

            reset_request = self.password_reset_repo.get_valid_token(reset_token)
            if not reset_request:
                return ServiceResponse.error_response(
                    message="Reset token is invalid, expired, or already used."
                )

            return ServiceResponse.success_response(
                message="Reset token is valid.",
                data=reset_request,
            )

        except Exception as exc:
            logger.exception("Failed to validate reset token: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to validate reset token."
            )

    def reset_password(
        self,
        reset_token: str,
        new_password: str,
        confirm_password: str,
    ) -> ServiceResponse:
        """
        Reset a user's password using a valid token.
        """
        try:
            reset_token = (reset_token or "").strip()
            new_password = new_password or ""
            confirm_password = confirm_password or ""

            Validators.require(reset_token, "Reset token")
            Validators.require(new_password, "New password")
            Validators.require(confirm_password, "Confirm password")

            if new_password != confirm_password:
                return ServiceResponse.error_response(
                    message="New password and confirm password do not match."
                )

            Validators.validate_password(new_password)

            reset_request = self.password_reset_repo.get_valid_token(reset_token)
            if not reset_request:
                return ServiceResponse.error_response(
                    message="Reset token is invalid, expired, or already used."
                )

            user = self.user_repo.get_by_id(reset_request["user_id"])
            if not user or user.get("is_deleted"):
                return ServiceResponse.error_response(
                    message="User account not found."
                )

            new_password_hash = Security.hash_password(new_password)

            self.user_repo.update_password(
                reset_request["user_id"],
                new_password_hash,
            )

            self.password_reset_repo.mark_as_used(reset_request["id"])

            logger.info(
                "Password reset successful: user_id=%s",
                reset_request["user_id"],
            )

            return ServiceResponse.success_response(
                message="Password has been reset successfully."
            )

        except Exception as exc:
            logger.exception("Failed to reset password: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to reset password."
            )

    def get_latest_active_request_for_user(self, user_id: int) -> ServiceResponse:
        """
        Return the latest active reset request for a user.
        Useful for debugging/admin support.
        """
        try:
            request = self.password_reset_repo.get_latest_active_request_for_user(
                user_id
            )

            if not request:
                return ServiceResponse.error_response(
                    message="No active password reset request found."
                )

            return ServiceResponse.success_response(
                message="Active password reset request retrieved successfully.",
                data=request,
            )

        except Exception as exc:
            logger.exception(
                "Failed to retrieve latest active password reset request: %s",
                exc,
            )
            return ServiceResponse.error_response(
                message="Failed to retrieve password reset request."
            )