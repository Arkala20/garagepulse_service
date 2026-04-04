"""
main.py

GaragePulse application entry point.

Responsibilities:
- Initialize logging
- Load environment variables
- Create AppWindow
- Register initial pages
- Start application
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from ui.app_window import AppWindow
from ui.pages.login_page import LoginPage


def setup_logging() -> None:
    """
    Configure application-wide logging.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def bootstrap_app() -> AppWindow:
    """
    Initialize the application window and register initial pages.
    """
    app = AppWindow()

    # Register initial pages
    app.register_page("login", LoginPage)

    # Start at login page
    app.show_page("login")

    return app


def main() -> None:
    """
    Application entry.
    """
    load_dotenv()
    setup_logging()

    logging.getLogger(__name__).info("Starting GaragePulse application...")

    app = bootstrap_app()
    app.start()


if __name__ == "__main__":
    main()