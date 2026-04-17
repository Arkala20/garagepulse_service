"""
ui/pages/dashboard_page.py

Improved production-style Dashboard page for GaragePulse.

Updates:
- adjusted left sidebar width and spacing
- renamed Active Accounts -> Staff Management
- changed revenue card label to Revenue This Month
- formatted subtotal values in recent activity
- fixed logout button spacing and bottom placement
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from services.session_service import SessionService


logger = logging.getLogger(__name__)


class DashboardPage(tk.Frame):
    """
    Main dashboard page with modern sidebar and content area.
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

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.dashboard_controller = app.get_controller("dashboard")
        self.auth_controller = app.get_controller("auth")
        self.active_page_name = "dashboard"

        self.summary_vars: dict[str, tk.StringVar] = {
            "total_revenue": tk.StringVar(value="$0.00"),
            "active_work_orders": tk.StringVar(value="0"),
            "completed_today": tk.StringVar(value="0"),
            "pending_payments": tk.StringVar(value="0"),
        }

        self.staff_vars: dict[str, tk.StringVar] = {
            "total_staff": tk.StringVar(value="0"),
            "active_staff": tk.StringVar(value="0"),
            "inactive_staff": tk.StringVar(value="0"),
        }

        self.configure(bg=self.CONTENT_BG)
        self._build_layout()

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self, bg=self.SIDEBAR_BG, width=self.SIDEBAR_WIDTH)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.content = tk.Frame(self, bg=self.CONTENT_BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self._build_sidebar()
        self._build_header()
        self._build_summary_cards()
        self._build_lower_sections()

    def _build_sidebar(self) -> None:
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        top = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        top.pack(fill="x", padx=18, pady=(18, 10))

        tk.Label(
            top,
            text="GaragePulse",
            font=("Segoe UI", 21, "bold"),
            bg=self.SIDEBAR_BG,
            fg=self.SIDEBAR_TEXT,
        ).pack(anchor="w")

        user = SessionService.get_current_user() or {}
        full_name = user.get("full_name", "User")
        role_code = user.get("role_code", "")

        info_box = tk.Frame(self.sidebar, bg=self.SIDEBAR_ALT)
        info_box.pack(fill="x", padx=18, pady=(4, 12))

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

        nav = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        nav.pack(fill="x", padx=14)

        self._nav_button(nav, "dashboard", "Dashboard", self._refresh_dashboard)
        self._nav_button(nav, "customers", "Customers", self._go_customers)
        self._nav_button(nav, "vehicles", "Vehicles", self._go_vehicles)
        self._nav_button(nav, "work_orders", "Work Orders", self._go_work_orders)
        self._nav_button(nav, "invoices", "Invoices", self._go_invoices)
        self._nav_button(nav, "notifications", "Notifications", self._go_notifications)

        if SessionService.has_role("OWNER", "ADMIN"):
            self._nav_button(nav, "users", "Staff Management", self._go_users)
            self._nav_button(nav, "reports", "Reports", self._go_reports)

        tk.Frame(self.sidebar, bg="#334155", height=1).pack(fill="x", padx=18, pady=14)

        logout_frame = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        logout_frame.pack(side="bottom", fill="x", padx=18, pady=(10, 20))

        tk.Button(
            logout_frame,
            text="Logout",
            command=self._logout,
            font=("Segoe UI", 10, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            cursor="hand2",
        ).pack(fill="x")

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

    def _build_header(self) -> None:
        header = tk.Frame(self.content, bg=self.CONTENT_BG)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 14))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="Owner Dashboard",
            font=("Segoe UI", 22, "bold"),
            bg=self.CONTENT_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            header,
            text="Refresh Dashboard",
            command=self._refresh_dashboard,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="e")

    def _build_summary_cards(self) -> None:
        cards = tk.Frame(self.content, bg=self.CONTENT_BG)
        cards.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 18))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)

        card_data = [
            ("Revenue This Month", "total_revenue"),
            ("Active Work Orders", "active_work_orders"),
            ("Completed Today", "completed_today"),
            ("Pending Payments", "pending_payments"),
        ]

        for idx, (title, key) in enumerate(card_data):
            card = tk.Frame(cards, bg=self.CARD_BG, bd=0, relief="flat")
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))

            tk.Label(
                card,
                text=title,
                font=("Segoe UI", 11),
                bg=self.CARD_BG,
                fg=self.BODY_COLOR,
            ).pack(anchor="w", padx=18, pady=(18, 8))

            tk.Label(
                card,
                textvariable=self.summary_vars[key],
                font=("Segoe UI", 24, "bold"),
                bg=self.CARD_BG,
                fg=self.TITLE_COLOR,
            ).pack(anchor="w", padx=18, pady=(0, 18))

    def _build_lower_sections(self) -> None:
        lower = tk.Frame(self.content, bg=self.CONTENT_BG)
        lower.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=1)
        lower.grid_rowconfigure(0, weight=1)

        self._build_recent_activity(lower)
        self._build_staff_overview(lower)

    def _build_recent_activity(self, parent) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(
            card,
            text="Recent Activity",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).pack(anchor="w", padx=18, pady=(18, 12))

        table_frame = tk.Frame(card, bg=self.CARD_BG)
        table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        columns = (
            "work_order_id",
            "customer_name",
            "plate_number",
            "current_status",
            "subtotal",
        )

        self.activity_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12,
        )
        self.activity_tree.grid(row=0, column=0, sticky="nsew")

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        headings = {
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "plate_number": "Plate",
            "current_status": "Status",
            "subtotal": "Subtotal",
        }

        widths = {
            "work_order_id": 150,
            "customer_name": 180,
            "plate_number": 120,
            "current_status": 140,
            "subtotal": 120,
        }

        for col in columns:
            self.activity_tree.heading(col, text=headings[col])
            self.activity_tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.activity_tree.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.activity_tree.configure(yscrollcommand=scrollbar.set)

    def _build_staff_overview(self, parent) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            card,
            text="Staff Overview",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).pack(anchor="w", padx=18, pady=(18, 14))

        for title, key in [
            ("Total Staff", "total_staff"),
            ("Active Staff", "active_staff"),
            ("Inactive Staff", "inactive_staff"),
        ]:
            row = tk.Frame(card, bg=self.CARD_BG)
            row.pack(fill="x", padx=18, pady=8)

            tk.Label(
                row,
                text=title,
                font=("Segoe UI", 11),
                bg=self.CARD_BG,
                fg=self.BODY_COLOR,
            ).pack(side="left")

            tk.Label(
                row,
                textvariable=self.staff_vars[key],
                font=("Segoe UI", 16, "bold"),
                bg=self.CARD_BG,
                fg=self.TITLE_COLOR,
            ).pack(side="right")

    def _refresh_dashboard(self) -> None:
        self.active_page_name = "dashboard"
        self._build_sidebar()
        self._load_summary()
        self._load_recent_activity()
        self._load_staff_overview()

    def _load_summary(self) -> None:
        response = self.dashboard_controller.get_dashboard_summary()
        if not response.success:
            messagebox.showerror("Dashboard Error", response.message)
            return

        data = response.data or {}
        self.summary_vars["total_revenue"].set(f"${float(data.get('total_revenue', 0.0)):.2f}")
        self.summary_vars["active_work_orders"].set(str(data.get("active_work_orders", 0)))
        self.summary_vars["completed_today"].set(str(data.get("completed_today", 0)))
        self.summary_vars["pending_payments"].set(str(data.get("pending_payments", 0)))

    def _load_recent_activity(self) -> None:
        response = self.dashboard_controller.get_recent_activity(limit=10)
        if not response.success:
            messagebox.showerror("Dashboard Error", response.message)
            return

        self.activity_tree.delete(*self.activity_tree.get_children())

        for row in response.data or []:
            subtotal = float(row.get("subtotal", 0) or 0)
            self.activity_tree.insert(
                "",
                "end",
                values=(
                    row.get("work_order_id", ""),
                    row.get("customer_name", ""),
                    row.get("plate_number", ""),
                    row.get("current_status", ""),
                    f"${subtotal:.2f}",
                ),
            )

    def _load_staff_overview(self) -> None:
        response = self.dashboard_controller.get_staff_overview()
        if not response.success:
            messagebox.showerror("Dashboard Error", response.message)
            return

        data = response.data or {}
        self.staff_vars["total_staff"].set(str(data.get("total_staff", 0)))
        self.staff_vars["active_staff"].set(str(data.get("active_staff", 0)))
        self.staff_vars["inactive_staff"].set(str(data.get("inactive_staff", 0)))

    def _nav_to_page(self, name: str, module_path: str, class_name: str) -> None:
        self.active_page_name = name
        if name not in self.app.pages:
            module = __import__(module_path, fromlist=[class_name])
            page_class = getattr(module, class_name)
            self.app.register_page(name, page_class)
        self.app.show_page(name)

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

    def on_show(self) -> None:
        self.active_page_name = "dashboard"
        self._build_sidebar()
        self._load_summary()
        self._load_recent_activity()
        self._load_staff_overview()