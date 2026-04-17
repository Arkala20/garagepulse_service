"""
repositories/password_reset_repository.py

Repository for password reset operations.
"""

from typing import Dict, Optional, List

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class PasswordResetRepository(BaseRepository):
    table_name = "password_resets"

    def create_reset_request(self, data: Dict) -> int:
        return self.insert(data)

    def get_database_now(self) -> Optional[Dict]:
        query = "SELECT NOW() AS db_now"
        return DatabaseManager.fetch_one(query)

    def get_by_reset_token(self, reset_token: str) -> Optional[Dict]:
        query = """
        SELECT *,
               NOW() AS db_now
        FROM password_resets
        WHERE reset_token = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (reset_token,))

    def get_valid_token(self, reset_token: str) -> Optional[Dict]:
        query = """
        SELECT *,
               NOW() AS db_now
        FROM password_resets
        WHERE reset_token = %s
          AND used_at IS NULL
          AND expires_at > NOW()
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (reset_token,))

    def mark_as_used(self, reset_id: int) -> int:
        query = """
        UPDATE password_resets
        SET used_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (reset_id,))

    def invalidate_user_tokens(self, user_id: int) -> int:
        query = """
        UPDATE password_resets
        SET used_at = NOW()
        WHERE user_id = %s
          AND used_at IS NULL
        """
        return DatabaseManager.execute(query, (user_id,))

    def get_latest_active_request_for_user(self, user_id: int) -> Optional[Dict]:
        query = """
        SELECT *,
               NOW() AS db_now
        FROM password_resets
        WHERE user_id = %s
          AND used_at IS NULL
          AND expires_at > NOW()
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (user_id,))

    def get_requests_by_user_id(self, user_id: int) -> List[Dict]:
        query = """
        SELECT *
        FROM password_resets
        WHERE user_id = %s
        ORDER BY created_at DESC, id DESC
        """
        return DatabaseManager.fetch_all(query, (user_id,))

    def delete_expired_tokens(self) -> int:
        query = """
        DELETE FROM password_resets
        WHERE expires_at < NOW()
        """
        return DatabaseManager.execute(query)