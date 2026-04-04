"""
ui/pages/dashboard_page.py

Production-style Dashboard page for GaragePulse.

Upgrades from prototype:
- role-aware sidebar
- summary cards
- recent activity section
- staff overview section
- navigation to core modules
- owner/admin-only entries for Active Accounts and Reports
"""

from __future__ import annotations

import logging
from tkinter import messagebox, ttk

from services.session_service import SessionService


logger = logging.getLogger(__name__)


class DashboardPage(ttk.Frame):
    """
    Main dashboard page with sidebar and content area.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.dashboard_controller = app.get_controller("dashboard")
        self.auth_controller = app.get_controller("auth")

        self.summary_vars = {
            "total_revenue": ttk.Label(),
            "active_work_orders": ttk.Label(),
            "completed_today": ttk.Label(),
            "pending_payments": ttk.Label(),
        }

        self.staff_vars = {
            "total_staff": ttk.Label(),
            "active_staff": ttk.Label(),
            "inactive_staff": ttk.Label(),
        }

        self._build_layout()

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="Card.TFrame", width=240, padding=16)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.content = ttk.Frame(self, style="App.TFrame", padding=20)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(2, weight=1)

        self._build_sidebar()
        self._build_header()
        self._build_summary_cards()
        self._build_lower_sections()

    def _build_sidebar(self) -> None:
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        ttk.Label(
            self.sidebar,
            text="GaragePulse",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(4, 16))

        user = SessionService.get_current_user() or {}
        full_name = user.get("full_name", "User")
        role_code = user.get("role_code", "")

        ttk.Label(
            self.sidebar,
            text=full_name,
            style="Body.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            self.sidebar,
            text=role_code,
            style="Body.TLabel",
        ).pack(anchor="w", pady=(0, 16))

        self._nav_button("Dashboard", self._refresh_dashboard)
        self._nav_button("Customers", self._go_customers)
        self._nav_button("Vehicles", self._go_vehicles)
        self._nav_button("Work Orders", self._go_work_orders)
        self._nav_button("Invoices", self._go_invoices)
        self._nav_button("Notifications", self._go_notifications)

        if SessionService.has_role("OWNER", "ADMIN"):
            self._nav_button("Active Accounts", self._go_users)
            self._nav_button("Reports", self._go_reports)

        ttk.Separator(self.sidebar).pack(fill="x", pady=12)

        ttk.Button(
            self.sidebar,
            text="Logout",
            command=self._logout,
        ).pack(fill="x", pady=(8, 0))

    def _build_header(self) -> None:
        header = ttk.Frame(self.content, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Owner Dashboard",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            header,
            text="Refresh Dashboard",
            command=self._refresh_dashboard,
        ).grid(row=0, column=1, sticky="e")

    def _build_summary_cards(self) -> None:
        cards_frame = ttk.Frame(self.content, style="App.TFrame")
        cards_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        cards = [
            ("Total Revenue", "total_revenue"),
            ("Active Work Orders", "active_work_orders"),
            ("Completed Today", "completed_today"),
            ("Pending Payments", "pending_payments"),
        ]

        for idx, (title, key) in enumerate(cards):
            card = ttk.Frame(cards_frame, style="Card.TFrame", padding=18)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0))

            ttk.Label(
                card,
                text=title,
                style="Body.TLabel",
            ).pack(anchor="w")

            value_label = ttk.Label(
                card,
                text="--",
                font=("Segoe UI", 18, "bold"),
            )
            value_label.pack(anchor="w", pady=(10, 0))
            self.summary_vars[key] = value_label

    def _build_lower_sections(self) -> None:
        lower = ttk.Frame(self.content, style="App.TFrame")
        lower.grid(row=2, column=0, sticky="nsew")
        lower.columnconfigure(0, weight=2)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(0, weight=1)

        self._build_recent_activity(lower)
        self._build_staff_overview(lower)

    def _build_recent_activity(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        ttk.Label(
            card,
            text="Recent Activity",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        columns = (
            "work_order_id",
            "customer_name",
            "plate_number",
            "current_status",
            "subtotal",
        )

        self.activity_tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            height=12,
        )
        self.activity_tree.grid(row=1, column=0, sticky="nsew")

        headings = {
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "plate_number": "Plate",
            "current_status": "Status",
            "subtotal": "Subtotal",
        }

        widths = {
            "work_order_id": 130,
            "customer_name": 150,
            "plate_number": 110,
            "current_status": 110,
            "subtotal": 100,
        }

        for col in columns:
            self.activity_tree.heading(col, text=headings[col])
            self.activity_tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(
            card,
            orient="vertical",
            command=self.activity_tree.yview,
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.activity_tree.configure(yscrollcommand=scrollbar.set)

    def _build_staff_overview(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        card.grid(row=0, column=1, sticky="nsew")
        card.columnconfigure(0, weight=1)

        ttk.Label(
            card,
            text="Staff Overview",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        labels = [
            ("Total Staff", "total_staff"),
            ("Active Staff", "active_staff"),
            ("Inactive Staff", "inactive_staff"),
        ]

        for idx, (title, key) in enumerate(labels, start=1):
            row = ttk.Frame(card, style="Card.TFrame")
            row.grid(row=idx, column=0, sticky="ew", pady=6)
            row.columnconfigure(1, weight=1)

            ttk.Label(
                row,
                text=title,
                style="Body.TLabel",
            ).grid(row=0, column=0, sticky="w")

            value_label = ttk.Label(
                row,
                text="--",
                font=("Segoe UI", 12, "bold"),
            )
            value_label.grid(row=0, column=1, sticky="e")
            self.staff_vars[key] = value_label

    def _refresh_dashboard(self) -> None:
        self._load_summary()
        self._load_recent_activity()
        self._load_staff_overview()

    def _load_summary(self) -> None:
        response = self.dashboard_controller.get_dashboard_summary()

        if not response.success:
            messagebox.showerror("Dashboard Error", response.message)
            return

        data = response.data or {}

        self.summary_vars["total_revenue"].configure(
            text=f"${float(data.get('total_revenue', 0.0)):.2f}"
        )
        self.summary_vars["active_work_orders"].configure(
            text=str(data.get("active_work_orders", 0))
        )
        self.summary_vars["completed_today"].configure(
            text=str(data.get("completed_today", 0))
        )
        self.summary_vars["pending_payments"].configure(
            text=str(data.get("pending_payments", 0))
        )

    def _load_recent_activity(self) -> None:
        response = self.dashboard_controller.get_recent_activity(limit=10)

        if not response.success:
            messagebox.showerror("Dashboard Error", response.message)
            return

        self.activity_tree.delete(*self.activity_tree.get_children())

        for row in response.data or []:
            self.activity_tree.insert(
                "",
                "end",
                values=(
                    row.get("work_order_id", ""),
                    row.get("customer_name", ""),
                    row.get("plate_number", ""),
                    row.get("current_status", ""),
                    row.get("subtotal", 0),
                ),
            )

    def _load_staff_overview(self) -> None:
        response = self.dashboard_controller.get_staff_overview()

        if not response.success:
            messagebox.showerror("Dashboard Error", response.message)
            return

        data = response.data or {}

        self.staff_vars["total_staff"].configure(
            text=str(data.get("total_staff", 0))
        )
        self.staff_vars["active_staff"].configure(
            text=str(data.get("active_staff", 0))
        )
        self.staff_vars["inactive_staff"].configure(
            text=str(data.get("inactive_staff", 0))
        )

    def _nav_to_page(self, name: str, module_path: str, class_name: str) -> None:
        if name not in self.app.pages:
            module = __import__(module_path, fromlist=[class_name])
            page_class = getattr(module, class_name)
            self.app.register_page(name, page_class)

        self.app.show_page(name)

    def _nav_button(self, text: str, command) -> None:
        ttk.Button(
            self.sidebar,
            text=text,
            command=command,
        ).pack(fill="x", pady=4)

    def _go_customers(self) -> None:
        self._nav_to_page("customers", "ui.pages.customers_page", "CustomersPage")

    def _go_vehicles(self) -> None:
        self._nav_to_page("vehicles", "ui.pages.vehicles_page", "VehiclesPage")

    def _go_work_orders(self) -> None:
        self._nav_to_page("work_orders", "ui.pages.work_orders_page", "WorkOrdersPage")

    def _go_invoices(self) -> None:
        self._nav_to_page("invoices", "ui.pages.invoices_page", "InvoicesPage")

    def _go_notifications(self) -> None:
        self._nav_to_page(
            "notifications",
            "ui.pages.notifications_page",
            "NotificationsPage",
        )

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
        self._build_sidebar()
        self._refresh_dashboard()