"""
repositories/invoice_item_repository.py

Repository for invoice item operations.
Handles invoice line items such as labor and parts breakdown.
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class InvoiceItemRepository(BaseRepository):
    """
    Repository for the invoice_items table.
    """

    table_name = "invoice_items"

    def create_item(self, data: Dict) -> int:
        """
        Add a line item to an invoice.
        """
        return self.insert(data)

    def create_items_bulk(self, items: List[Dict]) -> int:
        """
        Insert multiple invoice items in one operation.

        Returns:
            Number of affected rows
        """
        if not items:
            return 0

        columns = [
            "invoice_id",
            "item_type",
            "description",
            "quantity",
            "unit_price",
            "line_total",
            "source_reference",
        ]

        query = f"""
        INSERT INTO {self.table_name}
        ({", ".join(columns)})
        VALUES ({", ".join(["%s"] * len(columns))})
        """

        param_list = [
            (
                item.get("invoice_id"),
                item.get("item_type"),
                item.get("description"),
                item.get("quantity", 1),
                item.get("unit_price", 0),
                item.get("line_total", 0),
                item.get("source_reference"),
            )
            for item in items
        ]

        return DatabaseManager.execute_many(query, param_list)

    def get_by_invoice_id(self, invoice_id: int) -> List[Dict]:
        """
        Get all line items for an invoice.
        """
        query = """
        SELECT *
        FROM invoice_items
        WHERE invoice_id = %s
        ORDER BY id ASC
        """
        return DatabaseManager.fetch_all(query, (invoice_id,))

    def get_item_by_id(self, item_id: int) -> Optional[Dict]:
        """
        Get a single invoice item by ID.
        """
        query = """
        SELECT *
        FROM invoice_items
        WHERE id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (item_id,))

    def get_by_item_type(self, invoice_id: int, item_type: str) -> List[Dict]:
        """
        Get invoice items filtered by item type.
        Example item types: LABOR, PART
        """
        query = """
        SELECT *
        FROM invoice_items
        WHERE invoice_id = %s
          AND item_type = %s
        ORDER BY id ASC
        """
        return DatabaseManager.fetch_all(query, (invoice_id, item_type))

    def update_item(self, item_id: int, data: Dict) -> int:
        """
        Update an invoice line item.
        """
        return self.update(item_id, data)

    def delete_item(self, item_id: int) -> int:
        """
        Delete a single invoice item.
        """
        query = """
        DELETE FROM invoice_items
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (item_id,))

    def delete_by_invoice_id(self, invoice_id: int) -> int:
        """
        Delete all items linked to an invoice.
        Useful when rebuilding invoice items during invoice edit/regeneration.
        """
        query = """
        DELETE FROM invoice_items
        WHERE invoice_id = %s
        """
        return DatabaseManager.execute(query, (invoice_id,))

    def calculate_invoice_subtotal(self, invoice_id: int) -> float:
        """
        Calculate subtotal from all invoice items.
        """
        query = """
        SELECT COALESCE(SUM(line_total), 0) AS subtotal
        FROM invoice_items
        WHERE invoice_id = %s
        """
        result = DatabaseManager.fetch_one(query, (invoice_id,))
        return float(result["subtotal"]) if result else 0.0

    def count_items(self, invoice_id: int) -> int:
        """
        Count number of line items for an invoice.
        """
        query = """
        SELECT COUNT(*) AS count
        FROM invoice_items
        WHERE invoice_id = %s
        """
        result = DatabaseManager.fetch_one(query, (invoice_id,))
        return int(result["count"]) if result else 0