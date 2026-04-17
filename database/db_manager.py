"""
database/db_manager.py

Low-level database helper for GaragePulse.
Provides reusable query execution methods for repositories.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, Iterable, List, Optional

from mysql.connector import Error
from mysql.connector.cursor import MySQLCursorDict

from database.connection import DatabaseConnection
from config.settings import settings
print("DB DEBUG:", settings.DB_HOST, settings.DB_NAME, settings.DB_USER)


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Reusable DB helper for executing queries safely.

    Repositories should use this class instead of directly managing
    connection/cursor lifecycle for every operation.
    """

    @staticmethod
    @contextmanager
    def get_cursor(
        dictionary: bool = True,
    ) -> Generator[tuple[Any, MySQLCursorDict], None, None]:
        """
        Context manager that yields a connection and cursor, then safely closes both.

        Args:
            dictionary: If True, returns rows as dictionaries.

        Yields:
            tuple: (connection, cursor)
        """
        connection = None
        cursor = None
        try:
            connection = DatabaseConnection.get_connection()
            cursor = connection.cursor(dictionary=dictionary)
            yield connection, cursor
        except Error as exc:
            logger.exception("Database cursor error: %s", exc)
            raise
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Error as exc:
                    logger.warning("Failed to close cursor: %s", exc)

            if connection is not None:
                DatabaseConnection.close_connection(connection)

    @classmethod
    def fetch_one(
        cls,
        query: str,
        params: Optional[Iterable[Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a SELECT query and return a single row.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            A dictionary row or None
        """
        try:
            with cls.get_cursor(dictionary=True) as (_, cursor):
                cursor.execute(query, params or ())
                return cursor.fetchone()
        except Error as exc:
            logger.exception("fetch_one failed: %s", exc)
            raise

    @classmethod
    def fetch_all(
        cls,
        query: str,
        params: Optional[Iterable[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return all rows.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of dictionary rows
        """
        try:
            with cls.get_cursor(dictionary=True) as (_, cursor):
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except Error as exc:
            logger.exception("fetch_all failed: %s", exc)
            raise

    @classmethod
    def execute(
        cls,
        query: str,
        params: Optional[Iterable[Any]] = None,
        *,
        commit: bool = True,
    ) -> int:
        """
        Execute INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query
            params: Query parameters
            commit: Whether to commit transaction

        Returns:
            Number of affected rows
        """
        try:
            with cls.get_cursor(dictionary=False) as (connection, cursor):
                cursor.execute(query, params or ())
                affected_rows = cursor.rowcount

                if commit:
                    connection.commit()

                return affected_rows
        except Error as exc:
            logger.exception("execute failed: %s", exc)
            raise

    @classmethod
    def execute_and_get_last_id(
        cls,
        query: str,
        params: Optional[Iterable[Any]] = None,
    ) -> int:
        """
        Execute INSERT query and return inserted row ID.

        Args:
            query: SQL insert query
            params: Query parameters

        Returns:
            Last inserted ID
        """
        try:
            with cls.get_cursor(dictionary=False) as (connection, cursor):
                cursor.execute(query, params or ())
                connection.commit()
                return int(cursor.lastrowid)
        except Error as exc:
            logger.exception("execute_and_get_last_id failed: %s", exc)
            raise

    @classmethod
    def execute_many(
        cls,
        query: str,
        param_list: List[Iterable[Any]],
        *,
        commit: bool = True,
    ) -> int:
        """
        Execute a batch operation using executemany.

        Args:
            query: SQL query
            param_list: List of parameter tuples/lists
            commit: Whether to commit

        Returns:
            Number of affected rows
        """
        try:
            with cls.get_cursor(dictionary=False) as (connection, cursor):
                cursor.executemany(query, param_list)
                affected_rows = cursor.rowcount

                if commit:
                    connection.commit()

                return affected_rows
        except Error as exc:
            logger.exception("execute_many failed: %s", exc)
            raise

    @classmethod
    def execute_transaction(
        cls,
        statements: List[Dict[str, Any]],
    ) -> bool:
        """
        Execute multiple SQL statements in a single transaction.

        Each statement dict must contain:
            {
                "query": "...",
                "params": (...)
            }

        Args:
            statements: List of SQL statements

        Returns:
            True if committed successfully

        Raises:
            Exception if transaction fails
        """
        connection = None
        cursor = None

        try:
            connection = DatabaseConnection.get_connection()
            cursor = connection.cursor(dictionary=False)

            for statement in statements:
                query = statement["query"]
                params = statement.get("params", ())
                cursor.execute(query, params)

            connection.commit()
            return True

        except Error as exc:
            if connection is not None:
                connection.rollback()

            logger.exception("Transaction failed and rolled back: %s", exc)
            raise

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Error as exc:
                    logger.warning("Failed to close transaction cursor: %s", exc)

            if connection is not None:
                DatabaseConnection.close_connection(connection)

    @classmethod
    def test_connection(cls) -> bool:
        """
        Simple health check for database connection.

        Returns:
            True if DB is reachable, else raises exception
        """
        result = cls.fetch_one("SELECT 1 AS ok;")
        return bool(result and result.get("ok") == 1)