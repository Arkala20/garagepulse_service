"""
repositories/saved_payment_method_repository.py

Repository for saved payment methods.
Supports storing masked card information for customers.
Never stores raw card numbers.
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class SavedPaymentMethodRepository(BaseRepository):
    """
    Repository for saved_payment_methods table.
    """

    table_name = "saved_payment_methods"

    # -------------------------------------------------
    # Create payment method
    # -------------------------------------------------

    def create_payment_method(self, data: Dict) -> int:
        """
        Save a new payment method.

        Expected fields:
            customer_id
            card_brand
            last_four
            expiry_month
            expiry_year
            token_reference
            is_default
        """
        return self.insert(data)

    # -------------------------------------------------
    # Get methods
    # -------------------------------------------------

    def get_by_customer_id(self, customer_id: int) -> List[Dict]:
        """
        Get all saved payment methods for a customer.
        """
        query = """
        SELECT *
        FROM saved_payment_methods
        WHERE customer_id = %s
        ORDER BY is_default DESC, created_at DESC
        """
        return DatabaseManager.fetch_all(query, (customer_id,))

    def get_default_method(self, customer_id: int) -> Optional[Dict]:
        """
        Get default saved payment method for a customer.
        """
        query = """
        SELECT *
        FROM saved_payment_methods
        WHERE customer_id = %s
          AND is_default = 1
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (customer_id,))

    def get_by_id(self, method_id: int) -> Optional[Dict]:
        """
        Get payment method by ID.
        """
        query = """
        SELECT *
        FROM saved_payment_methods
        WHERE id = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (method_id,))

    # -------------------------------------------------
    # Default management
    # -------------------------------------------------

    def set_default_method(self, method_id: int, customer_id: int) -> int:
        """
        Set a payment method as default.
        Clears other defaults first.
        """
        # Clear existing default
        clear_query = """
        UPDATE saved_payment_methods
        SET is_default = 0
        WHERE customer_id = %s
        """
        DatabaseManager.execute(clear_query, (customer_id,))

        # Set new default
        set_query = """
        UPDATE saved_payment_methods
        SET is_default = 1
        WHERE id = %s
        """
        return DatabaseManager.execute(set_query, (method_id,))

    # -------------------------------------------------
    # Delete method
    # -------------------------------------------------

    def delete_method(self, method_id: int) -> int:
        """
        Delete a saved payment method.
        """
        query = """
        DELETE FROM saved_payment_methods
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (method_id,))