"""
repositories/user_repository.py

Repository for user-related database operations.
Supports authentication, staff/admin account workflows,
activation management, and role-aware user listing.
"""

from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    Repository for the users table.
    """

    table_name = "users"

    def get_by_email(self, email: str) -> Optional[Dict]:
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE LOWER(u.email) = LOWER(%s)
          AND u.is_deleted = 0
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (email,))

    def get_by_username(self, username: str) -> Optional[Dict]:
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE LOWER(u.username) = LOWER(%s)
          AND u.is_deleted = 0
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (username,))

    def get_by_email_or_username(self, identifier: str) -> Optional[Dict]:
        """
        Supports login using email OR username.
        Includes role details for authorization and password reset logic.
        """
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE (LOWER(u.email) = LOWER(%s) OR LOWER(u.username) = LOWER(%s))
          AND u.is_deleted = 0
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (identifier, identifier))

    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get a single user with role details by ID.
        """
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
          AND u.is_deleted = 0
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (user_id,))

    def create_user(self, data: Dict) -> int:
        """
        Create a new user.
        """
        return self.insert(data)

    def activate_user(self, user_id: int) -> int:
        query = """
        UPDATE users
        SET is_active = 1,
            updated_at = NOW()
        WHERE id = %s
          AND is_deleted = 0
        """
        return DatabaseManager.execute(query, (user_id,))

    def deactivate_user(self, user_id: int) -> int:
        query = """
        UPDATE users
        SET is_active = 0,
            updated_at = NOW()
        WHERE id = %s
          AND is_deleted = 0
        """
        return DatabaseManager.execute(query, (user_id,))

    def update_password(self, user_id: int, password_hash: str) -> int:
        query = """
        UPDATE users
        SET password_hash = %s,
            updated_at = NOW()
        WHERE id = %s
          AND is_deleted = 0
        """
        return DatabaseManager.execute(query, (password_hash, user_id))

    def update_last_login(self, user_id: int) -> int:
        query = """
        UPDATE users
        SET last_login_at = NOW(),
            updated_at = NOW()
        WHERE id = %s
          AND is_deleted = 0
        """
        return DatabaseManager.execute(query, (user_id,))

    def exists_by_email(self, email: str) -> bool:
        query = """
        SELECT id
        FROM users
        WHERE LOWER(email) = LOWER(%s)
          AND is_deleted = 0
        LIMIT 1
        """
        result = DatabaseManager.fetch_one(query, (email,))
        return result is not None

    def exists_by_username(self, username: str) -> bool:
        query = """
        SELECT id
        FROM users
        WHERE LOWER(username) = LOWER(%s)
          AND is_deleted = 0
        LIMIT 1
        """
        result = DatabaseManager.fetch_one(query, (username,))
        return result is not None

    def get_all_staff(self) -> List[Dict]:
        """
        Return non-deleted operational users with role details.
        """
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.is_deleted = 0
          AND r.role_code IN ('OWNER', 'ADMIN', 'STAFF')
        ORDER BY u.created_at DESC, u.id DESC
        """
        return DatabaseManager.fetch_all(query)

    def get_active_users(self) -> List[Dict]:
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.is_active = 1
          AND u.is_deleted = 0
        ORDER BY u.created_at DESC, u.id DESC
        """
        return DatabaseManager.fetch_all(query)

    def get_inactive_users(self) -> List[Dict]:
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.is_active = 0
          AND u.is_deleted = 0
        ORDER BY u.created_at DESC, u.id DESC
        """
        return DatabaseManager.fetch_all(query)

    def get_users_by_role_code(self, role_code: str) -> List[Dict]:
        """
        Return users filtered by a specific role code.
        """
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE r.role_code = %s
          AND u.is_deleted = 0
        ORDER BY u.created_at DESC, u.id DESC
        """
        return DatabaseManager.fetch_all(query, (role_code,))

    def soft_delete_user(self, user_id: int) -> int:
        query = """
        UPDATE users
        SET is_deleted = 1,
            updated_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (user_id,))

    def get_user_with_role(self, user_id: int) -> Optional[Dict]:
        """
        Get a single user with role information.
        """
        query = """
        SELECT
            u.*,
            r.role_name,
            r.role_code
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = %s
          AND u.is_deleted = 0
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (user_id,))