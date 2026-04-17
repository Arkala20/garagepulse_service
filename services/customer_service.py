"""
services/customer_service.py

Customer service for GaragePulse.
Supports create, update, and broad customer search.
"""

from __future__ import annotations

import logging
from typing import Optional

from repositories.customer_repository import CustomerRepository
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.response import ServiceResponse
from utils.validators import Validators


logger = logging.getLogger(__name__)


class CustomerService:
    """
    Business logic for customer management.
    """

    def __init__(self) -> None:
        self.customer_repo = CustomerRepository()

    def create_customer(
        self,
        full_name: str,
        phone: str,
        email: Optional[str] = None,
        address_line_1: Optional[str] = None,
        address_line_2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            full_name = (full_name or "").strip()
            phone = (phone or "").strip()
            email = (email or "").strip().lower() if email else None
            address_line_1 = (address_line_1 or "").strip() or None
            address_line_2 = (address_line_2 or "").strip() or None
            city = (city or "").strip() or None
            state = (state or "").strip() or None
            postal_code = (postal_code or "").strip() or None
            notes = (notes or "").strip() or None

            Validators.require(full_name, "Full name")
            Validators.validate_phone(phone)

            if email:
                Validators.validate_email(email)

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None

            customer_id = self.customer_repo.create_customer(
                {
                    "full_name": full_name,
                    "phone": phone,
                    "email": email,
                    "address_line_1": address_line_1,
                    "address_line_2": address_line_2,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                    "notes": notes,
                    "is_active": 1,
                    "created_by": actor_id,
                    "updated_by": actor_id,
                }
            )

            logger.info("Customer created successfully: id=%s", customer_id)

            return ServiceResponse.success_response(
                message="Customer created successfully.",
                data={"customer_id": customer_id},
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to create customer: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def update_customer(
        self,
        customer_id: int,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address_line_1: Optional[str] = None,
        address_line_2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            existing = self.customer_repo.get_by_id(customer_id)
            if not existing or not existing.get("is_active"):
                return ServiceResponse.error_response(message="Customer not found.")

            update_data = {}

            if full_name is not None:
                full_name = full_name.strip()
                Validators.require(full_name, "Full name")
                update_data["full_name"] = full_name

            if phone is not None:
                phone = phone.strip()
                Validators.validate_phone(phone)
                update_data["phone"] = phone

            if email is not None:
                email = email.strip().lower()
                if email:
                    Validators.validate_email(email)
                    update_data["email"] = email
                else:
                    update_data["email"] = None

            if address_line_1 is not None:
                update_data["address_line_1"] = address_line_1.strip() or None

            if address_line_2 is not None:
                update_data["address_line_2"] = address_line_2.strip() or None

            if city is not None:
                update_data["city"] = city.strip() or None

            if state is not None:
                update_data["state"] = state.strip() or None

            if postal_code is not None:
                update_data["postal_code"] = postal_code.strip() or None

            if notes is not None:
                update_data["notes"] = notes.strip() or None

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            update_data["updated_by"] = actor_id

            if len(update_data) == 1 and "updated_by" in update_data:
                return ServiceResponse.error_response(message="No fields to update.")

            self.customer_repo.update_customer(customer_id, update_data)

            logger.info("Customer updated successfully: id=%s", customer_id)

            return ServiceResponse.success_response(
                message="Customer updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update customer: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def search_customers(self, search_text: str) -> ServiceResponse:
        """
        Search by any visible customer detail.
        """
        try:
            SessionService.require_authentication()

            search_text = (search_text or "").strip()
            if not search_text:
                customers = self.customer_repo.get_all_customers()
            else:
                customers = self.customer_repo.search_customers(search_text)

            return ServiceResponse.success_response(
                message="Customers retrieved successfully.",
                data=customers,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to search customers: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def search_by_phone(self, phone_fragment: str) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            phone_fragment = (phone_fragment or "").strip()
            if not phone_fragment:
                return ServiceResponse.error_response(
                    message="Enter phone number to search."
                )

            results = self.customer_repo.search_by_phone(phone_fragment)

            return ServiceResponse.success_response(
                message="Customers retrieved successfully.",
                data=results,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to search customers by phone: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_customer(self, customer_id: int) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(message="Customer not found.")

            return ServiceResponse.success_response(
                message="Customer retrieved successfully.",
                data=customer,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve customer: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_all_customers(self) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            customers = self.customer_repo.get_all_customers()

            return ServiceResponse.success_response(
                message="Customers retrieved successfully.",
                data=customers,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to fetch customers: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def deactivate_customer(self, customer_id: int) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            existing = self.customer_repo.get_by_id(customer_id)
            if not existing or not existing.get("is_active"):
                return ServiceResponse.error_response(message="Customer not found.")

            self.customer_repo.deactivate_customer(customer_id)

            logger.info("Customer deactivated successfully: id=%s", customer_id)

            return ServiceResponse.success_response(
                message="Customer deactivated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to deactivate customer: %s", exc)
            return ServiceResponse.error_response(message=str(exc))