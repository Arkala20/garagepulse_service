"""
ui/pages/notifications_page.py

Production-style Notifications page for GaragePulse.

Upgrades from prototype:
- select work order from existing records
- customer auto-derived from selected work order
- list shows customer name
- double click opens full notification details
- status update tools for future delivery workflow
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class NotificationsPage(ttk.Frame):
    """
    Notifications management page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.notification_controller = app.get_controller("notification")
        self.work_order_controller = app.get_controller("work_order")

        self.work_order_var = tk.StringVar()
        self.customer_display_var = tk.StringVar()
        self.channel_var = tk.StringVar(value="EMAIL")
        self.subject_var = tk.StringVar()
        self.message_var = tk.StringVar()

        self.selected_notification_id_var = tk.StringVar()
        self.delivery_status_var = tk.StringVar(value="PENDING")
        self.provider_status_var = tk.StringVar()
        self.error_message_var = tk.StringVar()
        self.external_reference_var = tk.StringVar()

        self.work_order_map: dict[str, dict] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Notifications",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            header,
            text="Back to Dashboard",
            command=lambda: self.app.show_page("dashboard"),
        ).grid(row=0, column=2, sticky="e")

        body = ttk.Frame(self, style="App.TFrame")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left_panel(body)
        self._build_right_panel(body)

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=18)
        panel.grid(row=0, column=0, sticky="nsw", padx=(0, 15))

        ttk.Label(
            panel,
            text="Create Notification",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        row = 1
        self._add_label(panel, row, "Work Order")
        row += 1
        self.work_order_combo = ttk.Combobox(
            panel,
            textvariable=self.work_order_var,
            state="readonly",
            width=36,
        )
        self.work_order_combo.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self.work_order_combo.bind("<<ComboboxSelected>>", self._on_work_order_selected)

        row += 1
        self._add_label(panel, row, "Customer")
        row += 1
        ttk.Entry(
            panel,
            textvariable=self.customer_display_var,
            state="readonly",
            width=38,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Channel")
        row += 1
        ttk.Combobox(
            panel,
            textvariable=self.channel_var,
            values=["EMAIL", "SMS"],
            state="readonly",
            width=36,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Subject")
        row += 1
        ttk.Entry(panel, textvariable=self.subject_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Message")
        row += 1
        ttk.Entry(panel, textvariable=self.message_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 10)
        )

        row += 1
        ttk.Button(
            panel,
            text="Create Notification",
            style="Primary.TButton",
            command=self._create_notification,
        ).grid(row=row, column=0, sticky="ew", pady=(4, 14))

        row += 1
        ttk.Separator(panel).grid(row=row, column=0, sticky="ew", pady=8)

        row += 1
        ttk.Label(
            panel,
            text="Update Delivery Status",
            style="PageTitle.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(4, 12))

        row += 1
        self._add_label(panel, row, "Selected Notification ID")
        row += 1
        ttk.Entry(
            panel,
            textvariable=self.selected_notification_id_var,
            state="readonly",
            width=38,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Delivery Status")
        row += 1
        ttk.Combobox(
            panel,
            textvariable=self.delivery_status_var,
            values=["PENDING", "SENT", "FAILED"],
            state="readonly",
            width=36,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Provider Status")
        row += 1
        ttk.Entry(panel, textvariable=self.provider_status_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "External Reference")
        row += 1
        ttk.Entry(panel, textvariable=self.external_reference_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Error Message")
        row += 1
        ttk.Entry(panel, textvariable=self.error_message_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        ttk.Button(
            panel,
            text="Update Status",
            command=self._update_delivery_status,
        ).grid(row=row, column=0, sticky="ew")

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent, style="Card.TFrame", padding=20)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Notification Records",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        columns = (
            "id",
            "work_order_id",
            "customer_name",
            "channel",
            "delivery_status",
            "created_at",
        )

        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_notification_selected)
        self.tree.bind("<Double-1>", self._view_details)

        headings = {
            "id": "ID",
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "channel": "Channel",
            "delivery_status": "Status",
            "created_at": "Created At",
        }

        widths = {
            "id": 70,
            "work_order_id": 140,
            "customer_name": 180,
            "channel": 100,
            "delivery_status": 100,
            "created_at": 150,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(
            container,
            text="Refresh",
            command=self._load_all_notifications,
        ).grid(row=2, column=0, sticky="e", pady=(10, 0))

    def _add_label(self, parent: ttk.Frame, row: int, text: str) -> None:
        ttk.Label(parent, text=text, style="Body.TLabel").grid(
            row=row,
            column=0,
            sticky="w",
            pady=(0, 4),
        )

    def _load_work_orders(self) -> None:
        response = self.work_order_controller.get_all_work_orders()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.work_order_map.clear()
        display_values = []

        for work_order in response.data or []:
            display = (
                f"{work_order.get('work_order_id')} | "
                f"{work_order.get('customer_name', '')} | "
                f"{work_order.get('plate_number', '')}"
            )
            self.work_order_map[display] = {
                "id": work_order["id"],
                "customer_id": work_order.get("customer_id"),
                "customer_name": work_order.get("customer_name", ""),
                "work_order_id": work_order.get("work_order_id", ""),
            }
            display_values.append(display)

        self.work_order_combo["values"] = display_values
        if display_values and not self.work_order_var.get():
            self.work_order_combo.current(0)
            self._on_work_order_selected()

    def _on_work_order_selected(self, event=None) -> None:
        selected = self.work_order_var.get()
        entry = self.work_order_map.get(selected)

        if not entry:
            self.customer_display_var.set("")
            return

        self.customer_display_var.set(entry.get("customer_name", ""))

    def _create_notification(self) -> None:
        selected = self.work_order_var.get()
        entry = self.work_order_map.get(selected)

        if not entry:
            messagebox.showwarning(
                "Selection Required",
                "Please select a work order.",
            )
            return

        response = self.notification_controller.create_notification(
            work_order_id=entry["id"],
            customer_id=entry["customer_id"],
            channel=self.channel_var.get(),
            message_body=self.message_var.get(),
            subject=self.subject_var.get() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo(
            "Success",
            response.message + "\n\nNote: current build stores notification records in the system. Real email/SMS provider delivery is a later integration step.",
        )

        self.subject_var.set("")
        self.message_var.set("")
        self._load_all_notifications()

    def _load_all_notifications(self) -> None:
        response = self.notification_controller.get_all_notifications()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.tree.delete(*self.tree.get_children())

        for row in response.data or []:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get("id", ""),
                    row.get("work_order_id", ""),
                    row.get("customer_name", ""),
                    row.get("channel", ""),
                    row.get("delivery_status", ""),
                    row.get("created_at", ""),
                ),
            )

    def _on_notification_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        if not values:
            return

        self.selected_notification_id_var.set(str(values[0]))
        self.delivery_status_var.set(str(values[4]))

    def _update_delivery_status(self) -> None:
        notification_id = self.selected_notification_id_var.get().strip()
        if not notification_id:
            messagebox.showwarning(
                "Selection Required",
                "Select a notification row first.",
            )
            return

        response = self.notification_controller.update_delivery_status(
            notification_id=int(notification_id),
            delivery_status=self.delivery_status_var.get(),
            provider_status=self.provider_status_var.get() or None,
            error_message=self.error_message_var.get() or None,
            external_reference=self.external_reference_var.get() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_notifications()

    def _view_details(self, event=None) -> None:
        selected = self.tree.focus()
        values = self.tree.item(selected, "values")

        if not values:
            return

        notification_id = int(values[0])

        response = self.notification_controller.get_notification(notification_id)

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        data = response.data or {}

        details = [
            f"Customer: {data.get('customer_name', '')}",
            f"Work Order ID: {data.get('work_order_id', '')}",
            f"Channel: {data.get('channel', '')}",
            f"Subject: {data.get('subject', '')}",
            "",
            "Message:",
            f"{data.get('message_body', '')}",
            "",
            f"Delivery Status: {data.get('delivery_status', '')}",
            f"Provider Status: {data.get('provider_status', '')}",
            f"Sent To: {data.get('sent_to', '')}",
            f"Sent At: {data.get('sent_at', '')}",
            f"Created At: {data.get('created_at', '')}",
            f"Error Message: {data.get('error_message', '')}",
        ]

        messagebox.showinfo("Notification Details", "\n".join(details))

    def on_show(self) -> None:
        self._load_work_orders()
        self._load_all_notifications()