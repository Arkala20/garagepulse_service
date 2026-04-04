"""
controllers/customer_controller.py

Customer controller for GaragePulse.
Acts as the bridge between UI and CustomerService.
Handles customer creation, updates, search, and retrieval.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.customer_service import CustomerService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class CustomerController:
    """
    Controller for customer-related UI actions.
    """

    def __init__(self) -> None:
        self.customer_service = CustomerService()

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
        """
        Create a new customer.
        """
        logger.info("Creating customer name=%s phone=%s", full_name, phone)

        return self.customer_service.create_customer(
            full_name=full_name,
            phone=phone,
            email=email,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            notes=notes,
        )

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
        """
        Update an existing customer.
        """
        logger.info("Updating customer id=%s", customer_id)

        return self.customer_service.update_customer(
            customer_id=customer_id,
            full_name=full_name,
            phone=phone,
            email=email,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            notes=notes,
        )

    def search_by_phone(self, phone_fragment: str) -> ServiceResponse:
        """
        Search customers by phone number.

        Professor requirement:
        Customers search by phone.
        """
        logger.debug("Searching customers by phone fragment=%s", phone_fragment)

        return self.customer_service.search_by_phone(phone_fragment)

    def get_customer(self, customer_id: int) -> ServiceResponse:
        """
        Retrieve a specific customer.
        """
        logger.debug("Fetching customer id=%s", customer_id)

        return self.customer_service.get_customer(customer_id)

    def get_all_customers(self) -> ServiceResponse:
        """
        Retrieve all active customers.
        """
        logger.debug("Fetching all customers")

        return self.customer_service.get_all_customers()

    def deactivate_customer(self, customer_id: int) -> ServiceResponse:
        """
        Deactivate a customer record.
        """
        logger.info("Deactivating customer id=%s", customer_id)

        return self.customer_service.deactivate_customer(customer_id)