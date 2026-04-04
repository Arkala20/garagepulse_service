"""
repositories/base_repository.py

Base repository providing common database operations.
All repositories should inherit from this class.
"""

from typing import Any, Dict, List, Optional

from database.db_manager import DatabaseManager


class BaseRepository:
    """
    Base repository class with common CRUD helpers.
    """

    table_name: str = ""

    def __init__(self):
        if not self.table_name:
            raise ValueError("table_name must be defined in subclass")

    # -------------------------------------------------
    # Basic CRUD operations
    # -------------------------------------------------

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        return DatabaseManager.fetch_one(query, (record_id,))

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} LIMIT %s OFFSET %s"
        return DatabaseManager.fetch_all(query, (limit, offset))

    def delete_by_id(self, record_id: int) -> int:
        query = f"DELETE FROM {self.table_name} WHERE id = %s"
        return DatabaseManager.execute(query, (record_id,))

    # -------------------------------------------------
    # Insert helper
    # -------------------------------------------------

    def insert(self, data: Dict[str, Any]) -> int:
        """
        Insert a record dynamically.

        Args:
            data: dictionary of column -> value

        Returns:
            last inserted id
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))

        query = f"""
            INSERT INTO {self.table_name} ({columns})
            VALUES ({placeholders})
        """

        return DatabaseManager.execute_and_get_last_id(
            query,
            tuple(data.values())
        )

    # -------------------------------------------------
    # Update helper
    # -------------------------------------------------

    def update(self, record_id: int, data: Dict[str, Any]) -> int:
        """
        Update a record dynamically.

        Args:
            record_id: id of record
            data: dictionary of column -> value

        Returns:
            number of affected rows
        """
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])

        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            WHERE id = %s
        """

        params = list(data.values())
        params.append(record_id)

        return DatabaseManager.execute(query, tuple(params))

    # -------------------------------------------------
    # Search helpers
    # -------------------------------------------------

    def find_one_by_field(
        self, field: str, value: Any
    ) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} WHERE {field} = %s LIMIT 1"
        return DatabaseManager.fetch_one(query, (value,))

    def find_many_by_field(
        self, field: str, value: Any
    ) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.table_name} WHERE {field} = %s"
        return DatabaseManager.fetch_all(query, (value,))