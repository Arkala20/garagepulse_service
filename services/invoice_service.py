"""
services/invoice_service.py

Invoice service for GaragePulse.
Handles invoice generation from work orders, totals calculation,
payment status updates, saved payment method retrieval,
and invoice PDF generation.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

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

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    def get_all_invoices(self) -> ServiceResponse:
        """
        Return all invoices for listing screens.
        """
        try:
            rows = self.invoice_repo.get_all_invoices(limit=100000, offset=0)
            return ServiceResponse.success_response(
                message="Invoices loaded successfully.",
                data=rows or [],
            )
        except Exception as exc:
            logger.exception("Failed to load invoices: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_invoice(self, invoice_number: str) -> ServiceResponse:
        """
        Get invoice by invoice number with line items.
        """
        try:
            if not invoice_number or not str(invoice_number).strip():
                return ServiceResponse.error_response(message="Invoice number is required.")

            invoice = self.invoice_repo.get_by_invoice_number(str(invoice_number).strip())
            if not invoice:
                return ServiceResponse.error_response(message="Invoice not found.")

            items = self.invoice_item_repo.get_by_invoice_id(invoice["id"]) or []
            invoice["items"] = items

            return ServiceResponse.success_response(
                message="Invoice loaded successfully.",
                data=invoice,
            )
        except Exception as exc:
            logger.exception("Failed to fetch invoice: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    # ------------------------------------------------------------------
    # CREATE / REFRESH
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
        """
        Generate OR refresh invoice from a work order.
        """
        try:
            SessionService.require_authentication()

            Validators.validate_positive_number(tax_rate, "Tax rate")
            Validators.validate_positive_number(discount_amount, "Discount amount")

            work_order = self.work_order_repo.get_by_id_with_details(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            existing_invoice = self.invoice_repo.get_by_work_order_id(work_order_id)

            labor_total = float(work_order.get("labor_cost") or 0.0)
            parts = self.work_order_part_repo.get_billable_parts(work_order_id) or []
            parts_total = float(
                self.work_order_part_repo.calculate_parts_total(work_order_id) or 0.0
            )

            subtotal = labor_total + parts_total
            tax_amount = (subtotal * float(tax_rate)) / 100
            grand_total = subtotal + tax_amount - float(discount_amount)

            if grand_total < 0:
                return ServiceResponse.error_response(message="Grand total cannot be negative.")

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None

            cleaned_invoice_number = (invoice_number or "").strip() or None
            cleaned_payment_method = (payment_method_summary or "").strip() or None
            cleaned_notes = (notes or "").strip() or None

            if existing_invoice:
                invoice_id = existing_invoice["id"]
                final_invoice_number = existing_invoice.get("invoice_number")

                self.invoice_repo.update_invoice_totals(
                    invoice_id=invoice_id,
                    labor_total=labor_total,
                    parts_total=parts_total,
                    subtotal=subtotal,
                    tax_rate=float(tax_rate),
                    tax_amount=tax_amount,
                    discount_amount=float(discount_amount),
                    grand_total=grand_total,
                    due_date=due_date,
                    notes=cleaned_notes,
                )

                update_payload = {
                    "payment_method_summary": cleaned_payment_method,
                    "updated_by": actor_id,
                }
                if cleaned_invoice_number:
                    update_payload["invoice_number"] = cleaned_invoice_number
                    final_invoice_number = cleaned_invoice_number

                self.invoice_repo.update(invoice_id, update_payload)
                self.invoice_item_repo.delete_by_invoice_id(invoice_id)

            else:
                if cleaned_invoice_number:
                    final_invoice_number = cleaned_invoice_number
                else:
                    next_sequence = len(
                        self.invoice_repo.get_all_invoices(limit=100000, offset=0)
                    ) + 1
                    final_invoice_number = IDGenerator.generate_invoice_number(next_sequence)

                invoice_id = self.invoice_repo.create_invoice(
                    {
                        "invoice_number": final_invoice_number,
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
                        "payment_method_summary": cleaned_payment_method,
                        "notes": cleaned_notes,
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
                        "description": "Labor Charges",
                        "quantity": 1,
                        "unit_price": labor_total,
                        "line_total": labor_total,
                        "source_reference": work_order["work_order_id"],
                    }
                )

            for part in parts:
                line_total = float(part.get("line_total") or 0)
                unit_price = float(part.get("unit_price") or 0)
                quantity = float(part.get("quantity") or 0)

                # Skip zero-value part rows to avoid odd invoice display
                if line_total <= 0 and unit_price <= 0:
                    continue

                item_rows.append(
                    {
                        "invoice_id": invoice_id,
                        "item_type": "PART",
                        "description": part["part_name"],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                        "source_reference": str(part["id"]),
                    }
                )

            if item_rows:
                self.invoice_item_repo.create_items_bulk(item_rows)

            return ServiceResponse.success_response(
                message="Invoice created/updated successfully.",
                data={
                    "invoice_id": invoice_id,
                    "invoice_number": final_invoice_number,
                    "grand_total": grand_total,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Auth failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to process invoice: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    # ------------------------------------------------------------------
    # PAYMENT STATUS
    # ------------------------------------------------------------------
    def mark_invoice_paid(
        self,
        invoice_id: int,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Mark invoice as paid.
        """
        try:
            SessionService.require_authentication()

            invoice = self.invoice_repo.get_by_id(invoice_id)
            if not invoice:
                return ServiceResponse.error_response(message="Invoice not found.")

            update_data = {
                "payment_status": PaymentStatus.PAID,
            }

            if payment_method_summary is not None:
                update_data["payment_method_summary"] = payment_method_summary

            self.invoice_repo.update(invoice_id, update_data)

            return ServiceResponse.success_response(message="Invoice marked as paid.")

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Auth failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to mark invoice paid: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def mark_invoice_partial(
        self,
        invoice_id: int,
        paid_amount: Optional[float] = None,
        payment_method_summary: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Mark invoice as partial.
        """
        try:
            SessionService.require_authentication()

            invoice = self.invoice_repo.get_by_id(invoice_id)
            if not invoice:
                return ServiceResponse.error_response(message="Invoice not found.")

            if paid_amount is not None:
                Validators.validate_positive_number(paid_amount, "Partial paid amount")

                grand_total = float(invoice.get("grand_total") or 0)
                if paid_amount <= 0:
                    return ServiceResponse.error_response(
                        message="Partial paid amount must be greater than zero."
                    )
                if paid_amount >= grand_total:
                    return ServiceResponse.error_response(
                        message="Partial paid amount must be less than grand total."
                    )

            update_data = {
                "payment_status": PaymentStatus.PARTIAL,
            }

            if payment_method_summary is not None:
                update_data["payment_method_summary"] = payment_method_summary

            self.invoice_repo.update(invoice_id, update_data)

            return ServiceResponse.success_response(message="Invoice marked as partial.")

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Auth failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to mark invoice partial: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    # ------------------------------------------------------------------
    # SAVED PAYMENT METHODS
    # ------------------------------------------------------------------
    def get_saved_payment_methods(self, customer_id: int) -> ServiceResponse:
        """
        Retrieve saved payment methods for a customer.
        """
        try:
            methods = self.saved_payment_method_repo.get_by_customer_id(customer_id) or []
            return ServiceResponse.success_response(
                message="Saved payment methods loaded successfully.",
                data=methods,
            )
        except Exception as exc:
            logger.exception("Failed to load saved payment methods: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def set_default_payment_method(self, customer_id: int, method_id: int) -> ServiceResponse:
        """
        Set default saved payment method.
        """
        try:
            self.saved_payment_method_repo.clear_default_for_customer(customer_id)
            self.saved_payment_method_repo.update(method_id, {"is_default": True})

            return ServiceResponse.success_response(
                message="Default payment method updated successfully."
            )
        except Exception as exc:
            logger.exception("Failed to set default payment method: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    # ------------------------------------------------------------------
    # PDF HELPERS
    # ------------------------------------------------------------------
    def _safe_money(self, value) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _safe_text(self, value, default: str = "-") -> str:
        text = str(value).strip() if value is not None else ""
        return text if text else default

    def _get_invoice_work_order_details(self, invoice: dict) -> dict:
        work_order_id = invoice.get("work_order_id")
        if not work_order_id:
            return {}
        try:
            return self.work_order_repo.get_by_id_with_details(work_order_id) or {}
        except Exception:
            return {}

    def _build_invoice_styles(self):
        styles = getSampleStyleSheet()

        return {
            "title": ParagraphStyle(
                "InvoiceTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=28,
                leading=32,
                alignment=TA_CENTER,
                textColor=colors.black,
                spaceAfter=8,
            ),
            "normal": ParagraphStyle(
                "NormalCustom",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=colors.black,
            ),
            "footer": ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=10,
                leading=13,
                alignment=TA_CENTER,
                textColor=colors.black,
            ),
            "right": ParagraphStyle(
                "Right",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                alignment=TA_RIGHT,
                textColor=colors.black,
            ),
        }

    # ------------------------------------------------------------------
    # PDF GENERATION
    # ------------------------------------------------------------------
    def generate_invoice_pdf(self, invoice_id: int) -> ServiceResponse:
        """
        Generate invoice PDF file with production-style layout.
        """
        try:
            invoice = self.invoice_repo.get_by_id(invoice_id)
            if not invoice:
                return ServiceResponse.error_response(message="Invoice not found.")

            items = self.invoice_item_repo.get_by_invoice_id(invoice_id) or []
            work_order = self._get_invoice_work_order_details(invoice)

            invoice_number = self._safe_text(invoice.get("invoice_number"), f"INV-{invoice_id}")
            customer_name = self._safe_text(
                invoice.get("customer_name") or work_order.get("customer_name"),
                "Customer",
            )
            plate_number = self._safe_text(work_order.get("plate_number"))
            vehicle_text = self._safe_text(
                f"{work_order.get('vehicle_year', '')} {work_order.get('make', '')} {work_order.get('model', '')}".strip()
            )
            work_order_code = self._safe_text(work_order.get("work_order_id"))
            issue_description = self._safe_text(work_order.get("issue_description"))
            payment_method = self._safe_text(invoice.get("payment_method_summary"), "Cash")
            payment_status = self._safe_text(invoice.get("payment_status"), "PENDING")

            subtotal = self._safe_money(invoice.get("subtotal"))
            tax_amount = self._safe_money(invoice.get("tax_amount"))
            discount_amount = self._safe_money(invoice.get("discount_amount"))
            grand_total = self._safe_money(invoice.get("grand_total"))

            output_dir = os.path.join("generated_invoices")
            os.makedirs(output_dir, exist_ok=True)

            safe_invoice_number = str(invoice_number).replace("/", "-").replace("\\", "-").strip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.abspath(
                os.path.join(output_dir, f"invoice_{safe_invoice_number}_{timestamp}.pdf")
            )

            styles = self._build_invoice_styles()

            elements = []

            elements.append(Paragraph("GaragePulse", styles["title"]))
            elements.append(Paragraph("Auto Service Management System", styles["footer"]))
            elements.append(Spacer(1, 10))

            header_table = Table(
                [
                    [
                        Paragraph(
                            "<b>GaragePulse</b><br/>"
                            "Auto Service Management System<br/>"
                            "Mount Pleasant, MI<br/>"
                            "support@garagepulse.com<br/>"
                            "+1-989-444-3313",
                            styles["normal"],
                        ),
                        Paragraph(
                            f"<b>Invoice No:</b> {invoice_number}<br/>"
                            f"<b>Invoice Date:</b> {self._safe_text(invoice.get('invoice_date'))}<br/>"
                            f"<b>Due Date:</b> {self._safe_text(invoice.get('due_date'))}<br/>"
                            f"<b>Status:</b> {payment_status}",
                            styles["normal"],
                        ),
                    ]
                ],
                colWidths=[250, 250],
            )
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            elements.append(header_table)
            elements.append(Spacer(1, 14))

            info_table = Table(
                [
                    [
                        Paragraph(
                            f"<b>Invoice To</b><br/>{customer_name}",
                            styles["normal"],
                        ),
                        Paragraph(
                            f"<b>Vehicle / Work Order</b><br/>"
                            f"Work Order: {work_order_code}<br/>"
                            f"Plate Number: {plate_number}<br/>"
                            f"Vehicle: {vehicle_text}<br/>"
                            f"Issue: {issue_description}",
                            styles["normal"],
                        ),
                    ],
                    [
                        "",
                        Paragraph(
                            f"<b>Payment Details</b><br/>"
                            f"Method: {payment_method}<br/>"
                            f"Status: {payment_status}",
                            styles["normal"],
                        ),
                    ],
                ],
                colWidths=[250, 250],
            )
            info_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(info_table)
            elements.append(Spacer(1, 14))

            line_items = [["DESCRIPTION", "QTY", "UNIT PRICE", "TOTAL"]]

            if items:
                for item in items:
                    description = self._safe_text(item.get("description"))
                    qty = self._safe_text(item.get("quantity"), "1")
                    unit_price = f"${self._safe_money(item.get('unit_price')):,.2f}"
                    line_total = f"${self._safe_money(item.get('line_total')):,.2f}"
                    line_items.append([description, qty, unit_price, line_total])
            else:
                if subtotal > 0:
                    line_items.append(
                        ["Service Charges", "1", f"${subtotal:,.2f}", f"${subtotal:,.2f}"]
                    )
                else:
                    line_items.append(["No items", "", "", "$0.00"])

            items_table = Table(
                line_items,
                colWidths=[270, 55, 95, 95],
                repeatRows=1,
            )
            items_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B53")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#B0B7C3")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            elements.append(items_table)
            elements.append(Spacer(1, 18))

            terms_para = Paragraph(
                "<b>Terms and Conditions</b><br/>"
                "Please make payment within the agreed billing period. "
                "Thank you for choosing GaragePulse for your vehicle service needs.",
                styles["normal"],
            )

            totals_table = Table(
                [
                    ["Sub-total:", f"${subtotal:,.2f}"],
                    ["Discount:", f"${discount_amount:,.2f}"],
                    ["Tax:", f"${tax_amount:,.2f}"],
                    ["Total:", f"${grand_total:,.2f}"],
                ],
                colWidths=[110, 90],
            )
            totals_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#243B53")),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )

            bottom_table = Table(
                [[terms_para, totals_table]],
                colWidths=[320, 180],
            )
            bottom_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            elements.append(bottom_table)
            elements.append(Spacer(1, 30))

            elements.append(Paragraph("Thank you for your business", styles["footer"]))
            elements.append(
                Paragraph("GaragePulse | Auto Service Management System", styles["footer"])
            )

            doc = SimpleDocTemplate(
                output_file,
                pagesize=A4,
                rightMargin=36,
                leftMargin=36,
                topMargin=30,
                bottomMargin=30,
            )

            try:
                doc.build(elements)
            except PermissionError:
                fallback_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.abspath(
                    os.path.join(
                        output_dir,
                        f"invoice_{safe_invoice_number}_{fallback_timestamp}_new.pdf",
                    )
                )
                doc = SimpleDocTemplate(
                    output_file,
                    pagesize=A4,
                    rightMargin=36,
                    leftMargin=36,
                    topMargin=30,
                    bottomMargin=30,
                )
                doc.build(elements)

            return ServiceResponse.success_response(
                message="PDF generated successfully.",
                data={"file_path": output_file},
            )

        except Exception as exc:
            logger.exception("PDF generation failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))