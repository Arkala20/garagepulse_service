"""
services/notification_service.py

Notification service for GaragePulse.
Handles notification creation, retrieval, delivery status updates,
and real email sending for EMAIL channel notifications.

Professor alignment:
- Notification list should show customer name
- Clicking a notification should open full details
- Supports email/SMS delivery status tracking
"""

from __future__ import annotations

import logging
from typing import Optional

from config.constants import (
    NOTIFICATION_CHANNEL_LIST,
    NOTIFICATION_DELIVERY_STATUS_LIST,
)
from repositories.customer_repository import CustomerRepository
from repositories.notification_repository import NotificationRepository
from repositories.work_order_repository import WorkOrderRepository
from services.email_service import EmailService
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.response import ServiceResponse
from utils.validators import Validators


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Business logic for notification operations.
    """

    def __init__(self) -> None:
        self.notification_repo = NotificationRepository()
        self.customer_repo = CustomerRepository()
        self.work_order_repo = WorkOrderRepository()
        self.email_service = EmailService()

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
        Create a notification record linked to a work order and customer.

        For EMAIL channel:
        - tries to send real email immediately
        - stores delivery result as SENT or FAILED

        For SMS channel:
        - currently stores record only
        - real SMS provider integration can be added later
        """
        try:
            SessionService.require_authentication()

            channel = (channel or "").strip().upper()
            subject = (subject or "").strip() or None
            message_body = (message_body or "").strip()
            sent_to = (sent_to or "").strip() or None

            Validators.require(message_body, "Message body")

            if channel not in NOTIFICATION_CHANNEL_LIST:
                return ServiceResponse.error_response(
                    message="Invalid notification channel."
                )

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(
                    message="Customer not found."
                )

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(
                    message="Work order not found."
                )

            if work_order["customer_id"] != customer_id:
                return ServiceResponse.error_response(
                    message="Selected work order does not belong to the selected customer."
                )

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None

            customer_email = customer.get("email")
            delivery_status = "PENDING"
            provider_status = None
            error_message = None
            external_reference = None

            # Determine recipient if not manually passed
            if not sent_to and channel == "EMAIL":
                sent_to = customer_email

            # Real email sending
            if channel == "EMAIL":
                if not customer_email:
                    delivery_status = "FAILED"
                    error_message = "Customer does not have an email address."
                else:
                    email_response = self.email_service.send_email(
                        to_email=customer_email,
                        subject=subject or "GaragePulse Notification",
                        body=message_body,
                    )

                    if email_response.success:
                        delivery_status = "SENT"
                        provider_status = "SMTP_SUCCESS"
                    else:
                        delivery_status = "FAILED"
                        provider_status = "SMTP_FAILED"
                        error_message = email_response.message

            # SMS placeholder
            elif channel == "SMS":
                delivery_status = "PENDING"
                provider_status = "SMS_PROVIDER_NOT_CONFIGURED"

            notification_id = self.notification_repo.create_notification(
                {
                    "work_order_id": work_order_id,
                    "customer_id": customer_id,
                    "channel": channel,
                    "subject": subject,
                    "message_body": message_body,
                    "delivery_status": delivery_status,
                    "provider_status": provider_status,
                    "error_message": error_message,
                    "external_reference": external_reference,
                    "sent_to": sent_to,
                    "created_by": actor_id,
                }
            )

            logger.info(
                "Notification created: id=%s, work_order_id=%s, channel=%s, status=%s",
                notification_id,
                work_order_id,
                channel,
                delivery_status,
            )

            if channel == "EMAIL":
                if delivery_status == "SENT":
                    message = "Notification created and email sent successfully."
                else:
                    message = f"Notification created, but email sending failed: {error_message}"
            elif channel == "SMS":
                message = (
                    "Notification record created successfully. "
                    "Real SMS sending is not configured yet."
                )
            else:
                message = "Notification created successfully."

            return ServiceResponse.success_response(
                message=message,
                data={
                    "notification_id": notification_id,
                    "delivery_status": delivery_status,
                    "provider_status": provider_status,
                    "error_message": error_message,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to create notification: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_notification(self, notification_id: int) -> ServiceResponse:
        """
        Get a single notification with full details.
        Used when a user clicks a notification in the UI.
        """
        try:
            SessionService.require_authentication()

            notification = self.notification_repo.get_by_id_with_details(notification_id)
            if not notification:
                return ServiceResponse.error_response(
                    message="Notification not found."
                )

            return ServiceResponse.success_response(
                message="Notification retrieved successfully.",
                data=notification,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve notification: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_all_notifications(self) -> ServiceResponse:
        """
        Get notification list for UI.
        """
        try:
            SessionService.require_authentication()

            notifications = self.notification_repo.get_all_notifications()

            return ServiceResponse.success_response(
                message="Notifications retrieved successfully.",
                data=notifications,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve notifications: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_notifications_by_work_order(self, work_order_id: int) -> ServiceResponse:
        """
        Get all notifications linked to a work order.
        """
        try:
            SessionService.require_authentication()

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(
                    message="Work order not found."
                )

            notifications = self.notification_repo.get_by_work_order_id(work_order_id)

            return ServiceResponse.success_response(
                message="Work order notifications retrieved successfully.",
                data=notifications,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve work order notifications: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_notifications_by_customer(self, customer_id: int) -> ServiceResponse:
        """
        Get all notifications linked to a customer.
        """
        try:
            SessionService.require_authentication()

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(
                    message="Customer not found."
                )

            notifications = self.notification_repo.get_by_customer_id(customer_id)

            return ServiceResponse.success_response(
                message="Customer notifications retrieved successfully.",
                data=notifications,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve customer notifications: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def update_delivery_status(
        self,
        notification_id: int,
        delivery_status: str,
        provider_status: Optional[str] = None,
        error_message: Optional[str] = None,
        external_reference: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Update notification delivery status and provider response details.
        """
        try:
            SessionService.require_authentication()

            delivery_status = (delivery_status or "").strip().upper()
            provider_status = (provider_status or "").strip() or None
            error_message = (error_message or "").strip() or None
            external_reference = (external_reference or "").strip() or None

            if delivery_status not in NOTIFICATION_DELIVERY_STATUS_LIST:
                return ServiceResponse.error_response(
                    message="Invalid delivery status."
                )

            existing = self.notification_repo.get_by_id(notification_id)
            if not existing:
                return ServiceResponse.error_response(
                    message="Notification not found."
                )

            self.notification_repo.update_delivery_status(
                notification_id=notification_id,
                delivery_status=delivery_status,
                provider_status=provider_status,
                error_message=error_message,
                external_reference=external_reference,
            )

            logger.info(
                "Notification delivery status updated: id=%s, status=%s",
                notification_id,
                delivery_status,
            )

            return ServiceResponse.success_response(
                message="Notification delivery status updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update notification delivery status: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_failed_notifications(self) -> ServiceResponse:
        """
        Get all failed notifications.
        """
        try:
            SessionService.require_authentication()

            notifications = self.notification_repo.get_by_delivery_status("FAILED")

            return ServiceResponse.success_response(
                message="Failed notifications retrieved successfully.",
                data=notifications,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve failed notifications: %s", exc)
            return ServiceResponse.error_response(message=str(exc))