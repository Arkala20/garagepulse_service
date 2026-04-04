"""
repositories/role_repository.py

Repository for role-related database operations.
"""

from typing import Optional, Dict, List

from repositories.base_repository import BaseRepository
from database.db_manager import DatabaseManager


class RoleRepository(BaseRepository):
    """
    Repository for the roles table.
    """

    table_name = "roles"

    # -------------------------------------------------
    # Role lookup
    # -------------------------------------------------

    def get_by_role_code(self, role_code: str) -> Optional[Dict]:
        """
        Get role by role_code (OWNER, ADMIN, STAFF).
        """
        query = """
        SELECT *
        FROM roles
        WHERE role_code = %s
        LIMIT 1
        """

        return DatabaseManager.fetch_one(query, (role_code,))

    def get_all_roles(self) -> List[Dict]:
        """
        Get all roles.
        """
        query = """
        SELECT *
        FROM roles
        ORDER BY id
        """

        return DatabaseManager.fetch_all(query)

    # -------------------------------------------------
    # Helper
    # -------------------------------------------------

    def get_role_id(self, role_code: str) -> Optional[int]:
        """
        Return role ID from role_code.
        Useful when creating users.
        """

        role = self.get_by_role_code(role_code)

        if role:
            return role["id"]

        return None