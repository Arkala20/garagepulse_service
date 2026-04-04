"""
controllers/invoice_controller.py

Invoice controller for GaragePulse.
Bridges UI with InvoiceService for invoice generation,
retrieval, payment status updates, and saved payment methods.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.invoice_service import InvoiceService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class InvoiceController:
    """
    Controller for invoice-related UI actions.
    """

    def __init__(self) -> None:
        self.invoice_service = InvoiceService()

    def generate_invoice_from_work_order(
        self,
        work_order_id: int,
        tax_rate: float = 0.0,
        discount_amount: float = 0.0,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Generate an invoice from a work order.
        """
        logger.info(
            "Generating invoice from work_order_id=%s",
            work_order_id,
        )

        return self.invoice_service.generate_invoice_from_work_order(
            work_order_id=work_order_id,
            tax_rate=tax_rate,
            discount_amount=discount_amount,
            due_date=due_date,
            notes=notes,
        )

    def get_invoice(self, invoice_number: str) -> ServiceResponse:
        """
        Retrieve invoice with items.
        """
        logger.debug("Fetching invoice number=%s", invoice_number)

        return self.invoice_service.get_invoice(invoice_number)

    def get_all_invoices(self) -> ServiceResponse:
        """
        Retrieve all invoices.
        """
        logger.debug("Fetching all invoices")

        return self.invoice_service.get_all_invoices()

    def mark_invoice_paid(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Mark an invoice as paid.
        """
        logger.info("Marking invoice as paid id=%s", invoice_id)

        return self.invoice_service.mark_invoice_paid(
            invoice_id=invoice_id,
            payment_method_summary=payment_method_summary,
        )

    def mark_invoice_partial(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Mark invoice as partially paid.
        """
        logger.info("Marking invoice as partial id=%s", invoice_id)

        return self.invoice_service.mark_invoice_partial(
            invoice_id=invoice_id,
            payment_method_summary=payment_method_summary,
        )

    def get_saved_payment_methods(
        self,
        customer_id: int,
    ) -> ServiceResponse:
        """
        Retrieve saved payment methods for a customer.
        """
        logger.debug("Fetching saved payment methods for customer=%s", customer_id)

        return self.invoice_service.get_saved_payment_methods(customer_id)

    def set_default_payment_method(
        self,
        customer_id: int,
        method_id: int,
    ) -> ServiceResponse:
        """
        Set default saved payment method.
        """
        logger.info(
            "Setting default payment method id=%s for customer=%s",
            method_id,
            customer_id,
        )

        return self.invoice_service.set_default_payment_method(
            customer_id=customer_id,
            method_id=method_id,
        )