"""
repositories/customer_repository.py

Repository for customer-related database operations.
Handles CRUD operations and phone-based search.
"""

from typing import Dict, List, Optional

from repositories.base_repository import BaseRepository
from database.db_manager import DatabaseManager


class CustomerRepository(BaseRepository):
    """
    Repository for the customers table.
    """

    table_name = "customers"

    # -------------------------------------------------
    # Customer lookup
    # -------------------------------------------------

    def get_by_phone(self, phone: str) -> Optional[Dict]:
        """
        Find a customer by phone number.
        """
        query = """
        SELECT *
        FROM customers
        WHERE phone = %s AND is_active = 1
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (phone,))

    def search_by_phone(self, phone_fragment: str) -> List[Dict]:
        """
        Search customers using partial phone match.
        Supports professor requirement: search by phone.
        """
        query = """
        SELECT *
        FROM customers
        WHERE phone LIKE %s
        AND is_active = 1
        ORDER BY created_at DESC
        """
        return DatabaseManager.fetch_all(query, (f"%{phone_fragment}%",))

    def search_by_name(self, name: str) -> List[Dict]:
        """
        Search customers by name.
        """
        query = """
        SELECT *
        FROM customers
        WHERE full_name LIKE %s
        AND is_active = 1
        ORDER BY full_name
        """
        return DatabaseManager.fetch_all(query, (f"%{name}%",))

    # -------------------------------------------------
    # Customer listing
    # -------------------------------------------------

    def get_all_customers(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve all active customers.
        """
        query = """
        SELECT *
        FROM customers
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        return DatabaseManager.fetch_all(query, (limit, offset))

    # -------------------------------------------------
    # Customer update
    # -------------------------------------------------

    def update_customer(self, customer_id: int, data: Dict) -> int:
        """
        Update customer details.
        """
        return self.update(customer_id, data)

    # -------------------------------------------------
    # Customer creation
    # -------------------------------------------------

    def create_customer(self, data: Dict) -> int:
        """
        Create a new customer.
        """
        return self.insert(data)

    # -------------------------------------------------
    # Soft delete
    # -------------------------------------------------

    def deactivate_customer(self, customer_id: int) -> int:
        """
        Deactivate a customer instead of deleting.
        """
        query = """
        UPDATE customers
        SET is_active = 0
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (customer_id,))