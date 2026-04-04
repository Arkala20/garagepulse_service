"""
repositories/work_order_repository.py

Repository for work order operations.
Handles creation, updates, status tracking, and listing.
"""

from typing import Dict, List, Optional

from repositories.base_repository import BaseRepository
from database.db_manager import DatabaseManager


class WorkOrderRepository(BaseRepository):
    """
    Repository for the work_orders table.
    """

    table_name = "work_orders"

    # -------------------------------------------------
    # Work Order Lookup
    # -------------------------------------------------

    def get_by_work_order_id(self, work_order_id: str) -> Optional[Dict]:
        """
        Get work order using business ID (WO-000001).
        """
        query = """
        SELECT wo.*, 
               c.full_name AS customer_name,
               v.plate_number,
               u.username AS assigned_staff
        FROM work_orders wo
        JOIN customers c ON wo.customer_id = c.id
        JOIN vehicles v ON wo.vehicle_id = v.id
        LEFT JOIN users u ON wo.assigned_staff_id = u.id
        WHERE wo.work_order_id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (work_order_id,))

    def get_by_id_with_details(self, record_id: int) -> Optional[Dict]:
        """
        Get work order by internal ID with joins.
        """
        query = """
        SELECT wo.*, 
               c.full_name AS customer_name,
               c.phone AS customer_phone,
               v.plate_number,
               v.make,
               v.model,
               u.username AS assigned_staff
        FROM work_orders wo
        JOIN customers c ON wo.customer_id = c.id
        JOIN vehicles v ON wo.vehicle_id = v.id
        LEFT JOIN users u ON wo.assigned_staff_id = u.id
        WHERE wo.id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (record_id,))

    # -------------------------------------------------
    # Work Order Listing
    # -------------------------------------------------

    def get_all_work_orders(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve all work orders.
        """
        query = """
        SELECT wo.*, 
               c.full_name AS customer_name,
               v.plate_number
        FROM work_orders wo
        JOIN customers c ON wo.customer_id = c.id
        JOIN vehicles v ON wo.vehicle_id = v.id
        ORDER BY wo.created_at DESC
        LIMIT %s OFFSET %s
        """
        return DatabaseManager.fetch_all(query, (limit, offset))

    def get_by_status(self, status: str) -> List[Dict]:
        """
        Get work orders filtered by status.
        """
        query = """
        SELECT *
        FROM work_orders
        WHERE current_status = %s
        ORDER BY updated_at DESC
        """
        return DatabaseManager.fetch_all(query, (status,))

    def get_active_work_orders(self) -> List[Dict]:
        """
        Get active (non-completed) work orders.
        """
        query = """
        SELECT *
        FROM work_orders
        WHERE current_status IN ('NEW', 'IN_PROGRESS', 'READY')
        ORDER BY updated_at DESC
        """
        return DatabaseManager.fetch_all(query)

    # -------------------------------------------------
    # Create / Update
    # -------------------------------------------------

    def create_work_order(self, data: Dict) -> int:
        """
        Create new work order.
        """
        return self.insert(data)

    def update_work_order(self, work_order_id: int, data: Dict) -> int:
        """
        Update work order fields.
        """
        return self.update(work_order_id, data)

    # -------------------------------------------------
    # Status Management
    # -------------------------------------------------

    def update_status(self, work_order_id: int, status: str) -> int:
        """
        Update current status of work order.
        """
        query = """
        UPDATE work_orders
        SET current_status = %s,
            updated_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (status, work_order_id))

    # -------------------------------------------------
    # Financial Updates
    # -------------------------------------------------

    def update_costs(
        self,
        work_order_id: int,
        labor_cost: float,
        parts_total: float,
        subtotal: float,
    ) -> int:
        """
        Update financial fields of work order.
        """
        query = """
        UPDATE work_orders
        SET labor_cost = %s,
            parts_total = %s,
            subtotal = %s
        WHERE id = %s
        """
        return DatabaseManager.execute(
            query,
            (labor_cost, parts_total, subtotal, work_order_id),
        )

    # -------------------------------------------------
    # Assignment
    # -------------------------------------------------

    def assign_staff(self, work_order_id: int, staff_id: int) -> int:
        """
        Assign staff to work order.
        """
        query = """
        UPDATE work_orders
        SET assigned_staff_id = %s
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (staff_id, work_order_id))

    # -------------------------------------------------
    # Dashboard Queries
    # -------------------------------------------------

    def count_active_work_orders(self) -> int:
        query = """
        SELECT COUNT(*) AS count
        FROM work_orders
        WHERE current_status IN ('NEW', 'IN_PROGRESS', 'READY')
        """
        result = DatabaseManager.fetch_one(query)
        return result["count"] if result else 0

    def count_completed_today(self) -> int:
        query = """
        SELECT COUNT(*) AS count
        FROM work_orders
        WHERE DATE(completed_at) = CURDATE()
        """
        result = DatabaseManager.fetch_one(query)
        return result["count"] if result else 0