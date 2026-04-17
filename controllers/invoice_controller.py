"""
controllers/invoice_controller.py

Invoice controller for GaragePulse.
Bridges UI with InvoiceService for invoice generation,
retrieval, payment status updates, saved payment methods,
and invoice PDF generation.
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

    # ------------------------------------------------------------------
    # Generate invoice
    # ------------------------------------------------------------------
    def generate_invoice_from_work_order(
        self,
        work_order_id: int,
        tax_rate: float = 0.0,
        discount_amount: float = 0.0,
        invoice_number: Optional[str] = None,
        payment_method_summary: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        logger.info("Generating invoice from work_order_id=%s", work_order_id)
        return self.invoice_service.generate_invoice_from_work_order(
            work_order_id=work_order_id,
            tax_rate=tax_rate,
            discount_amount=discount_amount,
            invoice_number=invoice_number,
            payment_method_summary=payment_method_summary,
            due_date=due_date,
            notes=notes,
        )

    def generate_invoice(
        self,
        work_order_id: int,
        tax_rate: float = 0.0,
        discount_amount: float = 0.0,
        invoice_number: Optional[str] = None,
        payment_method_summary: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        logger.info("Generating invoice from UI for work_order_id=%s", work_order_id)
        return self.invoice_service.generate_invoice_from_work_order(
            work_order_id=work_order_id,
            tax_rate=tax_rate,
            discount_amount=discount_amount,
            invoice_number=invoice_number,
            payment_method_summary=payment_method_summary,
            due_date=due_date,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Retrieve invoice(s)
    # ------------------------------------------------------------------
    def get_invoice(self, invoice_number: str) -> ServiceResponse:
        logger.debug("Fetching invoice number=%s", invoice_number)
        return self.invoice_service.get_invoice(invoice_number)

    def get_invoice_by_number(self, invoice_number: str) -> ServiceResponse:
        logger.debug("Fetching invoice by number=%s", invoice_number)
        return self.invoice_service.get_invoice(invoice_number)

    def get_by_invoice_number(self, invoice_number: str) -> ServiceResponse:
        logger.debug("Fetching invoice by number=%s", invoice_number)
        return self.invoice_service.get_invoice(invoice_number)

    def get_all_invoices(self) -> ServiceResponse:
        logger.debug("Fetching all invoices")
        return self.invoice_service.get_all_invoices()

    # ------------------------------------------------------------------
    # Payment status updates
    # ------------------------------------------------------------------
    def mark_invoice_paid(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        logger.info("Marking invoice as paid id=%s", invoice_id)
        return self.invoice_service.mark_invoice_paid(
            invoice_id=invoice_id,
            payment_method_summary=payment_method_summary,
        )

    def mark_paid(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        logger.info("Marking invoice as paid id=%s", invoice_id)
        return self.invoice_service.mark_invoice_paid(
            invoice_id=invoice_id,
            payment_method_summary=payment_method_summary,
        )

    def mark_invoice_partial(
        self,
        invoice_id: int,
        paid_amount: Optional[float] = None,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        logger.info(
            "Marking invoice as partial id=%s, paid_amount=%s",
            invoice_id,
            paid_amount,
        )
        return self.invoice_service.mark_invoice_partial(
            invoice_id=invoice_id,
            paid_amount=paid_amount,
            payment_method_summary=payment_method_summary,
        )

    def mark_partial(
        self,
        invoice_id: int,
        paid_amount: Optional[float] = None,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        logger.info(
            "Marking invoice as partial id=%s, paid_amount=%s",
            invoice_id,
            paid_amount,
        )
        return self.invoice_service.mark_invoice_partial(
            invoice_id=invoice_id,
            paid_amount=paid_amount,
            payment_method_summary=payment_method_summary,
        )

    def update_payment_status(
        self,
        invoice_id: int,
        payment_status: str,
        paid_amount: Optional[float] = None,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        status = (payment_status or "").strip().upper()

        if status == "PAID":
            return self.mark_invoice_paid(
                invoice_id=invoice_id,
                payment_method_summary=payment_method_summary,
            )

        if status == "PARTIAL":
            return self.mark_partial(
                invoice_id=invoice_id,
                paid_amount=paid_amount,
                payment_method_summary=payment_method_summary,
            )

        logger.warning("Unsupported payment status update requested: %s", status)
        return ServiceResponse.error_response(
            message=f"Unsupported payment status: {payment_status}"
        )

    # ------------------------------------------------------------------
    # Saved payment methods
    # ------------------------------------------------------------------
    def get_saved_payment_methods(
        self,
        customer_id: int,
    ) -> ServiceResponse:
        logger.debug("Fetching saved payment methods for customer=%s", customer_id)
        return self.invoice_service.get_saved_payment_methods(customer_id)

    def set_default_payment_method(
        self,
        customer_id: int,
        method_id: int,
    ) -> ServiceResponse:
        logger.info(
            "Setting default payment method id=%s for customer=%s",
            method_id,
            customer_id,
        )
        return self.invoice_service.set_default_payment_method(
            customer_id=customer_id,
            method_id=method_id,
        )

    # ------------------------------------------------------------------
    # PDF generation
    # ------------------------------------------------------------------
    def generate_invoice_pdf(self, invoice_id: int) -> ServiceResponse:
        logger.info("Generating invoice PDF for invoice_id=%s", invoice_id)
        return self.invoice_service.generate_invoice_pdf(invoice_id)

    def download_invoice_pdf(self, invoice_id: int) -> ServiceResponse:
        logger.info("Downloading invoice PDF for invoice_id=%s", invoice_id)
        return self.invoice_service.generate_invoice_pdf(invoice_id)