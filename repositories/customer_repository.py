"""
repositories/customer_repository.py

Repository for customer-related database operations.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    """
    Repository for the customers table.
    """

    table_name = "customers"

    def create_customer(self, data: Dict) -> int:
        return self.insert(data)

    def update_customer(self, customer_id: int, data: Dict) -> int:
        return self.update(customer_id, data)

    def get_all_customers(self) -> List[Dict]:
        query = """
        SELECT
            id,
            full_name,
            phone,
            email,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            notes,
            is_active,
            created_at,
            updated_at
        FROM customers
        WHERE is_active = 1
        ORDER BY full_name ASC, id DESC
        """
        return DatabaseManager.fetch_all(query)

    def get_by_id(self, customer_id: int) -> Optional[Dict]:
        query = """
        SELECT
            id,
            full_name,
            phone,
            email,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            notes,
            is_active,
            created_at,
            updated_at
        FROM customers
        WHERE id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (customer_id,))

    def search_by_phone(self, phone_fragment: str) -> List[Dict]:
        query = """
        SELECT
            id,
            full_name,
            phone,
            email,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            notes,
            is_active,
            created_at,
            updated_at
        FROM customers
        WHERE is_active = 1
          AND phone LIKE %s
        ORDER BY full_name ASC, id DESC
        """
        return DatabaseManager.fetch_all(query, (f"%{phone_fragment}%",))

    def search_customers(self, search_text: str) -> List[Dict]:
        """
        Search customers using any useful visible field.
        """
        like_value = f"%{search_text}%"

        query = """
        SELECT
            id,
            full_name,
            phone,
            email,
            address_line_1,
            address_line_2,
            city,
            state,
            postal_code,
            notes,
            is_active,
            created_at,
            updated_at
        FROM customers
        WHERE is_active = 1
          AND (
                full_name LIKE %s
                OR phone LIKE %s
                OR email LIKE %s
                OR address_line_1 LIKE %s
                OR address_line_2 LIKE %s
                OR city LIKE %s
                OR state LIKE %s
                OR postal_code LIKE %s
                OR notes LIKE %s
              )
        ORDER BY full_name ASC, id DESC
        """
        params = (
            like_value,
            like_value,
            like_value,
            like_value,
            like_value,
            like_value,
            like_value,
            like_value,
            like_value,
        )
        return DatabaseManager.fetch_all(query, params)

    def deactivate_customer(self, customer_id: int) -> int:
        query = """
        UPDATE customers
        SET is_active = 0,
            updated_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (customer_id,))