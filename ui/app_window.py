"""
ui/app_window.py

Main Tkinter application window for GaragePulse.
Responsible for:
- root window setup
- page/frame switching
- controller initialization
- session-aware navigation hooks

UI stays thin. Business logic remains in controllers/services.
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Type

from controllers.auth_controller import AuthController
from controllers.customer_controller import CustomerController
from controllers.dashboard_controller import DashboardController
from controllers.invoice_controller import InvoiceController
from controllers.notification_controller import NotificationController
from controllers.user_controller import UserController
from controllers.vehicle_controller import VehicleController
from controllers.work_order_controller import WorkOrderController
from services.session_service import SessionService


logger = logging.getLogger(__name__)


class AppWindow(tk.Tk):
    """
    Main GaragePulse desktop application window.
    Manages page registration, navigation, and controller access.
    """

    def __init__(self) -> None:
        super().__init__()

        self.title("GaragePulse - Auto Service Management System")
        self.geometry("1280x800")
        self.minsize(1100, 700)

        self.style = ttk.Style()
        self._configure_theme()

        self.controllers = self._build_controllers()

        self.page_container = ttk.Frame(self)
        self.page_container.pack(fill="both", expand=True)

        self.pages: Dict[str, ttk.Frame] = {}
        self.current_page: Optional[ttk.Frame] = None

        logger.info("AppWindow initialized successfully.")

    def _configure_theme(self) -> None:
        """
        Configure a clean ttk theme for the app shell.
        """
        try:
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception as exc:
            logger.warning("Failed to apply ttk theme: %s", exc)

        self.configure(bg="#f5f6f8")

        self.style.configure("App.TFrame", background="#f5f6f8")
        self.style.configure("Card.TFrame", background="#ffffff")
        self.style.configure(
            "PageTitle.TLabel",
            font=("Segoe UI", 18, "bold"),
            background="#f5f6f8",
            foreground="#1f2937",
        )
        self.style.configure(
            "Body.TLabel",
            font=("Segoe UI", 10),
            background="#f5f6f8",
            foreground="#374151",
        )
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=10,
        )

    def _build_controllers(self) -> Dict[str, object]:
        """
        Initialize all controllers once and expose them to pages.
        """
        return {
            "auth": AuthController(),
            "user": UserController(),
            "customer": CustomerController(),
            "vehicle": VehicleController(),
            "work_order": WorkOrderController(),
            "invoice": InvoiceController(),
            "notification": NotificationController(),
            "dashboard": DashboardController(),
        }

    def get_controller(self, name: str) -> object:
        """
        Return a registered controller by name.
        """
        if name not in self.controllers:
            raise KeyError(f"Controller '{name}' is not registered.")
        return self.controllers[name]

    def register_page(
        self,
        page_name: str,
        page_class: Type[ttk.Frame],
    ) -> ttk.Frame:
        """
        Create and register a page instance.

        Args:
            page_name: unique page key
            page_class: Frame class

        Returns:
            instantiated page
        """
        if page_name in self.pages:
            return self.pages[page_name]

        page = page_class(self.page_container, self)
        self.pages[page_name] = page
        logger.info("Registered page: %s", page_name)
        return page

    def show_page(self, page_name: str) -> None:
        """
        Show a registered page and hide the previous one.
        """
        page = self.pages.get(page_name)
        if not page:
            raise KeyError(f"Page '{page_name}' is not registered.")

        if self.current_page is not None:
            self.current_page.pack_forget()

        self.current_page = page
        self.current_page.pack(fill="both", expand=True)

        on_show = getattr(self.current_page, "on_show", None)
        if callable(on_show):
            on_show()

        logger.info("Showing page: %s", page_name)

    def destroy_page(self, page_name: str) -> None:
        """
        Remove a page from memory.
        Useful for rebuilding pages after logout/login if needed.
        """
        page = self.pages.pop(page_name, None)
        if page is not None:
            page.destroy()
            logger.info("Destroyed page: %s", page_name)

    def clear_registered_pages(self) -> None:
        """
        Destroy all registered pages.
        """
        for page_name in list(self.pages.keys()):
            self.destroy_page(page_name)

        self.current_page = None

    def logout_and_redirect(self, login_page_name: str = "login") -> None:
        """
        Clear session and return to login page.
        """
        SessionService.clear_session()
        logger.info("Session cleared from AppWindow logout.")

        for page_name in list(self.pages.keys()):
            if page_name != login_page_name:
                self.destroy_page(page_name)

        self.show_page(login_page_name)

    def start(self) -> None:
        """
        Start Tkinter main loop.
        """
        logger.info("Starting Tkinter main loop.")
        self.mainloop()