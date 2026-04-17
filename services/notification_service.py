"""
services/notification_service.py

Notification service for GaragePulse.
Email-only real-time notification sending.
"""

from __future__ import annotations

import logging
from typing import Optional

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
        try:
            SessionService.require_authentication()

            message_body = (message_body or "").strip()
            subject = (subject or "").strip() or None
            sent_to = (sent_to or "").strip() or None

            Validators.require(message_body, "Message body")

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(message="Customer not found.")

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            if int(work_order["customer_id"]) != int(customer_id):
                return ServiceResponse.error_response(
                    message="Selected work order does not belong to the selected customer."
                )

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None

            customer_email = sent_to or (customer.get("email") or "").strip()

            delivery_status = "PENDING"
            provider_status = None
            error_message = None

            if not customer_email:
                delivery_status = "FAILED"
                provider_status = "EMAIL_NOT_FOUND"
                error_message = "Customer does not have an email address."
            else:
                send_response = self.email_service.send_email(
                    to_email=customer_email,
                    subject=subject or "GaragePulse Notification",
                    body=message_body,
                )

                if send_response.success:
                    delivery_status = "SENT"
                    provider_status = "SMTP_SUCCESS"
                else:
                    delivery_status = "FAILED"
                    provider_status = "SMTP_FAILED"
                    error_message = send_response.message

            notification_id = self.notification_repo.create_notification(
                {
                    "work_order_id": work_order_id,
                    "customer_id": customer_id,
                    "channel": "EMAIL",
                    "subject": subject,
                    "message_body": message_body,
                    "delivery_status": delivery_status,
                    "provider_status": provider_status,
                    "error_message": error_message,
                    "external_reference": None,
                    "sent_to": customer_email,
                    "created_by": actor_id,
                }
            )

            logger.info(
                "Notification created: id=%s, status=%s",
                notification_id,
                delivery_status,
            )

            if delivery_status == "SENT":
                msg = "Email sent successfully."
            else:
                msg = f"Notification created, but email sending failed: {error_message}"

            return ServiceResponse.success_response(
                message=msg,
                data={
                    "notification_id": notification_id,
                    "delivery_status": delivery_status,
                    "provider_status": provider_status,
                    "error_message": error_message,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to create notification: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_notification(self, notification_id: int) -> ServiceResponse:
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
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve notification: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_all_notifications(self) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            notifications = self.notification_repo.get_all_notifications()

            return ServiceResponse.success_response(
                message="Notifications retrieved successfully.",
                data=notifications,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve notifications: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def update_delivery_status(
        self,
        notification_id: int,
        delivery_status: str,
        provider_status: Optional[str] = None,
        error_message: Optional[str] = None,
        external_reference: Optional[str] = None,
    ) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            existing = self.notification_repo.get_by_id(notification_id)
            if not existing:
                return ServiceResponse.error_response(message="Notification not found.")

            self.notification_repo.update_delivery_status(
                notification_id=notification_id,
                delivery_status=delivery_status,
                provider_status=provider_status,
                error_message=error_message,
                external_reference=external_reference,
            )

            return ServiceResponse.success_response(
                message="Notification delivery status updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update delivery status: %s", exc)
            return ServiceResponse.error_response(message=str(exc))