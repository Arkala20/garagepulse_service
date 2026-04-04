"""
repositories/password_reset_repository.py

Repository for password reset operations.
Aligned with schema.sql fields:
- reset_token
- requested_via
- expires_at
- used_at
"""

from typing import Dict, Optional, List

from database.db_manager import DatabaseManager
from repositories.base_repository import BaseRepository


class PasswordResetRepository(BaseRepository):
    """
    Repository for the password_resets table.
    """

    table_name = "password_resets"

    def create_reset_request(self, data: Dict) -> int:
        """
        Create a password reset request.

        Expected fields:
            user_id
            reset_token
            requested_via
            expires_at
        """
        return self.insert(data)

    def get_by_reset_token(self, reset_token: str) -> Optional[Dict]:
        """
        Retrieve a reset request by raw reset token.
        """
        query = """
        SELECT *
        FROM password_resets
        WHERE reset_token = %s
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (reset_token,))

    def get_valid_token(self, reset_token: str) -> Optional[Dict]:
        """
        Return a valid token record:
        - token matches
        - not already used
        - not expired
        """
        query = """
        SELECT *
        FROM password_resets
        WHERE reset_token = %s
          AND used_at IS NULL
          AND expires_at > NOW()
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (reset_token,))

    def mark_as_used(self, reset_id: int) -> int:
        """
        Mark a reset token as used.
        """
        query = """
        UPDATE password_resets
        SET used_at = NOW()
        WHERE id = %s
        """
        return DatabaseManager.execute(query, (reset_id,))

    def invalidate_user_tokens(self, user_id: int) -> int:
        """
        Invalidate all currently unused tokens for a user.
        Used before creating a new reset request.
        """
        query = """
        UPDATE password_resets
        SET used_at = NOW()
        WHERE user_id = %s
          AND used_at IS NULL
        """
        return DatabaseManager.execute(query, (user_id,))

    def get_latest_active_request_for_user(self, user_id: int) -> Optional[Dict]:
        """
        Return the latest unused, unexpired reset request for a user.
        """
        query = """
        SELECT *
        FROM password_resets
        WHERE user_id = %s
          AND used_at IS NULL
          AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """
        return DatabaseManager.fetch_one(query, (user_id,))

    def get_requests_by_user_id(self, user_id: int) -> List[Dict]:
        """
        Return all reset requests for a user, newest first.
        """
        query = """
        SELECT *
        FROM password_resets
        WHERE user_id = %s
        ORDER BY created_at DESC
        """
        return DatabaseManager.fetch_all(query, (user_id,))

    def delete_expired_tokens(self) -> int:
        """
        Delete expired reset requests.
        Optional maintenance helper.
        """
        query = """
        DELETE FROM password_resets
        WHERE expires_at < NOW()
        """
        return DatabaseManager.execute(query)