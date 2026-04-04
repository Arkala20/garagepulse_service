"""
repositories/notification_repository.py

Repository for notification-related database operations.
Supports notification listing, customer-linked display, and detail retrieval.
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    """
    Repository for the notifications table.
    """

    table_name = "notifications"

    def create_notification(self, data: Dict) -> int:
        """
        Create a new notification record.
        """
        return self.insert(data)

    def get_by_id_with_details(self, notification_id: int) -> Optional[Dict]:
        """
        Get a notification with customer and work order details.

        Used when user clicks a notification to open full details.
        """
        query = """
        SELECT
            n.*,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            c.email AS customer_email,
            wo.work_order_id
        FROM notifications n
        JOIN customers c ON n.customer_id = c.id
        JOIN work_orders wo ON n.work_order_id = wo.id
        WHERE n.id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (notification_id,))

    def get_all_notifications(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Get notification list for UI.

        Professor requirement:
        show customer name instead of message preview in list view.
        """
        query = """
        SELECT
            n.id,
            n.channel,
            n.delivery_status,
            n.sent_at,
            n.created_at,
            c.full_name AS customer_name,
            wo.work_order_id
        FROM notifications n
        JOIN customers c ON n.customer_id = c.id
        JOIN work_orders wo ON n.work_order_id = wo.id
        ORDER BY n.created_at DESC
        LIMIT %s OFFSET %s
        """
        return DatabaseManager.fetch_all(query, (limit, offset))

    def get_by_work_order_id(self, work_order_id: int) -> List[Dict]:
        """
        Get all notifications linked to a work order.
        """
        query = """
        SELECT
            n.*,
            c.full_name AS customer_name
        FROM notifications n
        JOIN customers c ON n.customer_id = c.id
        WHERE n.work_order_id = %s
        ORDER BY n.created_at DESC
        """
        return DatabaseManager.fetch_all(query, (work_order_id,))

    def get_by_customer_id(self, customer_id: int) -> List[Dict]:
        """
        Get all notifications linked to a customer.
        """
        query = """
        SELECT
            n.*,
            wo.work_order_id
        FROM notifications n
        JOIN work_orders wo ON n.work_order_id = wo.id
        WHERE n.customer_id = %s
        ORDER BY n.created_at DESC
        """
        return DatabaseManager.fetch_all(query, (customer_id,))

    def get_by_delivery_status(self, delivery_status: str) -> List[Dict]:
        """
        Get notifications filtered by delivery status.
        Example: PENDING, SENT, FAILED
        """
        query = """
        SELECT
            n.*,
            c.full_name AS customer_name,
            wo.work_order_id
        FROM notifications n
        JOIN customers c ON n.customer_id = c.id
        JOIN work_orders wo ON n.work_order_id = wo.id
        WHERE n.delivery_status = %s
        ORDER BY n.created_at DESC
        """
        return DatabaseManager.fetch_all(query, (delivery_status,))

    def update_delivery_status(
        self,
        notification_id: int,
        delivery_status: str,
        provider_status: Optional[str] = None,
        error_message: Optional[str] = None,
        external_reference: Optional[str] = None,
    ) -> int:
        """
        Update notification delivery status and provider response details.
        """
        query = """
        UPDATE notifications
        SET delivery_status = %s,
            provider_status = %s,
            error_message = %s,
            external_reference = %s,
            sent_at = CASE
                WHEN %s = 'SENT' THEN NOW()
                ELSE sent_at
            END
        WHERE id = %s
        """
        return DatabaseManager.execute(
            query,
            (
                delivery_status,
                provider_status,
                error_message,
                external_reference,
                delivery_status,
                notification_id,
            ),
        )

    def count_failed_notifications(self) -> int:
        """
        Count failed notifications for monitoring/dashboard purposes.
        """
        query = """
        SELECT COUNT(*) AS count
        FROM notifications
        WHERE delivery_status = 'FAILED'
        """
        result = DatabaseManager.fetch_one(query)
        return int(result["count"]) if result else 0