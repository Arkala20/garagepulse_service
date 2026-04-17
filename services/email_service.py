"""
services/email_service.py

SMTP email service for GaragePulse.
Sends real emails using application settings.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from config.settings import settings
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class EmailService:
    """
    SMTP-based email sending service.
    """

    def __init__(self) -> None:
        self.smtp_host = getattr(settings, "SMTP_HOST", "")
        self.smtp_port = int(getattr(settings, "SMTP_PORT", 587) or 587)
        self.smtp_username = getattr(settings, "SMTP_USERNAME", "")
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", "")
        self.smtp_use_tls = bool(getattr(settings, "SMTP_USE_TLS", True))
        self.smtp_use_ssl = bool(getattr(settings, "SMTP_USE_SSL", False))
        self.smtp_from_email = getattr(settings, "SMTP_FROM_EMAIL", "")
        self.smtp_from_name = getattr(settings, "SMTP_FROM_NAME", "GaragePulse")

    def _validate_configuration(self) -> ServiceResponse | None:
        if not self.smtp_host:
            return ServiceResponse.error_response(
                message="SMTP configuration error: SMTP_HOST is missing."
            )

        if not self.smtp_port:
            return ServiceResponse.error_response(
                message="SMTP configuration error: SMTP_PORT is missing."
            )

        if not self.smtp_username:
            return ServiceResponse.error_response(
                message="SMTP configuration error: SMTP_USERNAME is missing."
            )

        if not self.smtp_password:
            return ServiceResponse.error_response(
                message="SMTP configuration error: SMTP_PASSWORD is missing."
            )

        if not self.smtp_from_email:
            return ServiceResponse.error_response(
                message="SMTP configuration error: SMTP_FROM_EMAIL is missing."
            )

        return None

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> ServiceResponse:
        """
        Send an email using SMTP.
        """
        try:
            config_error = self._validate_configuration()
            if config_error:
                return config_error

            to_email = (to_email or "").strip()
            subject = (subject or "").strip()
            body = (body or "").strip()

            if not to_email:
                return ServiceResponse.error_response(message="Recipient email is required.")

            if not subject:
                return ServiceResponse.error_response(message="Email subject is required.")

            if not body:
                return ServiceResponse.error_response(message="Email body is required.")

            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            message["To"] = to_email
            message.set_content(body)

            if self.smtp_use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    host=self.smtp_host,
                    port=self.smtp_port,
                    context=context,
                    timeout=30,
                ) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(
                    host=self.smtp_host,
                    port=self.smtp_port,
                    timeout=30,
                ) as server:
                    server.ehlo()

                    if self.smtp_use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()

                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message)

            logger.info("Email sent successfully to %s", to_email)
            return ServiceResponse.success_response(
                message="Email sent successfully."
            )

        except smtplib.SMTPAuthenticationError:
            logger.exception("SMTP authentication failed.")
            return ServiceResponse.error_response(
                message="Failed to send email: SMTP authentication failed."
            )
        except smtplib.SMTPException as exc:
            logger.exception("SMTP error: %s", exc)
            return ServiceResponse.error_response(
                message=f"Failed to send email: {exc}"
            )
        except Exception as exc:
            logger.exception("Unexpected email send error: %s", exc)
            return ServiceResponse.error_response(
                message=f"Failed to send email: {exc}"
            )