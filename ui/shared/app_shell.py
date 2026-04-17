"""
ui/shared/app_shell.py

Reusable application shell for GaragePulse pages.

Provides:
- dark professional sidebar
- active menu highlighting
- user info panel
- common header area
- logout handling
- fixed sidebar layout so logout stays visible
- aligned with dashboard sidebar sizing and spacing
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from services.session_service import SessionService


class AppShell(tk.Frame):
    """
    Reusable application shell with shared sidebar and content area.
    """

    SIDEBAR_WIDTH = 200

    SIDEBAR_BG = "#0f172a"
    SIDEBAR_ALT = "#1e293b"
    SIDEBAR_ACTIVE = "#2563eb"
    SIDEBAR_TEXT = "#f8fafc"
    SIDEBAR_MUTED = "#cbd5e1"
    CONTENT_BG = "#f1f5f9"
    CARD_BG = "#ffffff"
    TITLE_COLOR = "#0f172a"
    BODY_COLOR = "#475569"
    DANGER_BG = "#dc2626"
    DANGER_ACTIVE = "#b91c1c"

    def __init__(self, parent, app, active_page_name: str, page_title: str) -> None:
        super().__init__(parent, bg=self.CONTENT_BG)

        self.app = app
        self.active_page_name = active_page_name
        self.page_title = page_title
        self.auth_controller = app.get_controller("auth")

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self, bg=self.SIDEBAR_BG, width=self.SIDEBAR_WIDTH)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(1, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.main = tk.Frame(self, bg=self.CONTENT_BG)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.header = tk.Frame(self.main, bg=self.CONTENT_BG)
        self.header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 14))
        self.header.grid_columnconfigure(0, weight=1)

        self.content = tk.Frame(self.main, bg=self.CONTENT_BG)
        self.content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_header()

    def _build_sidebar(self) -> None:
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        top_container = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        top_container.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))

        tk.Label(
            top_container,
            text="GaragePulse",
            font=("Segoe UI", 21, "bold"),
            bg=self.SIDEBAR_BG,
            fg=self.SIDEBAR_TEXT,
        ).pack(anchor="w")

        user = SessionService.get_current_user() or {}
        full_name = user.get("full_name", "User")
        role_code = user.get("role_code", "")

        info_box = tk.Frame(top_container, bg=self.SIDEBAR_ALT)
        info_box.pack(fill="x", pady=(12, 0))

        tk.Label(
            info_box,
            text=full_name,
            font=("Segoe UI", 13, "bold"),
            bg=self.SIDEBAR_ALT,
            fg=self.SIDEBAR_TEXT,
        ).pack(anchor="w", padx=14, pady=(12, 3))

        tk.Label(
            info_box,
            text=role_code,
            font=("Segoe UI", 10),
            bg=self.SIDEBAR_ALT,
            fg=self.SIDEBAR_MUTED,
        ).pack(anchor="w", padx=14, pady=(0, 12))

        nav_container = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        nav_container.grid(row=1, column=0, sticky="nsew", padx=14)
        nav_container.grid_columnconfigure(0, weight=1)

        self._nav_button(nav_container, "dashboard", "Dashboard", self._go_dashboard)
        self._nav_button(nav_container, "customers", "Customers", self._go_customers)
        self._nav_button(nav_container, "vehicles", "Vehicles", self._go_vehicles)
        self._nav_button(nav_container, "work_orders", "Work Orders", self._go_work_orders)
        self._nav_button(nav_container, "invoices", "Invoices", self._go_invoices)
        self._nav_button(nav_container, "notifications", "Notifications", self._go_notifications)

        if SessionService.has_role("OWNER", "ADMIN"):
            self._nav_button(nav_container, "users", "Staff Management", self._go_users)
            self._nav_button(nav_container, "reports", "Reports", self._go_reports)

        bottom_container = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        bottom_container.grid(row=2, column=0, sticky="ew", padx=18, pady=(10, 20))

        tk.Frame(bottom_container, bg="#334155", height=1).pack(fill="x", pady=(0, 14))

        tk.Button(
            bottom_container,
            text="Logout",
            command=self._logout,
            font=("Segoe UI", 10, "bold"),
            bg=self.DANGER_BG,
            fg="white",
            activebackground=self.DANGER_ACTIVE,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            cursor="hand2",
        ).pack(fill="x")

    def _build_header(self) -> None:
        tk.Label(
            self.header,
            text=self.page_title,
            font=("Segoe UI", 22, "bold"),
            bg=self.CONTENT_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            self.header,
            text="Back to Dashboard",
            command=self._go_dashboard,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="e")

    def _nav_button(self, parent, page_name: str, text: str, command) -> None:
        is_active = self.active_page_name == page_name
        bg = self.SIDEBAR_ACTIVE if is_active else self.SIDEBAR_BG
        fg = self.SIDEBAR_TEXT if is_active else self.SIDEBAR_MUTED

        tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold" if is_active else "normal"),
            bg=bg,
            fg=fg,
            activebackground=self.SIDEBAR_ACTIVE,
            activeforeground="white",
            relief="flat",
            bd=0,
            anchor="w",
            padx=18,
            pady=11,
            cursor="hand2",
        ).pack(fill="x", pady=4)

    def _nav_to_page(self, name: str, module_path: str, class_name: str) -> None:
        if name not in self.app.pages:
            module = __import__(module_path, fromlist=[class_name])
            page_class = getattr(module, class_name)
            self.app.register_page(name, page_class)
        self.app.show_page(name)

    def _go_dashboard(self) -> None:
        self._nav_to_page("dashboard", "ui.pages.dashboard_page", "DashboardPage")

    def _go_customers(self) -> None:
        self._nav_to_page("customers", "ui.pages.customers_page", "CustomersPage")

    def _go_vehicles(self) -> None:
        self._nav_to_page("vehicles", "ui.pages.vehicles_page", "VehiclesPage")

    def _go_work_orders(self) -> None:
        self._nav_to_page("work_orders", "ui.pages.work_orders_page", "WorkOrdersPage")

    def _go_invoices(self) -> None:
        self._nav_to_page("invoices", "ui.pages.invoices_page", "InvoicesPage")

    def _go_notifications(self) -> None:
        self._nav_to_page("notifications", "ui.pages.notifications_page", "NotificationsPage")

    def _go_users(self) -> None:
        self._nav_to_page("users", "ui.pages.users_page", "UsersPage")

    def _go_reports(self) -> None:
        self._nav_to_page("reports", "ui.pages.reports_page", "ReportsPage")

    def _logout(self) -> None:
        response = self.auth_controller.logout()
        if not response.success:
            messagebox.showerror("Logout Error", response.message)
            return
        self.app.logout_and_redirect("login")