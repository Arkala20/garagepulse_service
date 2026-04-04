"""
services/email_service.py

SMTP email sending service for GaragePulse.

Recommended .env values:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_USE_TLS=True
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from config.settings import settings
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class EmailService:
    """
    SMTP email sending service.
    """

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> ServiceResponse:
        """
        Send an email using SMTP configuration from settings.
        """
        try:
            if not settings.SMTP_HOST:
                return ServiceResponse.error_response(
                    message="SMTP host is not configured."
                )

            if not settings.SMTP_PORT:
                return ServiceResponse.error_response(
                    message="SMTP port is not configured."
                )

            if not settings.SMTP_USERNAME:
                return ServiceResponse.error_response(
                    message="SMTP username is not configured."
                )

            if not settings.SMTP_PASSWORD:
                return ServiceResponse.error_response(
                    message="SMTP password is not configured."
                )

            if not settings.SMTP_FROM_EMAIL:
                return ServiceResponse.error_response(
                    message="SMTP from email is not configured."
                )

            if not to_email:
                return ServiceResponse.error_response(
                    message="Recipient email is required."
                )

            message = EmailMessage()
            message["From"] = settings.SMTP_FROM_EMAIL
            message["To"] = to_email
            message["Subject"] = subject or "GaragePulse Notification"
            message.set_content(body or "")

            with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT)) as server:
                server.ehlo()

                if str(settings.SMTP_USE_TLS).lower() == "true":
                    server.starttls()
                    server.ehlo()

                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(message)

            logger.info("Email sent successfully to %s", to_email)

            return ServiceResponse.success_response(
                message="Email sent successfully."
            )

        except Exception as exc:
            logger.exception("Email sending failed: %s", exc)
            return ServiceResponse.error_response(
                message=f"Failed to send email: {str(exc)}"
            )