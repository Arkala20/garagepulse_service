"""
services/invoice_service.py

Invoice service for GaragePulse.
Handles invoice generation from work orders, totals calculation,
payment status updates, and saved payment method retrieval.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from config.constants import PaymentStatus
from repositories.invoice_item_repository import InvoiceItemRepository
from repositories.invoice_repository import InvoiceRepository
from repositories.saved_payment_method_repository import SavedPaymentMethodRepository
from repositories.work_order_part_repository import WorkOrderPartRepository
from repositories.work_order_repository import WorkOrderRepository
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.id_generator import IDGenerator
from utils.response import ServiceResponse
from utils.validators import Validators


logger = logging.getLogger(__name__)


class InvoiceService:
    """
    Business logic for invoice operations.
    """

    def __init__(self) -> None:
        self.invoice_repo = InvoiceRepository()
        self.invoice_item_repo = InvoiceItemRepository()
        self.work_order_repo = WorkOrderRepository()
        self.work_order_part_repo = WorkOrderPartRepository()
        self.saved_payment_method_repo = SavedPaymentMethodRepository()

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
        try:
            SessionService.require_authentication()

            Validators.validate_positive_number(tax_rate, "Tax rate")
            Validators.validate_positive_number(discount_amount, "Discount amount")

            work_order = self.work_order_repo.get_by_id_with_details(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(
                    message="Work order not found."
                )

            existing_invoice = self.invoice_repo.get_by_work_order_id(work_order_id)
            if existing_invoice:
                return ServiceResponse.error_response(
                    message="An invoice already exists for this work order."
                )

            labor_total = float(work_order.get("labor_cost") or 0.0)
            parts = self.work_order_part_repo.get_billable_parts(work_order_id)
            parts_total = float(
                self.work_order_part_repo.calculate_parts_total(work_order_id)
            )

            subtotal = labor_total + parts_total
            tax_amount = (subtotal * float(tax_rate)) / 100
            grand_total = subtotal + tax_amount - float(discount_amount)

            if grand_total < 0:
                return ServiceResponse.error_response(
                    message="Grand total cannot be negative."
                )

            next_sequence = len(
                self.invoice_repo.get_all_invoices(limit=100000, offset=0)
            ) + 1
            invoice_number = IDGenerator.generate_invoice_number(next_sequence)

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None

            invoice_id = self.invoice_repo.create_invoice(
                {
                    "invoice_number": invoice_number,
                    "work_order_id": work_order_id,
                    "customer_id": work_order["customer_id"],
                    "invoice_date": date.today(),
                    "due_date": due_date,
                    "labor_total": labor_total,
                    "parts_total": parts_total,
                    "subtotal": subtotal,
                    "tax_rate": float(tax_rate),
                    "tax_amount": tax_amount,
                    "discount_amount": float(discount_amount),
                    "grand_total": grand_total,
                    "payment_status": PaymentStatus.PENDING,
                    "payment_method_summary": None,
                    "notes": (notes or "").strip() or None,
                    "created_by": actor_id,
                    "updated_by": actor_id,
                }
            )

            item_rows = []

            if labor_total > 0:
                item_rows.append(
                    {
                        "invoice_id": invoice_id,
                        "item_type": "LABOR",
                        "description": f"Labor for {work_order['work_order_id']}",
                        "quantity": 1,
                        "unit_price": labor_total,
                        "line_total": labor_total,
                        "source_reference": work_order["work_order_id"],
                    }
                )

            for part in parts:
                item_rows.append(
                    {
                        "invoice_id": invoice_id,
                        "item_type": "PART",
                        "description": part["part_name"],
                        "quantity": part["quantity"],
                        "unit_price": part["unit_price"],
                        "line_total": part["line_total"],
                        "source_reference": str(part["id"]),
                    }
                )

            if item_rows:
                self.invoice_item_repo.create_items_bulk(item_rows)

            logger.info(
                "Invoice generated successfully: invoice_id=%s, invoice_number=%s",
                invoice_id,
                invoice_number,
            )

            return ServiceResponse.success_response(
                message="Invoice generated successfully.",
                data={
                    "invoice_id": invoice_id,
                    "invoice_number": invoice_number,
                    "grand_total": grand_total,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to generate invoice: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_invoice(self, invoice_number: str) -> ServiceResponse:
        """
        Retrieve invoice with its line items.
        """
        try:
            SessionService.require_authentication()

            invoice = self.invoice_repo.get_by_invoice_number(invoice_number)
            if not invoice:
                return ServiceResponse.error_response(
                    message="Invoice not found."
                )

            items = self.invoice_item_repo.get_by_invoice_id(invoice["id"])

            return ServiceResponse.success_response(
                message="Invoice retrieved successfully.",
                data={
                    "invoice": invoice,
                    "items": items,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve invoice: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_all_invoices(self) -> ServiceResponse:
        """
        Retrieve all invoices.
        """
        try:
            SessionService.require_authentication()

            invoices = self.invoice_repo.get_all_invoices()

            return ServiceResponse.success_response(
                message="Invoices retrieved successfully.",
                data=invoices,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve invoices: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def mark_invoice_paid(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Mark an invoice as paid.
        """
        try:
            SessionService.require_authentication()

            invoice = self.invoice_repo.get_by_id(invoice_id)
            if not invoice:
                return ServiceResponse.error_response(
                    message="Invoice not found."
                )

            self.invoice_repo.update_payment_status(
                invoice_id=invoice_id,
                payment_status=PaymentStatus.PAID,
                payment_method_summary=payment_method_summary,
            )

            logger.info("Invoice marked paid: invoice_id=%s", invoice_id)

            return ServiceResponse.success_response(
                message="Invoice marked as paid successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to mark invoice paid: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def mark_invoice_partial(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Mark an invoice as partially paid.
        """
        try:
            SessionService.require_authentication()

            invoice = self.invoice_repo.get_by_id(invoice_id)
            if not invoice:
                return ServiceResponse.error_response(
                    message="Invoice not found."
                )

            self.invoice_repo.update_payment_status(
                invoice_id=invoice_id,
                payment_status=PaymentStatus.PARTIAL,
                payment_method_summary=payment_method_summary,
            )

            return ServiceResponse.success_response(
                message="Invoice marked as partial successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to mark invoice partial: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_saved_payment_methods(self, customer_id: int) -> ServiceResponse:
        """
        Get saved payment methods for a customer.
        """
        try:
            SessionService.require_authentication()

            methods = self.saved_payment_method_repo.get_by_customer_id(customer_id)

            return ServiceResponse.success_response(
                message="Saved payment methods retrieved successfully.",
                data=methods,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve payment methods: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def set_default_payment_method(
        self,
        customer_id: int,
        method_id: int,
    ) -> ServiceResponse:
        """
        Set a saved payment method as default.
        """
        try:
            SessionService.require_authentication()

            method = self.saved_payment_method_repo.get_by_id(method_id)
            if not method:
                return ServiceResponse.error_response(
                    message="Saved payment method not found."
                )

            if method["customer_id"] != customer_id:
                return ServiceResponse.error_response(
                    message="Payment method does not belong to the given customer."
                )

            self.saved_payment_method_repo.set_default_method(method_id, customer_id)

            return ServiceResponse.success_response(
                message="Default payment method updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to set default payment method: %s", exc)
            return ServiceResponse.error_response(message=str(exc))