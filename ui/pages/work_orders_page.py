"""
ui/pages/work_orders_page.py

Work Order Management page for GaragePulse using shared AppShell.

Updates:
- searchable customer selector instead of dropdown
- compact customer search layout
- customer results collapse after selection
- removed create-section Work Order ID input
- compressed layout and cleaner alignment
- same size for entries and dropdowns
- removed required markers from parts section
- filtered owner from Assign Staff dropdown
- keeps multi-vehicle-per-customer behavior
- fixes STAFF access issue on page load
- fixes row selection work order loading bug
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from config.constants import WORK_ORDER_STATUS_LIST
from services.session_service import SessionService
from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class WorkOrdersPage(AppShell):
    """
    Work Orders management page with shared app shell.
    """

    LEFT_PANEL_WIDTH = 340
    FIELD_PADX = 16

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="work_orders",
            page_title="Work Order Management",
        )

        self.work_order_controller = app.get_controller("work_order")
        self.customer_controller = app.get_controller("customer")
        self.vehicle_controller = app.get_controller("vehicle")
        self.user_controller = app.get_controller("user")

        self.selected_work_order_id_var = tk.StringVar()
        self.selected_work_order_code_var = tk.StringVar()

        self.customer_search_var = tk.StringVar()
        self.selected_customer_display_var = tk.StringVar()
        self.vehicle_var = tk.StringVar()
        self.staff_var = tk.StringVar()
        self.issue_var = tk.StringVar()


        self.status_var = tk.StringVar(value="NEW")
        self.status_note_var = tk.StringVar()

        self.labor_cost_var = tk.StringVar()

        self.part_name_var = tk.StringVar()
        self.part_quantity_var = tk.StringVar(value="1")
        self.part_unit_price_var = tk.StringVar(value="0")
        self.part_source_var = tk.StringVar(value="SHOP")
        self.part_billable_var = tk.BooleanVar(value=True)
        self.part_notes_var = tk.StringVar()

        self.selected_customer_id: int | None = None
        self.vehicle_map: dict[str, int] = {}
        self.staff_map: dict[str, int] = {}

        self._build_page_content()

    def _build_page_content(self) -> None:
        self.content.grid_columnconfigure(0, weight=0, minsize=self.LEFT_PANEL_WIDTH)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        left_outer = tk.Frame(
            self.content,
            bg=self.CONTENT_BG,
            width=self.LEFT_PANEL_WIDTH,
        )
        left_outer.grid(row=0, column=0, sticky="ns", padx=(0, 10))
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
            width=self.LEFT_PANEL_WIDTH - 18,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.CONTENT_BG)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_work_order_card(scrollable)
        self._build_cost_parts_card(scrollable)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _add_label(self, parent: tk.Frame, row: int, text: str, required: bool = False) -> None:
        label_text = f"{text} *" if required else text
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10, "bold" if required else "normal"),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 4))

    def _make_entry(self, parent: tk.Frame, textvariable, state="normal") -> tk.Entry:
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

    def _make_text_field(
        self,
        parent: tk.Frame,
        row: int,
        variable,
        state="normal",
        pady=(0, 8),
    ) -> tk.Entry:
        entry = self._make_entry(parent, variable, state=state)
        entry.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=pady, ipady=4)
        return entry

    def _make_combo(
        self,
        parent: tk.Frame,
        row: int,
        variable,
        values=None,
        state="readonly",
        pady=(0, 8),
    ) -> ttk.Combobox:
        combo = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values or [],
            state=state,
        )
        combo.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=pady)
        return combo

    def _make_primary_button(self, parent: tk.Frame, text: str, command, row: int, pady=(0, 10)) -> None:
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

    def _make_secondary_button(self, parent: tk.Frame, text: str, command, row: int, pady=(0, 10)) -> None:
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

    def _make_separator(self, parent: tk.Frame, row: int, pady=6) -> None:
        tk.Frame(parent, bg="#e2e8f0", height=1).grid(
            row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=pady
        )

    def _clear_customer_results(self) -> None:
        for item in self.customer_results_tree.get_children():
            self.customer_results_tree.delete(item)
        self.customer_results_frame.grid_remove()

    def _show_customer_results(self) -> None:
        self.customer_results_frame.grid()

    def _build_work_order_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.pack(fill="x", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            card,
            text="Work Order Details",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(16, 4))

        row += 1
        self.loaded_work_order_label = tk.Label(
            card,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.CARD_BG,
            fg="#2563eb",
        )
        self.loaded_work_order_label.grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 2))
        self.loaded_work_order_label.grid_remove()

        row += 1
        self._add_label(card, row, "Customer Search", required=True)
        row += 1

        search_frame = tk.Frame(card, bg=self.CARD_BG)
        search_frame.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 6))
        search_frame.grid_columnconfigure(0, weight=1)

        self.customer_search_entry = tk.Entry(
            search_frame,
            textvariable=self.customer_search_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        self.customer_search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=4)
        self.customer_search_entry.bind("<Return>", self._handle_customer_search)

        tk.Button(
            search_frame,
            text="Go",
            command=self._handle_customer_search,
            font=("Segoe UI", 9, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            width=4,
            padx=6,
            pady=8,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="ew")

        row += 1
        self.customer_results_frame = tk.Frame(card, bg=self.CARD_BG)
        self.customer_results_frame.grid(row=row, column=0, sticky="ew", padx=self.FIELD_PADX, pady=(0, 6))
        self.customer_results_frame.grid_columnconfigure(0, weight=1)
        self.customer_results_frame.grid_rowconfigure(0, weight=1)

        self.customer_results_tree = ttk.Treeview(
            self.customer_results_frame,
            columns=("name", "phone"),
            show="headings",
            height=2,
        )
        self.customer_results_tree.grid(row=0, column=0, sticky="ew")
        self.customer_results_tree.heading("name", text="Customer")
        self.customer_results_tree.heading("phone", text="Phone")
        self.customer_results_tree.column("name", width=180, anchor="w")
        self.customer_results_tree.column("phone", width=100, anchor="w")
        self.customer_results_tree.bind("<<TreeviewSelect>>", self._on_customer_result_selected)

        customer_scrollbar = ttk.Scrollbar(
            self.customer_results_frame,
            orient="vertical",
            command=self.customer_results_tree.yview,
        )
        customer_scrollbar.grid(row=0, column=1, sticky="ns")
        self.customer_results_tree.configure(yscrollcommand=customer_scrollbar.set)
        self.customer_results_frame.grid_remove()

        row += 1
        self._add_label(card, row, "Selected Customer", required=False)
        row += 1
        self.selected_customer_entry = self._make_text_field(
            card,
            row,
            self.selected_customer_display_var,
            state="readonly",
        )

        row += 1
        self._add_label(card, row, "Vehicle", required=True)
        row += 1
        self.vehicle_combo = self._make_combo(card, row, self.vehicle_var)

        row += 1
        self._add_label(card, row, "Assign Staff")
        row += 1
        self.staff_combo = self._make_combo(card, row, self.staff_var)

        row += 1
        self._add_label(card, row, "Issue Description", required=True)
        row += 1
        self.issue_entry = self._make_text_field(card, row, self.issue_var)

        row += 1


        row += 1
        self._make_primary_button(card, "Create Work Order", self._create_work_order, row, pady=(0, 10))

        row += 1
        self._make_separator(card, row, pady=6)

        row += 1
        self._add_label(card, row, "Selected Work Order ID")
        row += 1
        self.selected_work_order_entry = self._make_text_field(
            card,
            row,
            self.selected_work_order_code_var,
            state="readonly",
        )

        row += 1
        self._add_label(card, row, "Update Status", required=True)
        row += 1
        self.status_combo = self._make_combo(
            card,
            row,
            self.status_var,
            values=WORK_ORDER_STATUS_LIST,
        )

        row += 1
        self._add_label(card, row, "Status Note")
        row += 1
        self.status_note_entry = self._make_text_field(card, row, self.status_note_var)

        row += 1
        self._make_secondary_button(card, "Update Status", self._update_status, row, pady=(0, 16))

    def _build_cost_parts_card(self, parent: tk.Frame) -> None:
        card = tk.Frame(parent, bg=self.CARD_BG)
        card.pack(fill="x")
        card.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            card,
            text="Parts / Labor",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(16, 8))

        row += 1
        self._add_label(card, row, "Labor Cost")
        row += 1
        self.labor_cost_entry = self._make_text_field(card, row, self.labor_cost_var)

        row += 1
        self._make_secondary_button(card, "Update Labor Cost", self._update_labor_cost, row)

        row += 1
        self._make_separator(card, row, pady=6)

        row += 1
        self._add_label(card, row, "Part Name")
        row += 1
        self.part_name_entry = self._make_text_field(card, row, self.part_name_var)

        row += 1
        self._add_label(card, row, "Quantity")
        row += 1
        self.part_quantity_entry = self._make_text_field(card, row, self.part_quantity_var)

        row += 1
        self._add_label(card, row, "Unit Price")
        row += 1
        self.part_unit_price_entry = self._make_text_field(card, row, self.part_unit_price_var)

        row += 1
        self._add_label(card, row, "Part Source")
        row += 1
        self.part_source_combo = self._make_combo(
            card,
            row,
            self.part_source_var,
            values=["SHOP", "CUSTOMER"],
        )

        row += 1
        tk.Checkbutton(
            card,
            text="Billable",
            variable=self.part_billable_var,
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
            activebackground=self.CARD_BG,
            selectcolor=self.CARD_BG,
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, sticky="w", padx=self.FIELD_PADX, pady=(0, 8))

        row += 1
        self._add_label(card, row, "Part Notes")
        row += 1
        self.part_notes_entry = self._make_text_field(card, row, self.part_notes_var)

        row += 1
        self._make_secondary_button(card, "Add Part", self._add_part, row, pady=(0, 16))

    def _build_list_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        tk.Label(
            parent,
            text="Work Order Records",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 10))

        table_frame = tk.Frame(parent, bg=self.CARD_BG)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = (
            "work_order_id",
            "customer_name",
            "plate_number",
            "assigned_staff",
            "current_status",
            "labor_cost",
            "parts_total",
            "subtotal",
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
            "work_order_id": "Work Order ID",
            "customer_name": "Customer",
            "plate_number": "Plate Number",
            "assigned_staff": "Assigned Staff",
            "current_status": "Status",
            "labor_cost": "Labor",
            "parts_total": "Parts",
            "subtotal": "Subtotal",
        }

        widths = {
            "work_order_id": 160,
            "customer_name": 170,
            "plate_number": 140,
            "assigned_staff": 150,
            "current_status": 120,
            "labor_cost": 90,
            "parts_total": 90,
            "subtotal": 100,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

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
            command=self._load_all_work_orders,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
        ).grid(row=2, column=0, sticky="e", padx=18, pady=(0, 18))

    def _handle_customer_search(self, event=None) -> None:
        search_text = self.customer_search_var.get().strip()

        self._clear_customer_results()
        self.selected_customer_id = None
        self.selected_customer_display_var.set("")
        self.vehicle_var.set("")
        self.vehicle_combo["values"] = []
        self.vehicle_map.clear()

        if not search_text:
            messagebox.showwarning("Input Required", "Enter customer name or phone to search.")
            self.customer_search_entry.focus_set()
            return

        response = self.customer_controller.search_customers(search_text)
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        matches = response.data or []

        if not matches:
            messagebox.showinfo("No Match Found", "No customer found for the entered search.")
            return

        self._show_customer_results()

        for customer in matches:
            customer_id = str(customer.get("id", ""))
            full_name = (
                customer.get("full_name")
                or f"{str(customer.get('first_name', '')).strip()} {str(customer.get('last_name', '')).strip()}".strip()
            )
            phone = str(customer.get("phone", "") or "")
            self.customer_results_tree.insert(
                "",
                "end",
                iid=customer_id,
                values=(full_name, phone),
            )

        if len(matches) == 1:
            first_id = str(matches[0].get("id", ""))
            self.customer_results_tree.selection_set(first_id)
            self.customer_results_tree.focus(first_id)
            self._on_customer_result_selected()

    def _on_customer_result_selected(self, event=None) -> None:
        selected = self.customer_results_tree.focus()
        if not selected:
            selection = self.customer_results_tree.selection()
            if not selection:
                return
            selected = selection[0]

        response = self.customer_controller.get_customer(int(selected))
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        customer = response.data or {}
        full_name = (
            customer.get("full_name")
            or f"{str(customer.get('first_name', '')).strip()} {str(customer.get('last_name', '')).strip()}".strip()
        )
        phone = str(customer.get("phone", "") or "")

        self.selected_customer_id = int(selected)
        self.selected_customer_display_var.set(f"{full_name} | {phone}")
        self._load_vehicles_for_customer(self.selected_customer_id)
        self._clear_customer_results()

    def _load_vehicles_for_customer(self, customer_id: int) -> None:
        self.vehicle_var.set("")
        self.vehicle_combo["values"] = []
        self.vehicle_map.clear()

        response = self.vehicle_controller.get_by_customer_id(customer_id)
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        display_values = []
        for vehicle in response.data or []:
            year_val = vehicle.get("vehicle_year") or vehicle.get("year") or ""
            display = (
                f"{vehicle.get('plate_number')} | "
                f"{year_val} {vehicle.get('make')} {vehicle.get('model')}"
            )
            self.vehicle_map[display] = int(vehicle["id"])
            display_values.append(display)

        self.vehicle_combo["values"] = display_values

        if display_values:
            self.vehicle_combo.current(0)

    def _load_staff(self) -> None:
        self.staff_map.clear()
        display_values = []

        current_user = SessionService.get_current_user() or {}
        current_role = str(current_user.get("role_code", "") or "").strip().upper()

        if current_role == "STAFF":
            user_id = current_user.get("id")
            username = current_user.get("username", "")
            role_code = current_user.get("role_code", "STAFF")

            if user_id:
                display = f"{username} | {role_code}"
                self.staff_map[display] = int(user_id)
                display_values.append(display)

            self.staff_combo["values"] = display_values
            if display_values:
                self.staff_var.set(display_values[0])
            else:
                self.staff_var.set("")
            return

        response = self.user_controller.get_active_users()
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        for user in response.data or []:
            role_code = str(user.get("role_code", "") or "").strip().lower()
            if role_code == "owner":
                continue

            display = f"{user.get('username')} | {user.get('role_code')}"
            self.staff_map[display] = int(user["id"])
            display_values.append(display)

        self.staff_combo["values"] = display_values

        if self.staff_var.get() and self.staff_var.get() not in display_values:
            self.staff_var.set("")

        if not self.staff_var.get() and display_values:
            self.staff_var.set(display_values[0])

    def _load_work_order_into_form(self, work_order: dict) -> None:
        self.selected_work_order_id_var.set(str(work_order.get("id", "")))
        self.selected_work_order_code_var.set(str(work_order.get("work_order_id", "")))
        self.status_var.set(str(work_order.get("current_status", "") or "NEW"))
        self.labor_cost_var.set(str(work_order.get("labor_cost", "") or ""))
        self.loaded_work_order_label.config(
            text=f"Editing work order: {work_order.get('work_order_id', '')}"
        )
        self.loaded_work_order_label.grid()

    def _create_work_order(self) -> None:
        vehicle_display = self.vehicle_var.get()
        staff_display = self.staff_var.get()

        customer_id = self.selected_customer_id
        vehicle_id = self.vehicle_map.get(vehicle_display)
        staff_id = self.staff_map.get(staff_display) if staff_display else None

        if not customer_id:
            messagebox.showwarning("Input Required", "Please search and select a customer.")
            self.customer_search_entry.focus_set()
            return

        if not vehicle_id:
            messagebox.showwarning("Input Required", "Please select a vehicle.")
            return

        if not self.issue_var.get().strip():
            messagebox.showwarning("Input Required", "Issue Description is required.")
            self.issue_entry.focus_set()
            return

        response = self.work_order_controller.create_work_order(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            issue_description=self.issue_var.get().strip(),
            assigned_staff_id=staff_id,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self.issue_var.set("")
        self.customer_search_var.set("")
        self.selected_customer_display_var.set("")
        self.selected_customer_id = None
        self.vehicle_var.set("")
        self.vehicle_combo["values"] = []
        self.vehicle_map.clear()
        self.staff_var.set("")
        self._clear_customer_results()
        self._load_staff()
        self._load_all_work_orders()

    def _load_all_work_orders(self) -> None:
        response = self.work_order_controller.get_all_work_orders()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.tree.delete(*self.tree.get_children())

        for row in response.data or []:
            internal_id = str(row.get("id", ""))
            self.tree.insert(
                "",
                "end",
                iid=internal_id,
                values=(
                    row.get("work_order_id", ""),
                    row.get("customer_name", ""),
                    row.get("plate_number", ""),
                    row.get("assigned_staff", ""),
                    row.get("current_status", ""),
                    row.get("labor_cost", 0),
                    row.get("parts_total", 0),
                    row.get("subtotal", 0),
                ),
            )

    def _on_row_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        if not values:
            return

        work_order_code = str(values[0]).strip()

        if hasattr(self.work_order_controller, "get_work_order") and work_order_code:
            response = self.work_order_controller.get_work_order(work_order_code)
            if response.success and isinstance(response.data, dict):
                work_order = response.data.get("work_order") or response.data
                if isinstance(work_order, dict):
                    self._load_work_order_into_form(work_order)
                    return

        self.selected_work_order_id_var.set(str(selected))
        self.selected_work_order_code_var.set(work_order_code)
        self.status_var.set(str(values[4]))
        self.labor_cost_var.set(str(values[5]))
        self.loaded_work_order_label.config(text=f"Editing work order: {work_order_code}")
        self.loaded_work_order_label.grid()

    def _update_status(self) -> None:
        internal_id = self.selected_work_order_id_var.get().strip()
        if not internal_id:
            messagebox.showwarning(
                "Selection Required",
                "Load or select a work order first.",
            )
            return

        response = self.work_order_controller.update_status(
            work_order_id=int(internal_id),
            new_status=self.status_var.get(),
            status_note=self.status_note_var.get() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self.status_note_var.set("")
        self._load_all_work_orders()

    def _update_labor_cost(self) -> None:
        internal_id = self.selected_work_order_id_var.get().strip()
        if not internal_id:
            messagebox.showwarning(
                "Selection Required",
                "Load or select a work order first.",
            )
            return

        try:
            labor_cost = float(self.labor_cost_var.get() or 0)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Labor cost must be a number.")
            return

        response = self.work_order_controller.set_labor_cost(
            work_order_id=int(internal_id),
            labor_cost=labor_cost,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._load_all_work_orders()

    def _add_part(self) -> None:
        internal_id = self.selected_work_order_id_var.get().strip()
        if not internal_id:
            messagebox.showwarning(
                "Selection Required",
                "Load or select a work order first.",
            )
            return

        part_name = self.part_name_var.get().strip()
        if not part_name:
            messagebox.showwarning("Input Required", "Part Name is required.")
            self.part_name_entry.focus_set()
            return

        try:
            quantity = int(self.part_quantity_var.get() or 1)
            unit_price = float(self.part_unit_price_var.get() or 0)
        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                "Quantity must be integer and unit price must be numeric.",
            )
            return

        response = self.work_order_controller.add_part(
            work_order_id=int(internal_id),
            part_name=part_name,
            quantity=quantity,
            unit_price=unit_price,
            part_source=self.part_source_var.get(),
            is_billable=self.part_billable_var.get(),
            notes=self.part_notes_var.get().strip() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self.part_name_var.set("")
        self.part_quantity_var.set("1")
        self.part_unit_price_var.set("0")
        self.part_source_var.set("SHOP")
        self.part_billable_var.set(True)
        self.part_notes_var.set("")
        self._load_all_work_orders()

    def on_show(self) -> None:
        self._build_sidebar()
        self._load_staff()
        self._load_all_work_orders()