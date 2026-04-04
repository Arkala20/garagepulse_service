"""
repositories/work_order_part_repository.py

Repository for work order part operations.
Handles parts added to a work order, quantity, pricing, and totals.
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class WorkOrderPartRepository(BaseRepository):
    """
    Repository for the work_order_parts table.
    """

    table_name = "work_order_parts"

    def create_part(self, data: Dict) -> int:
        """
        Add a part line to a work order.
        """
        return self.insert(data)

    def update_part(self, part_id: int, data: Dict) -> int:
        """
        Update a part line item.
        """
        return self.update(part_id, data)

    def get_by_work_order_id(self, work_order_id: int) -> List[Dict]:
        """
        Get all parts for a work order.
        """
        query = """
        SELECT *
        FROM work_order_parts
        WHERE work_order_id = %s
        ORDER BY created_at ASC, id ASC
        """
        return DatabaseManager.fetch_all(query, (work_order_id,))

    def get_part_by_id(self, part_id: int) -> Optional[Dict]:
        """
        Get a single part line by ID.
        """
        query = """
        SELECT *
        FROM work_order_parts
        WHERE id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (part_id,))

    def delete_part(self, part_id: int) -> int:
        """
        Delete a part line from a work order.
        """
        query = """
        DELETE FROM work_order_parts
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (part_id,))

    def delete_by_work_order_id(self, work_order_id: int) -> int:
        """
        Delete all part lines for a work order.
        Useful if rebuilding part list in an edit workflow.
        """
        query = """
        DELETE FROM work_order_parts
        WHERE work_order_id = %s
        """
        return DatabaseManager.execute(query, (work_order_id,))

    def get_billable_parts(self, work_order_id: int) -> List[Dict]:
        """
        Get only billable parts for a work order.
        """
        query = """
        SELECT *
        FROM work_order_parts
        WHERE work_order_id = %s
          AND is_billable = 1
        ORDER BY created_at ASC, id ASC
        """
        return DatabaseManager.fetch_all(query, (work_order_id,))

    def calculate_parts_total(self, work_order_id: int) -> float:
        """
        Calculate total billable parts amount for a work order.
        """
        query = """
        SELECT COALESCE(SUM(line_total), 0) AS parts_total
        FROM work_order_parts
        WHERE work_order_id = %s
          AND is_billable = 1
        """
        result = DatabaseManager.fetch_one(query, (work_order_id,))
        return float(result["parts_total"]) if result else 0.0

    def count_parts(self, work_order_id: int) -> int:
        """
        Count number of part lines linked to a work order.
        """
        query = """
        SELECT COUNT(*) AS count
        FROM work_order_parts
        WHERE work_order_id = %s
        """
        result = DatabaseManager.fetch_one(query, (work_order_id,))
        return int(result["count"]) if result else 0