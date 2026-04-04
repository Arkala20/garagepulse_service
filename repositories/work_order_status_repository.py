"""
repositories/work_order_status_repository.py

Repository for work order status history operations.
Aligned with schema.sql fields:
- work_order_id
- status_value
- status_note
- changed_by
- changed_at
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class WorkOrderStatusRepository(BaseRepository):
    """
    Repository for the work_order_status_history table.
    """

    table_name = "work_order_status_history"

    def add_status_history(self, data: Dict) -> int:
        """
        Insert a new status history record.

        Expected data keys:
            work_order_id
            status_value
            status_note (optional)
            changed_by (optional)
            changed_at (optional)
        """
        return self.insert(data)

    def get_status_history(self, work_order_id: int) -> List[Dict]:
        """
        Retrieve full status history timeline for a work order.
        """
        query = """
        SELECT
            h.*,
            u.username AS changed_by_user,
            u.first_name,
            u.last_name
        FROM work_order_status_history h
        LEFT JOIN users u ON h.changed_by = u.id
        WHERE h.work_order_id = %s
        ORDER BY h.changed_at ASC, h.id ASC
        """
        return DatabaseManager.fetch_all(query, (work_order_id,))

    def get_latest_status(self, work_order_id: int) -> Optional[Dict]:
        """
        Get the latest status history entry for a work order.
        """
        query = """
        SELECT
            h.*,
            u.username AS changed_by_user
        FROM work_order_status_history h
        LEFT JOIN users u ON h.changed_by = u.id
        WHERE h.work_order_id = %s
        ORDER BY h.changed_at DESC, h.id DESC
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (work_order_id,))

    def get_status_counts(self, work_order_id: int) -> List[Dict]:
        """
        Return grouped counts by status_value for a work order.
        """
        query = """
        SELECT
            status_value,
            COUNT(*) AS status_count
        FROM work_order_status_history
        WHERE work_order_id = %s
        GROUP BY status_value
        ORDER BY status_value ASC
        """
        return DatabaseManager.fetch_all(query, (work_order_id,))

    def count_status_changes(self, work_order_id: int) -> int:
        """
        Count number of status history records for a work order.
        """
        query = """
        SELECT COUNT(*) AS count
        FROM work_order_status_history
        WHERE work_order_id = %s
        """
        result = DatabaseManager.fetch_one(query, (work_order_id,))
        return int(result["count"]) if result else 0

    def delete_by_work_order_id(self, work_order_id: int) -> int:
        """
        Delete all status history rows for a work order.
        Use cautiously.
        """
        query = """
        DELETE FROM work_order_status_history
        WHERE work_order_id = %s
        """
        return DatabaseManager.execute(query, (work_order_id,))