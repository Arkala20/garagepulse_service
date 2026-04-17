"""
ui/pages/reports_page.py

GaragePulse Reports page
- Uses shared app shell/sidebar
- Loads live data from controllers
- Production-style report views
- Fixes report revenue mismatch with dashboard
"""

from __future__ import annotations

import csv
import importlib
import logging
import tkinter as tk
from collections import defaultdict
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class ReportsPage(AppShell):
    """
    Live reports page using the same shell/sidebar behavior as the rest of the app.
    """

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="reports",
            page_title="Reports",
        )

        self.customer_controller = app.get_controller("customer")
        self.vehicle_controller = app.get_controller("vehicle")
        self.work_order_controller = app.get_controller("work_order")
        self.invoice_controller = app.get_controller("invoice")
        self.user_controller = app.get_controller("user")

        self.timeframe_var = tk.StringVar(value="All Time")
        self.selected_view = tk.StringVar(value="Revenue Summary")

        self.card_1_label = tk.StringVar(value="Revenue")
        self.card_2_label = tk.StringVar(value="Open Work Orders")
        self.card_3_label = tk.StringVar(value="Completed")
        self.card_4_label = tk.StringVar(value="Avg Invoice")

        self.card_1_value = tk.StringVar(value="$0.00")
        self.card_2_value = tk.StringVar(value="0")
        self.card_3_value = tk.StringVar(value="0")
        self.card_4_value = tk.StringVar(value="$0.00")

        self.current_report_data: dict = {}
        self.insight_text = None
        self.tree = None
        self.table_columns: list[str] = []
        self.chart_frame_left = None
        self.chart_frame_right = None

        self._build_page_content()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_page_content(self) -> None:
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(4, weight=1)

        self._build_header()
        self._build_filter_bar()
        self._build_summary_cards()
        self._build_center_panels()
        self._build_bottom_table()

    def _build_header(self) -> None:
        header = tk.Frame(self.content, bg=self.CONTENT_BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="Reports",
            bg=self.CONTENT_BG,
            fg=self.TITLE_COLOR,
            font=("Segoe UI", 24, "bold"),
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            header,
            text="Back to Dashboard",
            command=self._go_dashboard,
            bg="#e8edf5",
            fg=self.TITLE_COLOR,
            activebackground="#dbe4f0",
            activeforeground=self.TITLE_COLOR,
            relief="flat",
            bd=0,
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=12,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="e")

    def _build_filter_bar(self) -> None:
        bar = tk.Frame(self.content, bg=self.CONTENT_BG)
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        bar.grid_columnconfigure(20, weight=1)

        tk.Label(
            bar,
            text="Timeframe",
            bg=self.CONTENT_BG,
            fg=self.BODY_COLOR,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        combo = ttk.Combobox(
            bar,
            textvariable=self.timeframe_var,
            state="readonly",
            values=[
                "Today",
                "Last 7 Days",
                "Last 30 Days",
                "Last 90 Days",
                "This Month",
                "This Year",
                "All Time",
            ],
            width=16,
        )
        combo.grid(row=0, column=1, sticky="w", padx=(0, 12))
        combo.bind("<<ComboboxSelected>>", lambda e: self.load_report_data())

        view_combo = ttk.Combobox(
            bar,
            textvariable=self.selected_view,
            state="readonly",
            values=[
                "Revenue Summary",
                "Work Order Status",
                "Vehicle Insights",
                "Customer Insights",
            ],
            width=18,
        )
        view_combo.grid(row=0, column=2, sticky="w", padx=(0, 12))
        view_combo.bind("<<ComboboxSelected>>", lambda e: self.load_report_data())

        self._toolbar_button(bar, "Refresh", 3, self.load_report_data)
        self._toolbar_button(bar, "Export", 4, self.export_csv)

    def _build_summary_cards(self) -> None:
        row = tk.Frame(self.content, bg=self.CONTENT_BG)
        row.grid(row=2, column=0, sticky="ew", pady=(0, 14))

        for i in range(4):
            row.grid_columnconfigure(i, weight=1)

        self._create_stat_card(row, self.card_1_label, self.card_1_value, 0)
        self._create_stat_card(row, self.card_2_label, self.card_2_value, 1)
        self._create_stat_card(row, self.card_3_label, self.card_3_value, 2)
        self._create_stat_card(row, self.card_4_label, self.card_4_value, 3)

    def _build_center_panels(self) -> None:
        center = tk.Frame(self.content, bg=self.CONTENT_BG)
        center.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        center.grid_columnconfigure(0, weight=3)
        center.grid_columnconfigure(1, weight=2)

        charts_panel = self._card(center)
        charts_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        charts_panel.grid_columnconfigure(0, weight=1)
        charts_panel.grid_columnconfigure(1, weight=1)
        charts_panel.grid_rowconfigure(2, weight=1)

        tk.Label(
            charts_panel,
            text="Visual Analytics",
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 6))

        tk.Label(
            charts_panel,
            text="Operational trends and business insights for the selected report view.",
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 12))

        self.chart_frame_left = tk.Frame(charts_panel, bg=self.CARD_BG)
        self.chart_frame_left.grid(row=2, column=0, sticky="nsew", padx=(16, 8), pady=(0, 16))

        self.chart_frame_right = tk.Frame(charts_panel, bg=self.CARD_BG)
        self.chart_frame_right.grid(row=2, column=1, sticky="nsew", padx=(8, 16), pady=(0, 16))

        insights_panel = self._card(center)
        insights_panel.grid(row=0, column=1, sticky="nsew")
        insights_panel.grid_rowconfigure(1, weight=1)
        insights_panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            insights_panel,
            text="Report Insights",
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 10))

        self.insight_text = tk.Text(
            insights_panel,
            wrap="word",
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=2,
            pady=2,
        )
        self.insight_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.insight_text.configure(state="disabled")

    def _build_bottom_table(self) -> None:
        bottom = self._card(self.content)
        bottom.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        bottom.grid_rowconfigure(1, weight=1)
        bottom.grid_columnconfigure(0, weight=1)

        tk.Label(
            bottom,
            text="Detailed Records",
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))

        table_container = tk.Frame(bottom, bg=self.CARD_BG)
        table_container.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_container, show="headings", style="Treeview")

        y_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def _card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.CARD_BG,
            highlightbackground="#d9e1ea",
            highlightthickness=1,
            bd=0,
        )

    def _create_stat_card(self, parent: tk.Widget, title_var: tk.StringVar, value_var: tk.StringVar, col: int) -> None:
        card = self._card(parent)
        pad_left = (0, 6) if col == 0 else (6, 6)
        if col == 3:
            pad_left = (6, 0)
        card.grid(row=0, column=col, sticky="ew", padx=pad_left)

        tk.Label(
            card,
            textvariable=title_var,
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
            font=("Segoe UI", 11),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        tk.Label(
            card,
            textvariable=value_var,
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
            font=("Segoe UI", 22, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))

    def _toolbar_button(self, parent: tk.Widget, text: str, col: int, command) -> None:
        tk.Button(
            parent,
            text=text,
            command=command,
            bg="#e8edf5",
            fg=self.TITLE_COLOR,
            activebackground="#d9e3f2",
            activeforeground=self.TITLE_COLOR,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=9,
            cursor="hand2",
        ).grid(row=0, column=col, padx=4, sticky="w")

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    def load_report_data(self) -> None:
        try:
            customers = self._get_customers()
            vehicles = self._get_vehicles()
            work_orders = self._get_work_orders()
            invoices = self._get_invoices()

            filtered_work_orders = self._filter_by_timeframe(
                work_orders,
                ["created_at", "updated_at", "opened_at"],
            )
            filtered_invoices = self._filter_by_timeframe(
                invoices,
                ["invoice_date", "created_at", "updated_at"],
            )

            report_data = self._build_report_model(
                customers,
                vehicles,
                filtered_work_orders,
                filtered_invoices,
            )
            self.current_report_data = report_data

            self._update_cards(report_data)
            self._render_charts(report_data)
            self._render_insights(report_data)
            self._populate_table(
                report_data.get("table_columns", []),
                report_data.get("table_rows", []),
            )

        except Exception as exc:
            logger.exception("Failed to load reports data: %s", exc)
            messagebox.showerror("Reports Error", str(exc))

    def _get_customers(self):
        response = self.customer_controller.get_all_customers()
        if not response.success:
            raise ValueError(response.message)
        return response.data or []

    def _get_vehicles(self):
        if hasattr(self.vehicle_controller, "get_prioritized_vehicle_list"):
            response = self.vehicle_controller.get_prioritized_vehicle_list()
        else:
            response = self.vehicle_controller.get_all_vehicles()
        if not response.success:
            raise ValueError(response.message)
        return response.data or []

    def _get_work_orders(self):
        response = self.work_order_controller.get_all_work_orders()
        if not response.success:
            raise ValueError(response.message)
        return response.data or []

    def _get_invoices(self):
        response = self.invoice_controller.get_all_invoices()
        if not response.success:
            raise ValueError(response.message)
        return response.data or []

    def _filter_by_timeframe(self, rows, date_keys):
        selected = self.timeframe_var.get()
        if selected == "All Time":
            return list(rows)

        now = datetime.now()

        if selected == "Today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif selected == "Last 7 Days":
            cutoff = now - timedelta(days=7)
        elif selected == "Last 30 Days":
            cutoff = now - timedelta(days=30)
        elif selected == "Last 90 Days":
            cutoff = now - timedelta(days=90)
        elif selected == "This Month":
            cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif selected == "This Year":
            cutoff = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return list(rows)

        filtered = []
        for row in rows:
            matched = False
            for key in date_keys:
                dt = self._parse_date(row.get(key))
                if dt:
                    matched = True
                    if dt >= cutoff:
                        filtered.append(row)
                    break
            if not matched:
                filtered.append(row)
        return filtered

    def _parse_date(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        raw = str(value).strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(raw[:19], fmt)
            except Exception:
                continue
        return None

    def _safe_float(self, value) -> float:
        try:
            return float(value or 0)
        except Exception:
            return 0.0

    def _normalize_work_order_status(self, value: str) -> str:
        status = str(value or "").strip().upper()
        if status in {"NEW", "PENDING"}:
            return "Pending"
        if status == "IN_PROGRESS":
            return "In Progress"
        if status in {"COMPLETED", "CLOSED", "READY"}:
            return "Completed"
        if status in {"CANCELLED", "CANCELED"}:
            return "Cancelled"
        return "Other"

    def _build_report_model(self, customers, vehicles, work_orders, invoices) -> dict:
        selected_view = self.selected_view.get()

        customer_name_by_id = {}
        for c in customers:
            full_name = (
                c.get("full_name")
                or f"{str(c.get('first_name', '')).strip()} {str(c.get('last_name', '')).strip()}".strip()
            )
            customer_name_by_id[c.get("id")] = full_name or "Unknown"

        vehicle_count_by_customer = defaultdict(int)
        make_count = defaultdict(int)
        for v in vehicles:
            customer_id = v.get("customer_id")
            if customer_id is not None:
                vehicle_count_by_customer[customer_id] += 1
            make = str(v.get("make", "")).strip() or "Unknown"
            make_count[make] += 1

        work_order_count_by_customer = defaultdict(int)
        status_count = defaultdict(int)
        completed_count = 0
        open_count = 0

        for wo in work_orders:
            cid = wo.get("customer_id")
            if cid is not None:
                work_order_count_by_customer[cid] += 1

            normalized = self._normalize_work_order_status(wo.get("current_status"))
            status_count[normalized] += 1

            if normalized == "Completed":
                completed_count += 1
            elif normalized in {"Pending", "In Progress"}:
                open_count += 1

        revenue_by_customer = defaultdict(float)
        payment_status_count = defaultdict(int)
        revenue_by_date = defaultdict(float)

        paid_invoice_count = 0
        unpaid_invoice_count = 0

        for inv in invoices:
            cid = inv.get("customer_id")
            amount = self._safe_float(inv.get("grand_total"))
            if cid is not None:
                revenue_by_customer[cid] += amount

            payment_status = str(inv.get("payment_status", "")).strip().upper() or "UNKNOWN"
            payment_status_count[payment_status] += 1

            if payment_status == "PAID":
                paid_invoice_count += 1
            else:
                unpaid_invoice_count += 1

            dt = self._parse_date(inv.get("invoice_date") or inv.get("created_at"))
            if dt:
                revenue_by_date[dt.date()] += amount

        total_revenue = sum(self._safe_float(inv.get("grand_total")) for inv in invoices)
        avg_invoice = (total_revenue / len(invoices)) if invoices else 0.0

        if selected_view == "Revenue Summary":
            sorted_days = sorted(revenue_by_date.items(), key=lambda x: x[0])
            labels = [d.strftime("%b %d") for d, _ in sorted_days][-7:]
            values = [amt for _, amt in sorted_days][-7:]

            if not labels:
                labels = ["No Data"]
                values = [0]

            chart_left = {
                "type": "line",
                "title": "Revenue Trend",
                "labels": labels,
                "values": values,
                "x_label": "Period",
                "y_label": "Revenue ($)",
            }

            payment_labels = ["PAID", "PARTIAL", "PENDING", "UNKNOWN"]
            payment_values = [payment_status_count.get(x, 0) for x in payment_labels]
            chart_right = {
                "type": "bar",
                "title": "Payment Status Breakdown",
                "labels": payment_labels,
                "values": payment_values,
                "x_label": "Payment Status",
                "y_label": "Count",
            }

            table_columns = [
                "Invoice Number",
                "Customer",
                "Work Order ID",
                "Grand Total",
                "Payment Status",
                "Invoice Date",
            ]
            table_rows = []
            for inv in invoices:
                table_rows.append(
                    {
                        "Invoice Number": inv.get("invoice_number", ""),
                        "Customer": customer_name_by_id.get(inv.get("customer_id"), inv.get("customer_name", "")),
                        "Work Order ID": inv.get("work_order_id", ""),
                        "Grand Total": f"${self._safe_float(inv.get('grand_total')):.2f}",
                        "Payment Status": inv.get("payment_status", ""),
                        "Invoice Date": str(inv.get("invoice_date", "")),
                    }
                )

            insights = (
                "Revenue Summary\n\n"
                f"• Total revenue: ${total_revenue:.2f}\n"
                f"• Paid invoices: {paid_invoice_count}\n"
                f"• Unpaid / partial invoices: {unpaid_invoice_count}\n"
                f"• Average invoice value: ${avg_invoice:.2f}\n"
                "• Use this view to monitor cash flow and billing performance."
            )

            cards = [
                ("Revenue", f"${total_revenue:.2f}"),
                ("Open Work Orders", str(open_count)),
                ("Completed", str(completed_count)),
                ("Avg Invoice", f"${avg_invoice:.2f}"),
            ]

        elif selected_view == "Work Order Status":
            status_labels = ["Pending", "In Progress", "Completed", "Cancelled", "Other"]
            status_values = [status_count.get(x, 0) for x in status_labels]

            chart_left = {
                "type": "bar",
                "title": "Work Order Status Breakdown",
                "labels": status_labels,
                "values": status_values,
                "x_label": "Status",
                "y_label": "Count",
            }

            open_completed_labels = ["Open", "Completed"]
            open_completed_values = [open_count, completed_count]
            chart_right = {
                "type": "bar",
                "title": "Open vs Completed",
                "labels": open_completed_labels,
                "values": open_completed_values,
                "x_label": "Type",
                "y_label": "Count",
            }

            table_columns = [
                "Work Order ID",
                "Customer",
                "Plate Number",
                "Assigned Staff",
                "Status",
            ]
            table_rows = []
            for wo in work_orders:
                table_rows.append(
                    {
                        "Work Order ID": wo.get("work_order_id", ""),
                        "Customer": customer_name_by_id.get(wo.get("customer_id"), wo.get("customer_name", "")),
                        "Plate Number": wo.get("plate_number", ""),
                        "Assigned Staff": wo.get("assigned_staff_name", wo.get("assigned_staff", "")),
                        "Status": self._normalize_work_order_status(wo.get("current_status")),
                    }
                )

            insights = (
                "Work Order Status\n\n"
                f"• Open work orders: {open_count}\n"
                f"• Completed work orders: {completed_count}\n"
                f"• Pending jobs: {status_count.get('Pending', 0)}\n"
                f"• In-progress jobs: {status_count.get('In Progress', 0)}\n"
                "• This view helps monitor workshop load and turnaround."
            )

            cards = [
                ("Open Work Orders", str(open_count)),
                ("Completed", str(completed_count)),
                ("Pending", str(status_count.get("Pending", 0))),
                ("In Progress", str(status_count.get("In Progress", 0))),
            ]

        elif selected_view == "Vehicle Insights":
            sorted_makes = sorted(make_count.items(), key=lambda x: x[1], reverse=True)[:7]
            if sorted_makes:
                make_labels = [x[0] for x in sorted_makes]
                make_values = [x[1] for x in sorted_makes]
            else:
                make_labels = ["No Data"]
                make_values = [0]

            chart_left = {
                "type": "bar",
                "title": "Top Vehicle Makes",
                "labels": make_labels,
                "values": make_values,
                "x_label": "Make",
                "y_label": "Count",
            }

            customer_vehicle_pairs = sorted(vehicle_count_by_customer.items(), key=lambda x: x[1], reverse=True)[:7]
            if customer_vehicle_pairs:
                cust_labels = [customer_name_by_id.get(cid, "Unknown") for cid, _ in customer_vehicle_pairs]
                cust_values = [count for _, count in customer_vehicle_pairs]
            else:
                cust_labels = ["No Data"]
                cust_values = [0]

            chart_right = {
                "type": "bar",
                "title": "Vehicles by Customer",
                "labels": cust_labels,
                "values": cust_values,
                "x_label": "Customer",
                "y_label": "Vehicles",
            }

            table_columns = [
                "Customer",
                "Plate Number",
                "Make",
                "Model",
                "Year",
                "VIN",
            ]
            table_rows = []
            for v in vehicles:
                table_rows.append(
                    {
                        "Customer": customer_name_by_id.get(v.get("customer_id"), v.get("customer_name", "")),
                        "Plate Number": v.get("plate_number", ""),
                        "Make": v.get("make", ""),
                        "Model": v.get("model", ""),
                        "Year": v.get("year", ""),
                        "VIN": v.get("vin", ""),
                    }
                )

            insights = (
                "Vehicle Insights\n\n"
                f"• Total vehicles in record: {len(vehicles)}\n"
                f"• Unique makes tracked: {len(make_count)}\n"
                f"• Most common make: {make_labels[0] if make_labels else '-'}\n"
                "• This view helps with demand planning and inventory forecasting."
            )

            cards = [
                ("Vehicles", str(len(vehicles))),
                ("Unique Makes", str(len(make_count))),
                ("Open Work Orders", str(open_count)),
                ("Customers", str(len(customers))),
            ]

        else:
            customer_records = []
            for c in customers:
                cid = c.get("id")
                full_name = customer_name_by_id.get(cid, "Unknown")
                customer_records.append(
                    {
                        "Customer": full_name,
                        "Phone": c.get("phone", ""),
                        "Email": c.get("email", ""),
                        "City": c.get("city", ""),
                        "Vehicles": vehicle_count_by_customer.get(cid, 0),
                        "Work Orders": work_order_count_by_customer.get(cid, 0),
                        "Revenue": revenue_by_customer.get(cid, 0.0),
                    }
                )

            top_customers = sorted(customer_records, key=lambda x: x["Revenue"], reverse=True)[:7]
            if top_customers:
                cust_labels = [x["Customer"] for x in top_customers]
                cust_values = [x["Revenue"] for x in top_customers]
            else:
                cust_labels = ["No Data"]
                cust_values = [0]

            work_order_top = sorted(customer_records, key=lambda x: x["Work Orders"], reverse=True)[:7]
            if work_order_top:
                wo_labels = [x["Customer"] for x in work_order_top]
                wo_values = [x["Work Orders"] for x in work_order_top]
            else:
                wo_labels = ["No Data"]
                wo_values = [0]

            chart_left = {
                "type": "bar",
                "title": "Top Customers by Revenue",
                "labels": cust_labels,
                "values": cust_values,
                "x_label": "Customer",
                "y_label": "Revenue ($)",
            }

            chart_right = {
                "type": "bar",
                "title": "Top Customers by Work Orders",
                "labels": wo_labels,
                "values": wo_values,
                "x_label": "Customer",
                "y_label": "Work Orders",
            }

            table_columns = [
                "Customer",
                "Phone",
                "Email",
                "City",
                "Vehicles",
                "Work Orders",
                "Revenue",
            ]
            table_rows = []
            for record in customer_records:
                row = dict(record)
                row["Revenue"] = f"${self._safe_float(row['Revenue']):.2f}"
                table_rows.append(row)

            top_customer_name = cust_labels[0] if cust_labels else "-"
            top_customer_revenue = cust_values[0] if cust_values else 0

            insights = (
                "Customer Insights\n\n"
                f"• Total customers: {len(customers)}\n"
                f"• Top customer by revenue: {top_customer_name}\n"
                f"• Top customer revenue: ${top_customer_revenue:.2f}\n"
                "• This view helps identify repeat and high-value customers."
            )

            cards = [
                ("Customers", str(len(customers))),
                ("Vehicles", str(len(vehicles))),
                ("Work Orders", str(len(work_orders))),
                ("Revenue", f"${total_revenue:.2f}"),
            ]

        return {
            "cards": cards,
            "chart_left": chart_left,
            "chart_right": chart_right,
            "insights": insights,
            "table_columns": table_columns,
            "table_rows": table_rows,
        }

    # ------------------------------------------------------------------
    # VIEW RENDER
    # ------------------------------------------------------------------
    def _update_cards(self, report_data: dict) -> None:
        cards = report_data.get("cards", [])
        defaults = [
            ("Metric 1", "0"),
            ("Metric 2", "0"),
            ("Metric 3", "0"),
            ("Metric 4", "0"),
        ]
        cards = (cards + defaults)[:4]

        self.card_1_label.set(cards[0][0])
        self.card_1_value.set(cards[0][1])
        self.card_2_label.set(cards[1][0])
        self.card_2_value.set(cards[1][1])
        self.card_3_label.set(cards[2][0])
        self.card_3_value.set(cards[2][1])
        self.card_4_label.set(cards[3][0])
        self.card_4_value.set(cards[3][1])

    def _render_insights(self, report_data: dict) -> None:
        if not self.insight_text:
            return

        content = report_data.get("insights", "No insights available.")

        self.insight_text.configure(state="normal")
        self.insight_text.delete("1.0", tk.END)
        self.insight_text.insert("1.0", content)
        self.insight_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # CHARTS
    # ------------------------------------------------------------------
    def _render_charts(self, report_data: dict) -> None:
        if not self.chart_frame_left or not self.chart_frame_right:
            return

        for widget in self.chart_frame_left.winfo_children():
            widget.destroy()
        for widget in self.chart_frame_right.winfo_children():
            widget.destroy()

        self._draw_chart(self.chart_frame_left, report_data.get("chart_left", {}))
        self._draw_chart(self.chart_frame_right, report_data.get("chart_right", {}))

    def _draw_chart(self, parent, chart_data: dict) -> None:
        labels = chart_data.get("labels", [])
        values = chart_data.get("values", [])
        title = chart_data.get("title", "")
        x_label = chart_data.get("x_label", "")
        y_label = chart_data.get("y_label", "")
        chart_type = chart_data.get("type", "bar")

        fig = Figure(figsize=(4.6, 3.0), dpi=100)
        ax = fig.add_subplot(111)

        if not labels or not values or sum(values) == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=11)
            ax.set_axis_off()
        else:
            if chart_type == "line":
                ax.plot(labels, values, marker="o", linewidth=2)
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis="x", rotation=25, labelsize=9)
            else:
                ax.bar(labels, values)
                ax.grid(True, axis="y", alpha=0.3)
                ax.tick_params(axis="x", rotation=15, labelsize=9)

            ax.set_title(title, fontsize=11, pad=10)
            ax.set_xlabel(x_label, fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.tick_params(axis="y", labelsize=9)

        fig.subplots_adjust(left=0.13, right=0.97, top=0.88, bottom=0.22)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # TABLE / EXPORT
    # ------------------------------------------------------------------
    def _populate_table(self, columns, rows) -> None:
        if not self.tree:
            return

        self.tree.delete(*self.tree.get_children())

        self.tree["columns"] = columns
        self.table_columns = list(columns)

        widths = {
            "Invoice Number": 150,
            "Customer": 180,
            "Work Order ID": 130,
            "Grand Total": 110,
            "Payment Status": 120,
            "Invoice Date": 120,
            "Plate Number": 120,
            "Assigned Staff": 140,
            "Status": 110,
            "Phone": 120,
            "Email": 220,
            "City": 120,
            "Vehicles": 90,
            "Work Orders": 100,
            "Revenue": 110,
            "Make": 120,
            "Model": 120,
            "Year": 80,
            "VIN": 180,
            "Role": 100,
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 130), anchor="center")

        for row in rows:
            self.tree.insert(
                "",
                tk.END,
                values=[row.get(col, "") for col in columns],
            )

    def export_csv(self) -> None:
        rows = self.current_report_data.get("table_rows", [])
        columns = self.current_report_data.get("table_columns", [])

        if not rows or not columns:
            messagebox.showinfo("Export CSV", "No records available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Report CSV",
            defaultextension=".csv",
            initialfile=f"garagepulse_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow([row.get(col, "") for col in columns])

            messagebox.showinfo("Export CSV", f"Report exported successfully.\n\n{file_path}")
        except Exception as exc:
            messagebox.showerror("Export CSV", f"Failed to export CSV.\n\n{exc}")

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------
    def _go_dashboard(self) -> None:
        self._safe_navigate("dashboard")

    def _safe_navigate(self, page_name: str) -> None:
        try:
            page_map = {
                "dashboard": ("ui.pages.dashboard_page", "DashboardPage"),
                "customers": ("ui.pages.customers_page", "CustomersPage"),
                "vehicles": ("ui.pages.vehicles_page", "VehiclesPage"),
                "work_orders": ("ui.pages.work_orders_page", "WorkOrdersPage"),
                "invoices": ("ui.pages.invoices_page", "InvoicesPage"),
                "notifications": ("ui.pages.notifications_page", "NotificationsPage"),
                "active_accounts": ("ui.pages.active_accounts_page", "ActiveAccountsPage"),
                "reports": ("ui.pages.reports_page", "ReportsPage"),
            }

            if hasattr(self.app, "show_page"):
                try:
                    self.app.show_page(page_name)
                    return
                except Exception:
                    pass

            if hasattr(self.app, "pages") and page_name in getattr(self.app, "pages", {}):
                self.app.show_page(page_name)
                return

            if page_name not in page_map:
                raise ValueError(f"Unknown page mapping: {page_name}")

            module_name, class_name = page_map[page_name]
            module = importlib.import_module(module_name)
            page_class = getattr(module, class_name)

            if hasattr(self.app, "register_page"):
                self.app.register_page(page_name, page_class)
                self.app.show_page(page_name)
                return

            raise ValueError(f"Page '{page_name}' is not registered and app.register_page is unavailable.")

        except Exception as exc:
            messagebox.showerror("Navigation Error", str(exc))



    def on_show(self) -> None:
        if hasattr(super(), "on_show"):
            try:
                super().on_show()
            except Exception:
                pass
        self.load_report_data()