"""
ui/pages/invoices_page.py

Invoices page for GaragePulse using shared AppShell.

Features:
- type-and-load workflow using invoice number + Enter
- cleaner production-style layout
- mandatory markers on key generate/update fields
- equal-size update action buttons
- payment status filter limited to ALL / PENDING / PAID / PARTIAL
- auto refresh and auto highlight after generate/update
- fixed row selection for update / PDF / mark paid / mark partial
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class InvoicesPage(AppShell):
    """
    Invoice management page with shared app shell.
    """

    LEFT_PANEL_WIDTH = 390
    FIELD_PADX = 14

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="invoices",
            page_title="Invoices",
        )

        self.invoice_controller = app.get_controller("invoice")
        self.work_order_controller = app.get_controller("work_order")

        self.selected_invoice_id_var = tk.StringVar()
        self.invoice_lookup_var = tk.StringVar()

        self.work_order_var = tk.StringVar()
        self.tax_rate_var = tk.StringVar(value="6")
        self.discount_amount_var = tk.StringVar(value="0")
        self.invoice_number_var = tk.StringVar()
        self.payment_method_var = tk.StringVar(value="Cash")

        self.update_invoice_number_var = tk.StringVar()
        self.payment_status_var = tk.StringVar(value="PENDING")
        self.partial_amount_var = tk.StringVar(value="0")
        self.status_filter_var = tk.StringVar(value="ALL")

        self.work_order_map: dict[str, int] = {}

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

        self._build_scrollable_left_panel(left_outer)
        self._build_list_panel(right_card)

    def _build_scrollable_left_panel(self, parent: tk.Frame) -> None:
        container = tk.Frame(parent, bg=self.CONTENT_BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            bg=self.CONTENT_BG,
            highlightthickness=0,
            width=self.LEFT_PANEL_WIDTH - 16,
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

        self._build_generate_invoice_card(scrollable)
        self._build_invoice_update_card(scrollable)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ------------------------------------------------------------------
    # SHARED UI HELPERS
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

    def _make_primary_button(self, parent: tk.Frame, text: str, command, row: int, pady=(0, 12)) -> None:
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
            pady=11,
            cursor="hand2",
        ).grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=pady)

    # ------------------------------------------------------------------
    # LEFT PANEL
    # ------------------------------------------------------------------
    def _build_generate_invoice_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.pack(fill="x", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            card,
            text="Generate Invoice",
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

        row += 1
        self._add_label(card, row, "Tax Rate (%)", required=True)
        row += 1
        self.tax_rate_entry = self._make_entry(card, self.tax_rate_var)
        self.tax_rate_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=3)

        row += 1
        self._add_label(card, row, "Discount Amount")
        row += 1
        self.discount_amount_entry = self._make_entry(card, self.discount_amount_var)
        self.discount_amount_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=3)

        row += 1
        self._add_label(card, row, "Invoice Number")
        row += 1
        self.invoice_number_entry = self._make_entry(card, self.invoice_number_var)
        self.invoice_number_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=3)

        row += 1
        self._add_label(card, row, "Payment Method", required=True)
        row += 1
        self.payment_method_combo = ttk.Combobox(
            card,
            textvariable=self.payment_method_var,
            values=["Cash", "Card", "Bank Transfer", "Check", "Other"],
            state="readonly",
        )
        self.payment_method_combo.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 10))

        row += 1
        self._make_primary_button(card, "Generate Invoice", self._generate_invoice, row, pady=(0, 18))

    def _build_invoice_update_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.pack(fill="x")
        card.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            card,
            text="Invoice Update",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(18, 12))

        row += 1
        tk.Label(
            card,
            text="Type invoice number and press Enter, or select from the records table",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
            wraplength=self.LEFT_PANEL_WIDTH - 44,
            justify="left",
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 6))

        row += 1
        self.loaded_invoice_label = tk.Label(
            card,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.CARD_BG,
            fg="#2563eb",
            wraplength=self.LEFT_PANEL_WIDTH - 44,
            justify="left",
        )
        self.loaded_invoice_label.grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 8))
        self.loaded_invoice_label.grid_remove()

        row += 1
        self._add_label(card, row, "Invoice Lookup")
        row += 1
        lookup_entry = self._make_entry(card, self.invoice_lookup_var)
        lookup_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=3)
        lookup_entry.bind("<Return>", self._handle_type_and_load)

        row += 1
        self._add_label(card, row, "Selected Invoice", required=True)
        row += 1
        self.selected_invoice_entry = self._make_entry(card, self.update_invoice_number_var, state="readonly")
        self.selected_invoice_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8), ipady=3)

        row += 1
        self._add_label(card, row, "Payment Status", required=True)
        row += 1
        self.payment_status_combo = ttk.Combobox(
            card,
            textvariable=self.payment_status_var,
            values=["PENDING", "PAID", "PARTIAL"],
            state="readonly",
        )
        self.payment_status_combo.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 8))

        row += 1
        self._add_label(card, row, "Partial Paid Amount")
        row += 1
        self.partial_amount_entry = self._make_entry(card, self.partial_amount_var)
        self.partial_amount_entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 10), ipady=3)

        row += 1
        action_grid = tk.Frame(card, bg=self.CARD_BG)
        action_grid.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 18))
        action_grid.grid_columnconfigure(0, weight=1, uniform="invoice_actions")
        action_grid.grid_columnconfigure(1, weight=1, uniform="invoice_actions")

        common_button = {
            "font": ("Segoe UI", 10, "bold"),
            "bg": "#2563eb",
            "fg": "white",
            "activebackground": "#1d4ed8",
            "activeforeground": "white",
            "relief": "flat",
            "bd": 0,
            "padx": 8,
            "pady": 10,
            "cursor": "hand2",
        }

        tk.Button(action_grid, text="Mark Paid", command=self._mark_paid, **common_button).grid(
            row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8)
        )
        tk.Button(action_grid, text="Mark Partial", command=self._mark_partial, **common_button).grid(
            row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8)
        )
        tk.Button(action_grid, text="Download PDF", command=self._download_invoice_pdf, **common_button).grid(
            row=1, column=0, sticky="ew", padx=(0, 5)
        )
        tk.Button(action_grid, text="Clear", command=self._clear_invoice_update_form, **common_button).grid(
            row=1, column=1, sticky="ew", padx=(5, 0)
        )

    # ------------------------------------------------------------------
    # RIGHT PANEL
    # ------------------------------------------------------------------
    def _build_list_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        tk.Label(
            parent,
            text="Invoice Records",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(18, 12))

        filter_frame = tk.Frame(parent, bg=self.CARD_BG)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        filter_frame.grid_columnconfigure(2, weight=1)

        tk.Label(
            filter_frame,
            text="Payment Status",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=0, column=0, padx=(0, 8))

        self.status_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_filter_var,
            values=["ALL", "PENDING", "PAID", "PARTIAL"],
            state="readonly",
            width=14,
        )
        self.status_filter_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.status_filter_combo.bind("<<ComboboxSelected>>", self._apply_status_filter)

        tk.Button(
            filter_frame,
            text="Refresh",
            command=self._load_all_invoices,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
        ).grid(row=0, column=3, sticky="e")

        table_frame = tk.Frame(parent, bg=self.CARD_BG)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 18))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = (
            "invoice_number",
            "work_order_id",
            "customer_name",
            "grand_total",
            "payment_status",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

        headings = {
            "invoice_number": "Invoice Number",
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "grand_total": "Grand Total",
            "payment_status": "Payment Status",
        }

        widths = {
            "invoice_number": 150,
            "work_order_id": 150,
            "customer_name": 180,
            "grand_total": 110,
            "payment_status": 120,
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

        for wo in response.data or []:
            display = (
                f"{wo.get('work_order_id')} | "
                f"{wo.get('customer_name', '')} | "
                f"{wo.get('plate_number', '')}"
            )
            self.work_order_map[display] = int(wo["id"])
            display_values.append(display)

        self.work_order_combo["values"] = display_values

    def _load_invoice_into_form(self, invoice: dict) -> None:
        invoice_number = str(invoice.get("invoice_number", "") or "")
        payment_status = str(invoice.get("payment_status", "") or "PENDING")

        self.selected_invoice_id_var.set(str(invoice.get("id", "")))
        self.invoice_lookup_var.set(invoice_number)
        self.update_invoice_number_var.set(invoice_number)
        self.payment_status_var.set(payment_status)
        self.loaded_invoice_label.config(text=f"Editing invoice: {invoice_number}")
        self.loaded_invoice_label.grid()

    def _handle_type_and_load(self, event=None) -> None:
        invoice_number = self.invoice_lookup_var.get().strip()
        if not invoice_number:
            messagebox.showwarning("Search Required", "Type an invoice number and press Enter.")
            return

        response = None
        if hasattr(self.invoice_controller, "get_by_invoice_number"):
            response = self.invoice_controller.get_by_invoice_number(invoice_number)
        elif hasattr(self.invoice_controller, "get_invoice_by_number"):
            response = self.invoice_controller.get_invoice_by_number(invoice_number)
        else:
            response = self.invoice_controller.get_all_invoices()
            if response.success:
                rows = response.data or []
                match = next(
                    (row for row in rows if str(row.get("invoice_number", "")).strip() == invoice_number),
                    None,
                )
                response.data = match
                response.success = match is not None
                response.message = "Invoice found." if match else "Invoice not found."

        if not response.success:
            messagebox.showinfo("No Match Found", "No matching invoice was found.")
            return

        invoice = response.data or {}
        self._load_invoice_into_form(invoice)

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and str(values[0]).strip() == invoice_number:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                break

    # ------------------------------------------------------------------
    # GENERATE / LOAD / FILTER
    # ------------------------------------------------------------------
    def _generate_invoice(self) -> None:
        work_order_display = self.work_order_var.get()
        work_order_id = self.work_order_map.get(work_order_display)

        if not work_order_id:
            messagebox.showwarning("Input Required", "Please select a work order.")
            return

        tax_text = self.tax_rate_var.get().strip()
        if not tax_text:
            messagebox.showwarning("Input Required", "Tax rate is required.")
            self.tax_rate_entry.focus_set()
            return

        if not self.payment_method_var.get().strip():
            messagebox.showwarning("Input Required", "Payment method is required.")
            return

        try:
            tax_rate = float(tax_text)
            discount_amount = float(self.discount_amount_var.get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Tax rate and discount must be numeric values.")
            return

        response = self.invoice_controller.generate_invoice(
            work_order_id=work_order_id,
            tax_rate=tax_rate,
            discount_amount=discount_amount,
            invoice_number=self.invoice_number_var.get().strip() or None,
            payment_method_summary=self.payment_method_var.get().strip() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self.invoice_number_var.set("")
        self.discount_amount_var.set("0")

        self.status_filter_var.set("ALL")
        self._apply_status_filter()
        self._highlight_invoice_by_work_order(work_order_id)

    def _load_all_invoices(self) -> None:
        self._apply_status_filter()

    def _populate_tree(self, invoices: list[dict]) -> None:
        self.tree.delete(*self.tree.get_children())

        for row in invoices:
            invoice_id = str(row.get("id", ""))
            self.tree.insert(
                "",
                "end",
                iid=invoice_id,
                values=(
                    row.get("invoice_number", ""),
                    row.get("work_order_id", ""),
                    row.get("customer_name", ""),
                    row.get("grand_total", 0),
                    row.get("payment_status", ""),
                ),
            )

    def _apply_status_filter(self, event=None) -> None:
        response = self.invoice_controller.get_all_invoices()
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        rows = response.data or []
        selected_status = self.status_filter_var.get().strip().upper()

        if selected_status == "ALL":
            self._populate_tree(rows)
            return

        filtered = [
            row for row in rows
            if str(row.get("payment_status", "")).upper() == selected_status
        ]
        self._populate_tree(filtered)

    def _highlight_invoice_by_work_order(self, work_order_id: int) -> None:
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and str(values[1]) == str(work_order_id):
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                self._on_row_selected()
                break

    # ------------------------------------------------------------------
    # ROW SELECTION
    # ------------------------------------------------------------------
    def _on_row_selected(self, event=None) -> None:
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected = selected_items[0]
        values = self.tree.item(selected, "values")
        if not values:
            return

        invoice_id = str(selected).strip()
        invoice_number = str(values[0]).strip()

        self.selected_invoice_id_var.set(invoice_id)
        self.invoice_lookup_var.set(invoice_number)
        self.update_invoice_number_var.set(invoice_number)
        self.loaded_invoice_label.config(text=f"Editing invoice: {invoice_number}")
        self.loaded_invoice_label.grid()

        response = None
        if hasattr(self.invoice_controller, "get_by_invoice_number"):
            response = self.invoice_controller.get_by_invoice_number(invoice_number)
        elif hasattr(self.invoice_controller, "get_invoice_by_number"):
            response = self.invoice_controller.get_invoice_by_number(invoice_number)

        if response and response.success:
            invoice = response.data or {}
            self._load_invoice_into_form(invoice)
            return

        if len(values) >= 5:
            self.payment_status_var.set(str(values[4] or "PENDING"))

    # ------------------------------------------------------------------
    # PAYMENT ACTIONS
    # ------------------------------------------------------------------
    def _mark_paid(self) -> None:
        invoice_id = self.selected_invoice_id_var.get().strip()

        if not invoice_id:
            selected_items = self.tree.selection()
            if selected_items:
                invoice_id = str(selected_items[0]).strip()
                self.selected_invoice_id_var.set(invoice_id)

        if not invoice_id:
            messagebox.showwarning("Selection Required", "Load or select an invoice first.")
            return

        if hasattr(self.invoice_controller, "mark_paid"):
            response = self.invoice_controller.mark_paid(int(invoice_id))
        else:
            response = self.invoice_controller.update_payment_status(
                invoice_id=int(invoice_id),
                payment_status="PAID",
            )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_invoices()
        self._reselect_invoice(invoice_id)

    def _mark_partial(self) -> None:
        invoice_id = self.selected_invoice_id_var.get().strip()

        if not invoice_id:
            selected_items = self.tree.selection()
            if selected_items:
                invoice_id = str(selected_items[0]).strip()
                self.selected_invoice_id_var.set(invoice_id)

        if not invoice_id:
            messagebox.showwarning("Selection Required", "Load or select an invoice first.")
            return

        try:
            partial_amount = float(self.partial_amount_var.get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Partial paid amount must be numeric.")
            return

        if partial_amount <= 0:
            messagebox.showwarning("Invalid Input", "Enter the amount paid by the customer.")
            return

        if hasattr(self.invoice_controller, "mark_partial"):
            response = self.invoice_controller.mark_partial(
                invoice_id=int(invoice_id),
                paid_amount=partial_amount,
            )
        else:
            response = self.invoice_controller.update_payment_status(
                invoice_id=int(invoice_id),
                payment_status="PARTIAL",
                paid_amount=partial_amount,
            )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_invoices()
        self._reselect_invoice(invoice_id)

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def _download_invoice_pdf(self) -> None:
        invoice_id = self.selected_invoice_id_var.get().strip()

        if not invoice_id:
            selected_items = self.tree.selection()
            if selected_items:
                invoice_id = str(selected_items[0]).strip()
                self.selected_invoice_id_var.set(invoice_id)

        if not invoice_id:
            messagebox.showwarning("Selection Required", "Load or select an invoice first.")
            return

        response = None
        if hasattr(self.invoice_controller, "generate_invoice_pdf"):
            response = self.invoice_controller.generate_invoice_pdf(int(invoice_id))
        elif hasattr(self.invoice_controller, "download_invoice_pdf"):
            response = self.invoice_controller.download_invoice_pdf(int(invoice_id))
        else:
            messagebox.showerror("PDF Not Available", "Invoice PDF download method is missing in the controller.")
            return

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        pdf_path = ""
        if isinstance(response.data, dict):
            pdf_path = str(response.data.get("pdf_path", "") or response.data.get("file_path", "") or "")
        elif isinstance(response.data, str):
            pdf_path = response.data

        if pdf_path:
            messagebox.showinfo("Success", f"Invoice PDF downloaded successfully.\n\nSaved to:\n{pdf_path}")
        else:
            messagebox.showinfo("Success", response.message)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _reselect_invoice(self, invoice_id: str) -> None:
        if invoice_id in self.tree.get_children():
            self.tree.selection_set(invoice_id)
            self.tree.focus(invoice_id)
            self.tree.see(invoice_id)
            self._on_row_selected()

    # ------------------------------------------------------------------
    # CLEAR
    # ------------------------------------------------------------------
    def _clear_invoice_update_form(self) -> None:
        self.selected_invoice_id_var.set("")
        self.invoice_lookup_var.set("")
        self.update_invoice_number_var.set("")
        self.payment_status_var.set("PENDING")
        self.partial_amount_var.set("0")
        self.loaded_invoice_label.config(text="")
        self.loaded_invoice_label.grid_remove()

        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    # ------------------------------------------------------------------
    # SHOW
    # ------------------------------------------------------------------
    def on_show(self) -> None:
        self._build_sidebar()
        self._load_work_orders()
        self._load_all_invoices()