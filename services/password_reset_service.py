"""
services/password_reset_service.py
"""

from __future__ import annotations

import logging
from datetime import timedelta

from config.settings import settings
from repositories.password_reset_repository import PasswordResetRepository
from repositories.user_repository import UserRepository
from services.email_service import EmailService
from utils.response import ServiceResponse
from utils.security import Security
from utils.validators import Validators


logger = logging.getLogger(__name__)


class PasswordResetService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.password_reset_repo = PasswordResetRepository()
        self.email_service = EmailService()

    def request_password_reset(self, identifier: str) -> ServiceResponse:
        try:
            identifier = (identifier or "").strip()
            Validators.require(identifier, "Email or Username")

            user = self.user_repo.get_by_email_or_username(identifier)
            if not user:
                return ServiceResponse.success_response(
                    message="If an account exists, a reset token has been sent to the registered email."
                )

            if user.get("is_deleted"):
                return ServiceResponse.error_response(
                    message="This account is no longer available."
                )

            user_email = str(user.get("email") or "").strip()
            if not user_email:
                return ServiceResponse.error_response(
                    message="No email is registered for this account."
                )

            token = Security.generate_token(32)

            db_now_row = self.password_reset_repo.get_database_now()
            if not db_now_row or not db_now_row.get("db_now"):
                return ServiceResponse.error_response(
                    message="Failed to read database time for password reset."
                )

            db_now = db_now_row["db_now"]
            expires_at = db_now + timedelta(
                minutes=settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
            )

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
                "RESET CREATE | user_id=%s | token=%r | db_now=%s | expires_at=%s | via=%s",
                user["id"],
                token,
                db_now.strftime("%Y-%m-%d %H:%M:%S"),
                expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                requested_via,
            )

            subject = "GaragePulse Password Reset Token"
            body = (
                f"Hello {user.get('first_name', 'User')},\n\n"
                f"You requested a password reset for your GaragePulse account.\n\n"
                f"Your reset token is:\n{token}\n\n"
                f"This token expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"GaragePulse Auto Service Management System"
            )

            email_response = self.email_service.send_email(
                to_email=user_email,
                subject=subject,
                body=body,
            )

            if not email_response.success:
                return ServiceResponse.error_response(
                    message=f"Reset token created, but email sending failed: {email_response.message}"
                )

            return ServiceResponse.success_response(
                message="If an account exists, a reset token has been sent to the registered email."
            )

        except Exception as exc:
            logger.exception("Failed to create password reset request: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to create password reset request."
            )

    def validate_reset_token(self, reset_token: str) -> ServiceResponse:
        try:
            reset_token = (reset_token or "").strip()
            Validators.require(reset_token, "Reset token")

            reset_request = self.password_reset_repo.get_valid_token(reset_token)

            logger.info(
                "RESET VALIDATE | token=%r | found=%s | row=%s",
                reset_token,
                bool(reset_request),
                reset_request,
            )

            if not reset_request:
                latest = self.password_reset_repo.get_by_reset_token(reset_token)
                logger.warning(
                    "RESET VALIDATE MISS | token=%r | raw_row=%s",
                    reset_token,
                    latest,
                )
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

            logger.info(
                "RESET APPLY | token=%r | found=%s | row=%s",
                reset_token,
                bool(reset_request),
                reset_request,
            )

            if not reset_request:
                latest = self.password_reset_repo.get_by_reset_token(reset_token)
                logger.warning(
                    "RESET APPLY MISS | token=%r | raw_row=%s",
                    reset_token,
                    latest,
                )
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
                "RESET SUCCESS | user_id=%s | token=%r",
                reset_request["user_id"],
                reset_token,
            )

            return ServiceResponse.success_response(
                message="Password has been reset successfully."
            )

        except Exception as exc:
            logger.exception("Failed to reset password: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to reset password."
            )