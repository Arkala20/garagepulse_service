

from __future__ import annotations

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class VehicleRepository(BaseRepository):
        table_name = "vehicles"

        def create_vehicle(self, data: Dict) -> int:
            return self.insert(data)

        def update_vehicle(self, vehicle_id: int, data: Dict) -> int:
            return self.update(vehicle_id, data)

        def get_by_id(self, vehicle_id: int) -> Optional[Dict]:
            query = """
            SELECT
                v.id,
                v.customer_id,
                c.full_name AS customer_name,
                c.phone,
                v.make,
                v.model,
                v.vehicle_year,
                v.vin,
                v.plate_number,
                v.color,
                v.mileage,
                v.notes,
                v.is_active,
                COALESCE(wo.current_status, 'NEW') AS current_status,
                v.created_at,
                v.updated_at
            FROM vehicles v
            INNER JOIN customers c
                ON c.id = v.customer_id
            LEFT JOIN (
                SELECT w1.vehicle_id, w1.current_status
                FROM work_orders w1
                INNER JOIN (
                    SELECT vehicle_id, MAX(id) AS latest_id
                    FROM work_orders
                    GROUP BY vehicle_id
                ) latest
                    ON latest.latest_id = w1.id
            ) wo
                ON wo.vehicle_id = v.id
            WHERE v.id = %s
              AND v.is_active = 1
            LIMIT 1
            """
            return DatabaseManager.fetch_one(query, (vehicle_id,))

        def get_by_customer_id(self, customer_id: int) -> List[Dict]:
            query = """
            SELECT
                v.id,
                v.customer_id,
                c.full_name AS customer_name,
                c.phone,
                v.make,
                v.model,
                v.vehicle_year,
                v.vin,
                v.plate_number,
                v.color,
                v.mileage,
                v.notes,
                v.is_active,
                COALESCE(wo.current_status, 'NEW') AS current_status,
                v.created_at,
                v.updated_at
            FROM vehicles v
            INNER JOIN customers c
                ON c.id = v.customer_id
            LEFT JOIN (
                SELECT w1.vehicle_id, w1.current_status
                FROM work_orders w1
                INNER JOIN (
                    SELECT vehicle_id, MAX(id) AS latest_id
                    FROM work_orders
                    GROUP BY vehicle_id
                ) latest
                    ON latest.latest_id = w1.id
            ) wo
                ON wo.vehicle_id = v.id
            WHERE v.customer_id = %s
              AND v.is_active = 1
            ORDER BY v.created_at DESC, v.id DESC
            """
            return DatabaseManager.fetch_all(query, (customer_id,))

        def get_all_vehicles(self) -> List[Dict]:
            query = """
            SELECT
                v.id,
                v.customer_id,
                c.full_name AS customer_name,
                c.phone,
                v.make,
                v.model,
                v.vehicle_year,
                v.vin,
                v.plate_number,
                v.color,
                v.mileage,
                v.notes,
                v.is_active,
                COALESCE(wo.current_status, 'NEW') AS current_status,
                v.created_at,
                v.updated_at
            FROM vehicles v
            INNER JOIN customers c
                ON c.id = v.customer_id
            LEFT JOIN (
                SELECT w1.vehicle_id, w1.current_status
                FROM work_orders w1
                INNER JOIN (
                    SELECT vehicle_id, MAX(id) AS latest_id
                    FROM work_orders
                    GROUP BY vehicle_id
                ) latest
                    ON latest.latest_id = w1.id
            ) wo
                ON wo.vehicle_id = v.id
            WHERE v.is_active = 1
            ORDER BY v.created_at DESC, v.id DESC
            """
            return DatabaseManager.fetch_all(query)

        def get_by_plate_number(self, plate_number: str) -> Optional[Dict]:
            query = """
            SELECT
                v.id,
                v.customer_id,
                c.full_name AS customer_name,
                c.phone,
                v.make,
                v.model,
                v.vehicle_year,
                v.vin,
                v.plate_number,
                v.color,
                v.mileage,
                v.notes,
                v.is_active,
                COALESCE(wo.current_status, 'NEW') AS current_status,
                v.created_at,
                v.updated_at
            FROM vehicles v
            INNER JOIN customers c
                ON c.id = v.customer_id
            LEFT JOIN (
                SELECT w1.vehicle_id, w1.current_status
                FROM work_orders w1
                INNER JOIN (
                    SELECT vehicle_id, MAX(id) AS latest_id
                    FROM work_orders
                    GROUP BY vehicle_id
                ) latest
                    ON latest.latest_id = w1.id
            ) wo
                ON wo.vehicle_id = v.id
            WHERE v.is_active = 1
              AND UPPER(v.plate_number) = UPPER(%s)
            LIMIT 1
            """
            return DatabaseManager.fetch_one(query, (plate_number,))

        def search_by_plate(self, plate_fragment: str) -> List[Dict]:
            query = """
            SELECT
                v.id,
                v.customer_id,
                c.full_name AS customer_name,
                c.phone,
                v.make,
                v.model,
                v.vehicle_year,
                v.vin,
                v.plate_number,
                v.color,
                v.mileage,
                v.notes,
                v.is_active,
                COALESCE(wo.current_status, 'NEW') AS current_status,
                v.created_at,
                v.updated_at
            FROM vehicles v
            INNER JOIN customers c
                ON c.id = v.customer_id
            LEFT JOIN (
                SELECT w1.vehicle_id, w1.current_status
                FROM work_orders w1
                INNER JOIN (
                    SELECT vehicle_id, MAX(id) AS latest_id
                    FROM work_orders
                    GROUP BY vehicle_id
                ) latest
                    ON latest.latest_id = w1.id
            ) wo
                ON wo.vehicle_id = v.id
            WHERE v.is_active = 1
              AND v.plate_number LIKE %s
            ORDER BY v.created_at DESC, v.id DESC
            """
            return DatabaseManager.fetch_all(query, (f"%{plate_fragment}%",))

        def get_prioritized_vehicle_list(self) -> List[Dict]:
            query = """
            SELECT
                v.id,
                v.customer_id,
                c.full_name AS customer_name,
                c.phone,
                v.make,
                v.model,
                v.vehicle_year,
                v.vin,
                v.plate_number,
                v.color,
                v.mileage,
                v.notes,
                v.is_active,
                COALESCE(wo.current_status, 'NEW') AS current_status,
                v.created_at,
                v.updated_at,
                CASE
                    WHEN wo.current_status IN ('IN_PROGRESS', 'READY') THEN 0
                    ELSE 1
                END AS priority_rank
            FROM vehicles v
            INNER JOIN customers c
                ON c.id = v.customer_id
            LEFT JOIN (
                SELECT w1.vehicle_id, w1.current_status
                FROM work_orders w1
                INNER JOIN (
                    SELECT vehicle_id, MAX(id) AS latest_id
                    FROM work_orders
                    GROUP BY vehicle_id
                ) latest
                    ON latest.latest_id = w1.id
            ) wo
                ON wo.vehicle_id = v.id
            WHERE v.is_active = 1
            ORDER BY priority_rank ASC, v.created_at DESC, v.id DESC
            """
            return DatabaseManager.fetch_all(query)

        def deactivate_vehicle(self, vehicle_id: int) -> int:
            query = """
            UPDATE vehicles
            SET is_active = 0,
                updated_at = NOW()
            WHERE id = %s
            """
            return DatabaseManager.execute(query, (vehicle_id,))