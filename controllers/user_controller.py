"""
controllers/user_controller.py

User controller for GaragePulse.
Handles UI requests related to staff registration,
account activation/deactivation, and user retrieval.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.user_service import UserService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class UserController:
    """
    Controller for user management workflows.
    """

    def __init__(self) -> None:
        self.user_service = UserService()

    def register_staff(
        self,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        phone: Optional[str],
        password: str,
        role_code: str = "STAFF",
    ) -> ServiceResponse:
        """
        Create a staff/admin account.

        Professor requirement:
        No active checkbox — account is created inactive.
        """
        logger.info(
            "Registering staff user username=%s email=%s role=%s",
            username,
            email,
            role_code,
        )

        return self.user_service.register_staff(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone=phone,
            password=password,
            role_code=role_code,
        )

    def activate_user(self, user_id: int) -> ServiceResponse:
        """
        Activate a user account.
        """
        logger.info("Activating user id=%s", user_id)

        return self.user_service.activate_user(user_id)

    def deactivate_user(self, user_id: int) -> ServiceResponse:
        """
        Deactivate a user account.
        """
        logger.info("Deactivating user id=%s", user_id)

        return self.user_service.deactivate_user(user_id)

    def get_all_staff(self) -> ServiceResponse:
        """
        Retrieve all staff/admin users.

        Used by Active Accounts page.
        """
        logger.debug("Fetching all staff users")

        return self.user_service.get_all_staff()

    def get_active_users(self) -> ServiceResponse:
        """
        Retrieve only active users.
        """
        logger.debug("Fetching active users")

        return self.user_service.get_active_users()

    def get_inactive_users(self) -> ServiceResponse:
        """
        Retrieve inactive users.

        Useful for account activation page.
        """
        logger.debug("Fetching inactive users")

        return self.user_service.get_inactive_users()

    def get_user(self, user_id: int) -> ServiceResponse:
        """
        Retrieve a specific user.
        """
        logger.debug("Fetching user id=%s", user_id)

        return self.user_service.get_user(user_id)