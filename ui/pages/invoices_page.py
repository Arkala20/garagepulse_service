"""
ui/pages/invoices_page.py

Production-style Invoices page for GaragePulse.

Upgrades from prototype:
- select work order from existing records instead of typing raw internal IDs
- generate invoice from selected work order
- select invoice rows for payment updates
- view invoice details cleanly
- show saved payment methods area placeholder for future-ready design
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class InvoicesPage(ttk.Frame):
    """
    Invoices management page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.invoice_controller = app.get_controller("invoice")
        self.work_order_controller = app.get_controller("work_order")

        self.work_order_var = tk.StringVar()
        self.tax_rate_var = tk.StringVar(value="0")
        self.discount_var = tk.StringVar(value="0")
        self.payment_method_summary_var = tk.StringVar()
        self.selected_invoice_number_var = tk.StringVar()

        self.work_order_map: dict[str, int] = {}
        self.invoice_id_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Invoices",
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
            text="Generate Invoice",
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

        row += 1
        self._add_label(panel, row, "Tax Rate (%)")
        row += 1
        ttk.Entry(panel, textvariable=self.tax_rate_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Discount Amount")
        row += 1
        ttk.Entry(panel, textvariable=self.discount_var, width=38).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        ttk.Button(
            panel,
            text="Generate Invoice",
            style="Primary.TButton",
            command=self._generate_invoice,
        ).grid(row=row, column=0, sticky="ew", pady=(4, 14))

        row += 1
        ttk.Separator(panel).grid(row=row, column=0, sticky="ew", pady=8)

        row += 1
        ttk.Label(
            panel,
            text="Selected Invoice",
            style="PageTitle.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(4, 12))

        row += 1
        self._add_label(panel, row, "Invoice Number")
        row += 1
        ttk.Entry(
            panel,
            textvariable=self.selected_invoice_number_var,
            state="readonly",
            width=38,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Payment Method Summary")
        row += 1
        ttk.Entry(
            panel,
            textvariable=self.payment_method_summary_var,
            width=38,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        ttk.Button(
            panel,
            text="Mark Paid",
            command=self._mark_paid,
        ).grid(row=row, column=0, sticky="ew", pady=(4, 6))

        row += 1
        ttk.Button(
            panel,
            text="Mark Partial",
            command=self._mark_partial,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 6))

        row += 1
        ttk.Button(
            panel,
            text="View Invoice",
            command=self._view_invoice,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 14))

        row += 1
        ttk.Separator(panel).grid(row=row, column=0, sticky="ew", pady=8)

        row += 1
        ttk.Label(
            panel,
            text="Saved Payment Methods",
            style="PageTitle.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(4, 12))

        row += 1
        ttk.Label(
            panel,
            text=(
                "Future-ready placeholder.\n"
                "Real saved card listing and provider integration\n"
                "can be added in the next phase."
            ),
            style="Body.TLabel",
            justify="left",
        ).grid(row=row, column=0, sticky="w")

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent, style="Card.TFrame", padding=20)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Invoice Records",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        columns = (
            "id",
            "invoice_number",
            "work_order_id",
            "customer_name",
            "grand_total",
            "payment_status",
        )

        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_invoice_selected)

        headings = {
            "id": "ID",
            "invoice_number": "Invoice Number",
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "grand_total": "Grand Total",
            "payment_status": "Payment Status",
        }

        widths = {
            "id": 70,
            "invoice_number": 140,
            "work_order_id": 140,
            "customer_name": 170,
            "grand_total": 110,
            "payment_status": 130,
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
            command=self._load_all_invoices,
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
                f"{work_order.get('plate_number', '')} | "
                f"ID:{work_order.get('id')}"
            )
            self.work_order_map[display] = work_order["id"]
            display_values.append(display)

        self.work_order_combo["values"] = display_values
        if display_values and not self.work_order_var.get():
            self.work_order_combo.current(0)

    def _generate_invoice(self) -> None:
        selected_work_order = self.work_order_var.get()
        work_order_id = self.work_order_map.get(selected_work_order)

        if not work_order_id:
            messagebox.showwarning(
                "Selection Required",
                "Please select a work order first.",
            )
            return

        try:
            response = self.invoice_controller.generate_invoice_from_work_order(
                work_order_id=work_order_id,
                tax_rate=float(self.tax_rate_var.get() or 0),
                discount_amount=float(self.discount_var.get() or 0),
            )

            if not response.success:
                messagebox.showerror("Error", response.message)
                return

            self.selected_invoice_number_var.set(
                response.data.get("invoice_number", "")
            )

            messagebox.showinfo("Success", response.message)
            self._load_all_invoices()

        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _load_all_invoices(self) -> None:
        response = self.invoice_controller.get_all_invoices()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.tree.delete(*self.tree.get_children())

        for invoice in response.data or []:
            self.tree.insert(
                "",
                "end",
                values=(
                    invoice.get("id", ""),
                    invoice.get("invoice_number", ""),
                    invoice.get("work_order_id", ""),
                    invoice.get("customer_name", ""),
                    invoice.get("grand_total", ""),
                    invoice.get("payment_status", ""),
                ),
            )

    def _on_invoice_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        if not values:
            return

        self.invoice_id_var.set(str(values[0]))
        self.selected_invoice_number_var.set(str(values[1]))

    def _mark_paid(self) -> None:
        invoice_id = self.invoice_id_var.get().strip()
        if not invoice_id:
            messagebox.showwarning(
                "Selection Required",
                "Select an invoice row first.",
            )
            return

        response = self.invoice_controller.mark_invoice_paid(
            invoice_id=int(invoice_id),
            payment_method_summary=self.payment_method_summary_var.get().strip() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_invoices()

    def _mark_partial(self) -> None:
        invoice_id = self.invoice_id_var.get().strip()
        if not invoice_id:
            messagebox.showwarning(
                "Selection Required",
                "Select an invoice row first.",
            )
            return

        response = self.invoice_controller.mark_invoice_partial(
            invoice_id=int(invoice_id),
            payment_method_summary=self.payment_method_summary_var.get().strip() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_invoices()

    def _view_invoice(self) -> None:
        invoice_number = self.selected_invoice_number_var.get().strip()

        if not invoice_number:
            messagebox.showwarning(
                "Selection Required",
                "Select an invoice row first.",
            )
            return

        response = self.invoice_controller.get_invoice(invoice_number)

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        invoice = response.data.get("invoice", {})
        items = response.data.get("items", [])

        lines = [
            f"Invoice Number: {invoice.get('invoice_number', '')}",
            f"Work Order ID: {invoice.get('work_order_id', '')}",
            f"Customer: {invoice.get('customer_name', '')}",
            f"Grand Total: ${invoice.get('grand_total', 0)}",
            f"Payment Status: {invoice.get('payment_status', '')}",
            "",
            "Items:",
        ]

        for item in items:
            lines.append(
                f"- {item.get('item_type', '')}: "
                f"{item.get('description', '')} "
                f"(${item.get('line_total', 0)})"
            )

        messagebox.showinfo("Invoice Details", "\n".join(lines))

    def on_show(self) -> None:
        self._load_work_orders()
        self._load_all_invoices()