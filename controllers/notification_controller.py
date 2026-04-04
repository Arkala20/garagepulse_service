"""
controllers/notification_controller.py

Notification controller for GaragePulse.
Bridges UI with NotificationService for creating, viewing,
and updating notification delivery status.

Professor alignment:
- List shows customer name (handled in service/repo)
- Clicking opens full notification details
"""

from __future__ import annotations

import logging
from typing import Optional

from services.notification_service import NotificationService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class NotificationController:
    """
    Controller for notification-related UI actions.
    """

    def __init__(self) -> None:
        self.notification_service = NotificationService()

    def create_notification(
        self,
        work_order_id: int,
        customer_id: int,
        channel: str,
        message_body: str,
        subject: Optional[str] = None,
        sent_to: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Create a notification.
        """
        logger.info(
            "Creating notification for work_order_id=%s channel=%s",
            work_order_id,
            channel,
        )

        return self.notification_service.create_notification(
            work_order_id=work_order_id,
            customer_id=customer_id,
            channel=channel,
            message_body=message_body,
            subject=subject,
            sent_to=sent_to,
        )

    def get_notification(self, notification_id: int) -> ServiceResponse:
        """
        Get full notification details (on click).
        """
        logger.debug("Fetching notification id=%s", notification_id)

        return self.notification_service.get_notification(notification_id)

    def get_all_notifications(self) -> ServiceResponse:
        """
        Get notification list for UI.
        """
        logger.debug("Fetching all notifications")

        return self.notification_service.get_all_notifications()

    def get_notifications_by_work_order(
        self,
        work_order_id: int,
    ) -> ServiceResponse:
        """
        Get notifications linked to a work order.
        """
        logger.debug(
            "Fetching notifications for work_order_id=%s",
            work_order_id,
        )

        return self.notification_service.get_notifications_by_work_order(
            work_order_id
        )

    def get_notifications_by_customer(
        self,
        customer_id: int,
    ) -> ServiceResponse:
        """
        Get notifications linked to a customer.
        """
        logger.debug(
            "Fetching notifications for customer_id=%s",
            customer_id,
        )

        return self.notification_service.get_notifications_by_customer(
            customer_id
        )

    def update_delivery_status(
        self,
        notification_id: int,
        delivery_status: str,
        provider_status: Optional[str] = None,
        error_message: Optional[str] = None,
        external_reference: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Update notification delivery status.
        """
        logger.info(
            "Updating notification status id=%s -> %s",
            notification_id,
            delivery_status,
        )

        return self.notification_service.update_delivery_status(
            notification_id=notification_id,
            delivery_status=delivery_status,
            provider_status=provider_status,
            error_message=error_message,
            external_reference=external_reference,
        )

    def get_failed_notifications(self) -> ServiceResponse:
        """
        Retrieve failed notifications.
        """
        logger.debug("Fetching failed notifications")

        return self.notification_service.get_failed_notifications()