"""
repositories/vehicle_repository.py

Repository for vehicle-related database operations.
Supports customer linkage, plate search, and prioritized vehicle listing.
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class VehicleRepository(BaseRepository):
    """
    Repository for the vehicles table.
    """

    table_name = "vehicles"

    def get_by_plate_number(self, plate_number: str) -> Optional[Dict]:
        """
        Find a single active vehicle by exact plate number.
        """
        query = """
        SELECT v.*, c.full_name AS customer_name, c.phone AS customer_phone
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        WHERE v.plate_number = %s
          AND v.is_active = 1
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (plate_number,))

    def get_by_vin(self, vin: str) -> Optional[Dict]:
        """
        Find a single active vehicle by VIN.
        """
        query = """
        SELECT v.*, c.full_name AS customer_name, c.phone AS customer_phone
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        WHERE v.vin = %s
          AND v.is_active = 1
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (vin,))

    def search_by_plate(self, plate_fragment: str) -> List[Dict]:
        """
        Search active vehicles using partial plate number match.

        Supports professor requirement:
        search by vehicle number / license plate.
        """
        query = """
        SELECT v.*, c.full_name AS customer_name, c.phone AS customer_phone
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        WHERE v.plate_number LIKE %s
          AND v.is_active = 1
        ORDER BY v.updated_at DESC, v.created_at DESC
        """
        return DatabaseManager.fetch_all(query, (f"%{plate_fragment}%",))

    def search_by_make_or_model(self, search_text: str) -> List[Dict]:
        """
        Search active vehicles by make or model.
        """
        query = """
        SELECT v.*, c.full_name AS customer_name, c.phone AS customer_phone
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        WHERE (v.make LIKE %s OR v.model LIKE %s)
          AND v.is_active = 1
        ORDER BY v.updated_at DESC, v.created_at DESC
        """
        like_value = f"%{search_text}%"
        return DatabaseManager.fetch_all(query, (like_value, like_value))

    def get_by_customer_id(self, customer_id: int) -> List[Dict]:
        """
        Get all active vehicles for a customer.
        """
        query = """
        SELECT *
        FROM vehicles
        WHERE customer_id = %s
          AND is_active = 1
        ORDER BY updated_at DESC, created_at DESC
        """
        return DatabaseManager.fetch_all(query, (customer_id,))

    def get_all_vehicles(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all active vehicles with customer details.
        """
        query = """
        SELECT v.*, c.full_name AS customer_name, c.phone AS customer_phone
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        WHERE v.is_active = 1
        ORDER BY v.updated_at DESC, v.created_at DESC
        LIMIT %s OFFSET %s
        """
        return DatabaseManager.fetch_all(query, (limit, offset))

    def get_prioritized_vehicle_list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Return vehicles prioritized for dashboard/vehicle page display.

        Priority:
        1. Vehicles tied to IN_PROGRESS or READY work orders
        2. Most recently updated vehicles
        3. Most recently created vehicles

        This supports the professor requirement to emphasize
        latest or in-progress relevant vehicles first.
        """
        query = """
        SELECT
            v.*,
            c.full_name AS customer_name,
            c.phone AS customer_phone,
            wo.work_order_id,
            wo.current_status,
            wo.updated_at AS work_order_updated_at,
            CASE
                WHEN wo.current_status = 'IN_PROGRESS' THEN 1
                WHEN wo.current_status = 'READY' THEN 2
                ELSE 3
            END AS priority_rank
        FROM vehicles v
        JOIN customers c ON v.customer_id = c.id
        LEFT JOIN (
            SELECT w1.*
            FROM work_orders w1
            INNER JOIN (
                SELECT vehicle_id, MAX(updated_at) AS max_updated_at
                FROM work_orders
                GROUP BY vehicle_id
            ) w2
                ON w1.vehicle_id = w2.vehicle_id
               AND w1.updated_at = w2.max_updated_at
        ) wo ON v.id = wo.vehicle_id
        WHERE v.is_active = 1
        ORDER BY
            priority_rank ASC,
            CASE
                WHEN wo.current_status IN ('IN_PROGRESS', 'READY') THEN wo.updated_at
                ELSE NULL
            END DESC,
            v.updated_at DESC,
            v.created_at DESC
        LIMIT %s OFFSET %s
        """
        return DatabaseManager.fetch_all(query, (limit, offset))

    def create_vehicle(self, data: Dict) -> int:
        """
        Create a new vehicle.
        """
        return self.insert(data)

    def update_vehicle(self, vehicle_id: int, data: Dict) -> int:
        """
        Update vehicle details.
        """
        return self.update(vehicle_id, data)

    def deactivate_vehicle(self, vehicle_id: int) -> int:
        """
        Soft deactivate a vehicle instead of deleting it.
        """
        query = """
        UPDATE vehicles
        SET is_active = 0
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (vehicle_id,))