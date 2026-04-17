"""
ui/pages/notifications_page.py

Notifications page for GaragePulse using shared AppShell.

Improvements:
- email-only workflow
- cleaner production-style layout
- realistic default subject/message
- customer auto-fills from selected work order
- readonly delivery tracking panel
- better width/alignment
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class NotificationsPage(AppShell):
    """
    Notifications management page with shared app shell.
    """

    LEFT_PANEL_WIDTH = 430
    FIELD_PADX = 16

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="notifications",
            page_title="Notifications",
        )

        self.notification_controller = app.get_controller("notification")
        self.work_order_controller = app.get_controller("work_order")

        self.work_order_var = tk.StringVar()
        self.customer_display_var = tk.StringVar()
        self.recipient_email_var = tk.StringVar()
        self.subject_var = tk.StringVar()

        self.selected_notification_id_var = tk.StringVar()
        self.delivery_status_var = tk.StringVar(value="PENDING")
        self.provider_status_var = tk.StringVar()
        self.error_message_var = tk.StringVar()
        self.external_reference_var = tk.StringVar()
        self.created_at_var = tk.StringVar()

        self.work_order_map: dict[str, dict] = {}

        self._build_page_content()

    # ------------------------------------------------------------------
    # PAGE LAYOUT
    # ------------------------------------------------------------------
    def _build_page_content(self) -> None:
        self.content.grid_columnconfigure(0, weight=0, minsize=self.LEFT_PANEL_WIDTH)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        left_outer = tk.Frame(
            self.content,
            bg=self.CONTENT_BG,
            width=self.LEFT_PANEL_WIDTH,
        )
        left_outer.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        left_outer.grid_propagate(False)

        right_card = tk.Frame(self.content, bg=self.CARD_BG)
        right_card.grid(row=0, column=1, sticky="nsew")

        self._build_scrollable_form_panel(left_outer)
        self._build_list_panel(right_card)

    def _build_scrollable_form_panel(self, parent: tk.Frame) -> None:
        container = tk.Frame(parent, bg=self.CONTENT_BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            bg=self.CONTENT_BG,
            highlightthickness=0,
            width=self.LEFT_PANEL_WIDTH - 18,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.CONTENT_BG)

        window_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")

        def _on_scrollable_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)

        scrollable.bind("<Configure>", _on_scrollable_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_email_card(scrollable)
        self._build_tracking_card(scrollable)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ------------------------------------------------------------------
    # SHARED HELPERS
    # ------------------------------------------------------------------
    def _add_label(self, parent: tk.Frame, row: int, text: str, required: bool = False) -> None:
        label_text = f"{text} *" if required else text
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold" if required else "normal"),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 4))

    def _make_entry(self, parent: tk.Frame, textvariable, state: str = "normal") -> tk.Entry:
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            state=state,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        if state == "readonly":
            entry.configure(readonlybackground="#f8fafc")
        return entry

    def _make_primary_button(self, parent: tk.Frame, text: str, command, row: int, pady=(0, 16)) -> None:
        tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=12,
            cursor="hand2",
        ).grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=pady)

    def _clear_tracking_fields(self) -> None:
        self.selected_notification_id_var.set("")
        self.delivery_status_var.set("PENDING")
        self.provider_status_var.set("")
        self.external_reference_var.set("")
        self.error_message_var.set("")
        self.created_at_var.set("")

    def _build_default_message(self, entry: dict) -> tuple[str, str]:
        customer_name = entry.get("customer_name", "Customer")
        work_order_code = entry.get("work_order_id", "")
        plate_number = entry.get("plate_number", "")
        status = entry.get("current_status", "UPDATED")

        subject = f"GaragePulse Update - Work Order {work_order_code}"
        message = (
            f"Hello {customer_name},\n\n"
            f"This is an update regarding your vehicle service request.\n\n"
            f"Work Order: {work_order_code}\n"
            f"Vehicle: {plate_number}\n"
            f"Current Status: {status}\n\n"
            f"If you have any questions, please contact GaragePulse.\n\n"
            f"Thank you,\n"
            f"GaragePulse Auto Service Management System"
        )
        return subject, message

    # ------------------------------------------------------------------
    # LEFT PANEL
    # ------------------------------------------------------------------
    def _build_email_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.pack(fill="x", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            card,
            text="Send Email Notification",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(18, 12))

        row += 1
        self._add_label(card, row, "Work Order", required=True)
        row += 1
        self.work_order_combo = ttk.Combobox(
            card,
            textvariable=self.work_order_var,
            state="readonly",
        )
        self.work_order_combo.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8))
        self.work_order_combo.bind("<<ComboboxSelected>>", self._on_work_order_selected)

        row += 1
        self._add_label(card, row, "Customer", required=True)
        row += 1
        self.customer_entry = self._make_entry(card, self.customer_display_var, state="readonly")
        self.customer_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Recipient Email", required=True)
        row += 1
        self.email_entry = self._make_entry(card, self.recipient_email_var, state="readonly")
        self.email_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Subject", required=True)
        row += 1
        self.subject_entry = self._make_entry(card, self.subject_var)
        self.subject_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Message", required=True)
        row += 1
        self.message_text = tk.Text(
            card,
            height=7,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            wrap="word",
        )
        self.message_text.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 10))

        row += 1
        self._make_primary_button(card, "Send Email", self._create_notification, row)

    def _build_tracking_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.pack(fill="x")
        card.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            card,
            text="Delivery Tracking",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(18, 12))

        row += 1
        tk.Label(
            card,
            text="Select a notification record to view delivery details.",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 8))

        row += 1
        self._add_label(card, row, "Selected Notification")
        row += 1
        self.selected_notification_entry = self._make_entry(
            card,
            self.selected_notification_id_var,
            state="readonly",
        )
        self.selected_notification_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Delivery Status")
        row += 1
        self.delivery_status_entry = self._make_entry(
            card,
            self.delivery_status_var,
            state="readonly",
        )
        self.delivery_status_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Provider Status")
        row += 1
        self.provider_status_entry = self._make_entry(
            card,
            self.provider_status_var,
            state="readonly",
        )
        self.provider_status_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "External Reference")
        row += 1
        self.external_reference_entry = self._make_entry(
            card,
            self.external_reference_var,
            state="readonly",
        )
        self.external_reference_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Created At")
        row += 1
        self.created_at_entry = self._make_entry(
            card,
            self.created_at_var,
            state="readonly",
        )
        self.created_at_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=4)

        row += 1
        self._add_label(card, row, "Error Message")
        row += 1
        self.error_message_entry = self._make_entry(
            card,
            self.error_message_var,
            state="readonly",
        )
        self.error_message_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 16), ipady=4)

    # ------------------------------------------------------------------
    # RIGHT PANEL
    # ------------------------------------------------------------------
    def _build_list_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        tk.Label(
            parent,
            text="Notification Records",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(18, 12))

        table_frame = tk.Frame(parent, bg=self.CARD_BG)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 18))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = (
            "work_order_id",
            "customer_name",
            "delivery_status",
            "created_at",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_notification_selected)
        self.tree.bind("<Double-1>", self._view_details)

        headings = {
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "delivery_status": "Status",
            "created_at": "Created At",
        }

        widths = {
            "work_order_id": 190,
            "customer_name": 230,
            "delivery_status": 120,
            "created_at": 180,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w", stretch=True)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        tk.Button(
            parent,
            text="Refresh",
            command=self._load_all_notifications,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
        ).grid(row=2, column=0, sticky="e", padx=16, pady=(0, 18))

    # ------------------------------------------------------------------
    # DATA LOADERS
    # ------------------------------------------------------------------
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
                "customer_email": work_order.get("customer_email", ""),
                "work_order_id": work_order.get("work_order_id", ""),
                "plate_number": work_order.get("plate_number", ""),
                "current_status": work_order.get("current_status", ""),
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
            self.recipient_email_var.set("")
            self.subject_var.set("")
            self.message_text.delete("1.0", tk.END)
            return

        self.customer_display_var.set(entry.get("customer_name", ""))
        self.recipient_email_var.set(entry.get("customer_email", ""))

        subject, message = self._build_default_message(entry)
        self.subject_var.set(subject)
        self.message_text.delete("1.0", tk.END)
        self.message_text.insert("1.0", message)

    def _create_notification(self) -> None:
        selected = self.work_order_var.get()
        entry = self.work_order_map.get(selected)

        if not entry:
            messagebox.showwarning("Selection Required", "Please select a work order.")
            return

        recipient_email = self.recipient_email_var.get().strip()
        subject = self.subject_var.get().strip()
        message_body = self.message_text.get("1.0", tk.END).strip()

        if not recipient_email:
            messagebox.showwarning("Input Required", "Recipient email is required.")
            return

        if not subject:
            messagebox.showwarning("Input Required", "Subject is required.")
            self.subject_entry.focus_set()
            return

        if not message_body:
            messagebox.showwarning("Input Required", "Message is required.")
            self.message_text.focus_set()
            return

        response = self.notification_controller.create_notification(
            work_order_id=entry["id"],
            customer_id=entry["customer_id"],
            channel="EMAIL",
            message_body=message_body,
            subject=subject,
            sent_to=recipient_email,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_notifications()

    def _load_all_notifications(self) -> None:
        response = self.notification_controller.get_all_notifications()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.tree.delete(*self.tree.get_children())

        for row in response.data or []:
            notification_id = str(row.get("id", ""))
            self.tree.insert(
                "",
                "end",
                iid=notification_id,
                values=(
                    row.get("work_order_id", ""),
                    row.get("customer_name", ""),
                    row.get("delivery_status", ""),
                    row.get("created_at", ""),
                ),
            )

    def _on_notification_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            selection = self.tree.selection()
            if not selection:
                return
            selected = selection[0]

        response = self.notification_controller.get_notification(int(selected))
        if not response.success:
            self.selected_notification_id_var.set(str(selected))
            values = self.tree.item(selected, "values")
            if values:
                self.delivery_status_var.set(str(values[2] or "PENDING"))
                self.created_at_var.set(str(values[3] or ""))
            return

        data = response.data or {}
        self.selected_notification_id_var.set(str(data.get("id", selected)))
        self.delivery_status_var.set(str(data.get("delivery_status", "") or "PENDING"))
        self.provider_status_var.set(str(data.get("provider_status", "") or ""))
        self.error_message_var.set(str(data.get("error_message", "") or ""))
        self.external_reference_var.set(str(data.get("external_reference", "") or ""))
        self.created_at_var.set(str(data.get("created_at", "") or ""))

    def _view_details(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        response = self.notification_controller.get_notification(int(selected))

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        data = response.data or {}

        details = [
            f"Customer: {data.get('customer_name', '')}",
            f"Work Order ID: {data.get('work_order_id', '')}",
            f"Channel: {data.get('channel', '')}",
            f"Recipient: {data.get('sent_to', '')}",
            f"Subject: {data.get('subject', '')}",
            "",
            "Message:",
            f"{data.get('message_body', '')}",
            "",
            f"Delivery Status: {data.get('delivery_status', '')}",
            f"Provider Status: {data.get('provider_status', '')}",
            f"Created At: {data.get('created_at', '')}",
            f"Error Message: {data.get('error_message', '')}",
        ]

        messagebox.showinfo("Notification Details", "\n".join(details))

    def on_show(self) -> None:
        self._build_sidebar()
        self._clear_tracking_fields()
        self._load_work_orders()
        self._load_all_notifications()