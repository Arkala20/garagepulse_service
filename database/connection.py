"""
database/connection.py

Database connection manager for GaragePulse.
Handles creation and reuse of MySQL connections.
"""

import mysql.connector
from mysql.connector import pooling, Error
import logging

from config.settings import settings


logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Manages MySQL connection pooling for the application.
    """

    _connection_pool = None

    @classmethod
    def initialize_pool(cls):
        """
        Initialize the MySQL connection pool.
        Should be called once during application startup.
        """
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pooling.MySQLConnectionPool(
                    pool_name="garagepulse_pool",
                    pool_size=10,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                )

                logger.info("MySQL connection pool initialized.")

            except Error as e:
                logger.error(f"Failed to initialize MySQL pool: {e}")
                raise

    @classmethod
    def get_connection(cls):
        """
        Retrieve a connection from the pool.
        """
        try:
            if cls._connection_pool is None:
                cls.initialize_pool()

            connection = cls._connection_pool.get_connection()

            if connection.is_connected():
                return connection

        except Error as e:
            logger.error(f"Error getting DB connection: {e}")
            raise

    @staticmethod
    def close_connection(connection):
        """
        Return connection back to the pool.
        """
        try:
            if connection and connection.is_connected():
                connection.close()
        except Error as e:
            logger.warning(f"Error closing DB connection: {e}")