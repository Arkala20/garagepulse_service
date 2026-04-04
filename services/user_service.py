"""
services/user_service.py

User management service for GaragePulse.
Handles staff registration, account activation/deactivation,
and user lookup workflows.

Professor alignment:
- Staff registration does NOT include an active checkbox.
- Active account management is handled separately.
"""

from __future__ import annotations

import logging
from typing import Optional

from config.constants import Roles
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from services.session_service import SessionService
from utils.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
)
from utils.response import ServiceResponse
from utils.security import Security
from utils.validators import Validators


logger = logging.getLogger(__name__)


class UserService:
    """
    Business logic for user and staff account management.
    """

    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()

    def register_staff(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        phone: Optional[str],
        password: str,
        role_code: str = Roles.STAFF,
    ) -> ServiceResponse:
        """
        Register a staff/admin user.

        Notes:
        - Only OWNER or ADMIN can create staff accounts.
        - Account is created inactive by default.
        - No active checkbox is used here.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            first_name = (first_name or "").strip()
            last_name = (last_name or "").strip()
            username = (username or "").strip()
            email = (email or "").strip().lower()
            phone = (phone or "").strip() if phone else None

            Validators.require(first_name, "First name")
            Validators.require(last_name, "Last name")
            Validators.validate_username(username)
            Validators.validate_email(email)
            Validators.validate_password(password)

            if phone:
                Validators.validate_phone(phone)

            if self.user_repo.exists_by_username(username):
                raise ConflictError("Username already exists.")

            if self.user_repo.exists_by_email(email):
                raise ConflictError("Email already exists.")

            role = self.role_repo.get_by_role_code(role_code)
            if not role:
                raise NotFoundError("Selected role was not found.")

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            password_hash = Security.hash_password(password)

            user_id = self.user_repo.create_user(
                {
                    "role_id": role["id"],
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username,
                    "email": email,
                    "phone": phone,
                    "password_hash": password_hash,
                    "is_active": 0,
                    "created_by": actor_id,
                    "updated_by": actor_id,
                }
            )

            logger.info(
                "User created successfully: user_id=%s, username=%s, role=%s",
                user_id,
                username,
                role_code,
            )

            return ServiceResponse.success_response(
                message=(
                    "Staff account created successfully. "
                    "Account is inactive until activated."
                ),
                data={
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "role_code": role_code,
                    "is_active": False,
                },
            )

        except (ConflictError, NotFoundError) as exc:
            logger.warning("User registration failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Unexpected error during user registration: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to create staff account."
            )

    def activate_user(self, user_id: int) -> ServiceResponse:
        """
        Activate a user account.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            user = self.user_repo.get_by_id(user_id)
            if not user or user.get("is_deleted"):
                raise NotFoundError("User not found.")

            if user.get("is_active"):
                return ServiceResponse.error_response(
                    message="User account is already active."
                )

            self.user_repo.activate_user(user_id)

            logger.info("User activated: user_id=%s", user_id)
            return ServiceResponse.success_response(
                message="User account activated successfully."
            )

        except NotFoundError as exc:
            logger.warning("Activate user failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to activate user: %s", exc)
            return ServiceResponse.error_response(message="Failed to activate user.")

    def deactivate_user(self, user_id: int) -> ServiceResponse:
        """
        Deactivate a user account.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            current_user = SessionService.get_current_user()
            if current_user and current_user.get("id") == user_id:
                return ServiceResponse.error_response(
                    message="You cannot deactivate your own account."
                )

            user = self.user_repo.get_by_id(user_id)
            if not user or user.get("is_deleted"):
                raise NotFoundError("User not found.")

            if not user.get("is_active"):
                return ServiceResponse.error_response(
                    message="User account is already inactive."
                )

            self.user_repo.deactivate_user(user_id)

            logger.info("User deactivated: user_id=%s", user_id)
            return ServiceResponse.success_response(
                message="User account deactivated successfully."
            )

        except NotFoundError as exc:
            logger.warning("Deactivate user failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to deactivate user: %s", exc)
            return ServiceResponse.error_response(message="Failed to deactivate user.")

    def get_all_staff(self) -> ServiceResponse:
        """
        Return all non-deleted operational users with role information.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            users = self.user_repo.get_all_staff()
            return ServiceResponse.success_response(
                message="Users retrieved successfully.",
                data=users,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve users: %s", exc)
            return ServiceResponse.error_response(message="Failed to retrieve users.")

    def get_active_users(self) -> ServiceResponse:
        """
        Return active users only.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            users = self.user_repo.get_active_users()
            return ServiceResponse.success_response(
                message="Active users retrieved successfully.",
                data=users,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve active users: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to retrieve active users."
            )

    def get_inactive_users(self) -> ServiceResponse:
        """
        Return inactive users only.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            users = self.user_repo.get_inactive_users()
            return ServiceResponse.success_response(
                message="Inactive users retrieved successfully.",
                data=users,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve inactive users: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to retrieve inactive users."
            )

    def get_user(self, user_id: int) -> ServiceResponse:
        """
        Get a single user with role information.
        """
        try:
            SessionService.require_role(Roles.OWNER, Roles.ADMIN)

            user = self.user_repo.get_user_with_role(user_id)
            if not user:
                return ServiceResponse.error_response(message="User not found.")

            return ServiceResponse.success_response(
                message="User retrieved successfully.",
                data=user,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authorization/authentication failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve user: %s", exc)
            return ServiceResponse.error_response(message="Failed to retrieve user.")