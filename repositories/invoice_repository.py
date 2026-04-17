"""
repositories/invoice_repository.py

Repository for invoice-related operations.
Aligned with schema.sql fields, including:
- payment_method_summary
- labor_total
- parts_total
- subtotal
- tax_rate
- tax_amount
- discount_amount
- grand_total
- payment_status
- paid_at
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class InvoiceRepository(BaseRepository):
    """
    Repository for the invoices table.
    """

    table_name = "invoices"

    def create_invoice(self, data: Dict) -> int:
        """
        Create a new invoice.
        """
        return self.insert(data)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Dict]:
        """
        Get invoice by business invoice number.
        """
        query = """
        SELECT
            i.*,
            wo.work_order_id,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            c.email AS customer_email
        FROM invoices i
        JOIN work_orders wo ON i.work_order_id = wo.id
        JOIN customers c ON i.customer_id = c.id
        WHERE i.invoice_number = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (invoice_number,))

    def get_by_work_order_id(self, work_order_id: int) -> Optional[Dict]:
        """
        Get invoice linked to a work order.
        """
        query = """
        SELECT *
        FROM invoices
        WHERE work_order_id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (work_order_id,))

    def get_all_invoices(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve all invoices with customer and work order details.
        """
        query = """
        SELECT
            i.*,
            wo.work_order_id,
            c.full_name AS customer_name
        FROM invoices i
        JOIN work_orders wo ON i.work_order_id = wo.id
        JOIN customers c ON i.customer_id = c.id
        ORDER BY i.created_at DESC, i.id DESC
        LIMIT %s OFFSET %s
        """
        return DatabaseManager.fetch_all(query, (limit, offset))

    def update_payment_status(
        self,
        invoice_id: int,
        payment_status: str,
        payment_method_summary: Optional[str] = None,
    ) -> int:
        """
        Update invoice payment status and optional payment method summary.

        Sets paid_at when payment status becomes PAID.
        """
        query = """
        UPDATE invoices
        SET payment_status = %s,
            payment_method_summary = %s,
            paid_at = CASE
                WHEN %s = 'PAID' THEN NOW()
                ELSE paid_at
            END,
            updated_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(
            query,
            (
                payment_status,
                payment_method_summary,
                payment_status,
                invoice_id,
            ),
        )

    def update_invoice_totals(
        self,
        invoice_id,
        labor_total,
        parts_total,
        subtotal,
        tax_rate,
        tax_amount,
        discount_amount,
        grand_total,
        due_date,
        notes,
    ):
        query = """
        UPDATE invoices
        SET labor_total = %s,
            parts_total = %s,
            subtotal = %s,
            tax_rate = %s,
            tax_amount = %s,
            discount_amount = %s,
            grand_total = %s,
            due_date = %s,
            notes = %s,
            updated_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(
            query,
            (
                labor_total,
                parts_total,
                subtotal,
                tax_rate,
                tax_amount,
                discount_amount,
                grand_total,
                due_date,
                notes,
                invoice_id,
            ),
        )

    def get_total_revenue(self) -> float:
        """
        Calculate all-time invoiced revenue.
        """
        query = """
        SELECT COALESCE(SUM(grand_total), 0) AS total_revenue
        FROM invoices
        """
        result = DatabaseManager.fetch_one(query)
        return float(result["total_revenue"]) if result else 0.0

    def get_current_month_revenue(self) -> float:
        """
        Calculate invoiced revenue for the current month.

        Business rule:
        - based on invoice creation month
        - includes all generated invoices
        """
        query = """
        SELECT COALESCE(SUM(grand_total), 0) AS total_revenue
        FROM invoices
        WHERE YEAR(created_at) = YEAR(CURDATE())
          AND MONTH(created_at) = MONTH(CURDATE())
        """
        result = DatabaseManager.fetch_one(query)
        return float(result["total_revenue"]) if result else 0.0

    def get_current_month_collected_revenue(self) -> float:
        """
        Optional metric: money actually collected this month.
        Uses paid_at and PAID status.
        """
        query = """
        SELECT COALESCE(SUM(grand_total), 0) AS total_revenue
        FROM invoices
        WHERE payment_status = 'PAID'
          AND paid_at IS NOT NULL
          AND YEAR(paid_at) = YEAR(CURDATE())
          AND MONTH(paid_at) = MONTH(CURDATE())
        """
        result = DatabaseManager.fetch_one(query)
        return float(result["total_revenue"]) if result else 0.0

    def get_pending_payments_count(self) -> int:
        """
        Count invoices that are pending or partially paid.
        """
        query = """
        SELECT COUNT(*) AS count
        FROM invoices
        WHERE payment_status IN ('PENDING', 'PARTIAL')
        """
        result = DatabaseManager.fetch_one(query)
        return int(result["count"]) if result else 0

    def delete_invoice(self, invoice_id: int) -> int:
        """
        Delete an invoice.
        Use cautiously.
        """
        query = """
        DELETE FROM invoices
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (invoice_id,))