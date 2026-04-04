"""
app.py

GaragePulse Application Entry Point.

Responsibilities:
- Initialize logging
- Initialize database connection pool
- Test database connectivity
- Start the desktop UI application
"""

import logging
import sys

from config.logging_config import setup_logging
from database.connection import DatabaseConnection
from database.db_manager import DatabaseManager
from config.settings import settings


logger = logging.getLogger(__name__)


def initialize_application():
    """
    Initialize core services before launching UI.
    """
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    try:
        # Initialize DB connection pool
        DatabaseConnection.initialize_pool()

        # Verify database connection
        if DatabaseManager.test_connection():
            logger.info("Database connection verified successfully.")

    except Exception as e:
        logger.exception("Failed to initialize application: %s", e)
        sys.exit(1)


def start_ui():
    """
    Placeholder for UI startup.

    UI will be implemented later in ui/app_window.py.
    """
    logger.info("UI initialization placeholder.")

    print(
        f"""
========================================
 {settings.APP_NAME} v{settings.APP_VERSION}
 Auto Service Management System
========================================
Application initialized successfully.
UI will be started once UI modules are built.
"""
    )


def main():
    """
    Main application runner.
    """

    # Setup logging first
    setup_logging()

    logger.info("Initializing application...")

    initialize_application()

    # Start UI layer (placeholder for now)
    start_ui()


if __name__ == "__main__":
    main()