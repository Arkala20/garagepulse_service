"""
ui/pages/work_orders_page.py

Production-style Work Orders page for GaragePulse.

Upgrades from prototype:
- customer selection via dropdown
- vehicle dropdown filtered by selected customer
- staff dropdown
- row click auto-selects work order
- status update via dropdown (no free typing)
- labor cost update
- part add form
- uses Work Order ID terminology throughout
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from config.constants import WORK_ORDER_STATUS_LIST


logger = logging.getLogger(__name__)


class WorkOrdersPage(ttk.Frame):
    """
    Work Orders management page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.work_order_controller = app.get_controller("work_order")
        self.customer_controller = app.get_controller("customer")
        self.vehicle_controller = app.get_controller("vehicle")
        self.user_controller = app.get_controller("user")

        self.customer_var = tk.StringVar()
        self.vehicle_var = tk.StringVar()
        self.staff_var = tk.StringVar()
        self.issue_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        self.selected_work_order_id_var = tk.StringVar()
        self.selected_work_order_code_var = tk.StringVar()
        self.status_var = tk.StringVar(value="NEW")
        self.status_note_var = tk.StringVar()

        self.labor_cost_var = tk.StringVar()

        self.part_name_var = tk.StringVar()
        self.part_quantity_var = tk.StringVar(value="1")
        self.part_unit_price_var = tk.StringVar(value="0")
        self.part_source_var = tk.StringVar(value="SHOP")
        self.part_billable_var = tk.BooleanVar(value=True)
        self.part_notes_var = tk.StringVar()

        self.customer_map: dict[str, int] = {}
        self.vehicle_map: dict[str, int] = {}
        self.staff_map: dict[str, int] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Work Orders",
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
            text="Create Work Order",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        row = 1
        self._add_label(panel, row, "Customer")
        row += 1
        self.customer_combo = ttk.Combobox(
            panel,
            textvariable=self.customer_var,
            state="readonly",
            width=34,
        )
        self.customer_combo.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self.customer_combo.bind("<<ComboboxSelected>>", self._on_customer_selected)

        row += 1
        self._add_label(panel, row, "Vehicle")
        row += 1
        self.vehicle_combo = ttk.Combobox(
            panel,
            textvariable=self.vehicle_var,
            state="readonly",
            width=34,
        )
        self.vehicle_combo.grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Assign Staff")
        row += 1
        self.staff_combo = ttk.Combobox(
            panel,
            textvariable=self.staff_var,
            state="readonly",
            width=34,
        )
        self.staff_combo.grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Issue Description")
        row += 1
        ttk.Entry(panel, textvariable=self.issue_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Notes")
        row += 1
        ttk.Entry(panel, textvariable=self.notes_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 10)
        )

        row += 1
        ttk.Button(
            panel,
            text="Create Work Order",
            style="Primary.TButton",
            command=self._create_work_order,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 14))

        row += 1
        ttk.Separator(panel).grid(row=row, column=0, sticky="ew", pady=8)

        row += 1
        ttk.Label(
            panel,
            text="Selected Work Order",
            style="PageTitle.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(4, 12))

        row += 1
        self._add_label(panel, row, "Selected Work Order ID")
        row += 1
        ttk.Entry(
            panel,
            textvariable=self.selected_work_order_code_var,
            state="readonly",
            width=36,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Update Status")
        row += 1
        self.status_combo = ttk.Combobox(
            panel,
            textvariable=self.status_var,
            values=WORK_ORDER_STATUS_LIST,
            state="readonly",
            width=34,
        )
        self.status_combo.grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Status Note")
        row += 1
        ttk.Entry(panel, textvariable=self.status_note_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        ttk.Button(
            panel,
            text="Update Status",
            command=self._update_status,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 12))

        row += 1
        self._add_label(panel, row, "Labor Cost")
        row += 1
        ttk.Entry(panel, textvariable=self.labor_cost_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        ttk.Button(
            panel,
            text="Update Labor Cost",
            command=self._update_labor_cost,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 14))

        row += 1
        ttk.Separator(panel).grid(row=row, column=0, sticky="ew", pady=8)

        row += 1
        ttk.Label(
            panel,
            text="Add Part",
            style="PageTitle.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(4, 12))

        row += 1
        self._add_label(panel, row, "Part Name")
        row += 1
        ttk.Entry(panel, textvariable=self.part_name_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Quantity")
        row += 1
        ttk.Entry(panel, textvariable=self.part_quantity_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Unit Price")
        row += 1
        ttk.Entry(panel, textvariable=self.part_unit_price_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Part Source")
        row += 1
        ttk.Combobox(
            panel,
            textvariable=self.part_source_var,
            values=["SHOP", "CUSTOMER"],
            state="readonly",
            width=34,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 8))

        row += 1
        ttk.Checkbutton(
            panel,
            text="Billable",
            variable=self.part_billable_var,
        ).grid(row=row, column=0, sticky="w", pady=(0, 8))

        row += 1
        self._add_label(panel, row, "Part Notes")
        row += 1
        ttk.Entry(panel, textvariable=self.part_notes_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        ttk.Button(
            panel,
            text="Add Part",
            command=self._add_part,
        ).grid(row=row, column=0, sticky="ew")

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent, style="Card.TFrame", padding=20)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Work Order Records",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        columns = (
            "id",
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
            container,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

        headings = {
            "id": "ID",
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
            "id": 70,
            "work_order_id": 130,
            "customer_name": 150,
            "plate_number": 120,
            "assigned_staff": 120,
            "current_status": 110,
            "labor_cost": 90,
            "parts_total": 90,
            "subtotal": 100,
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
            command=self._load_all_work_orders,
        ).grid(row=2, column=0, sticky="e", pady=(10, 0))

    def _add_label(self, parent: ttk.Frame, row: int, text: str) -> None:
        ttk.Label(parent, text=text, style="Body.TLabel").grid(
            row=row,
            column=0,
            sticky="w",
            pady=(0, 4),
        )

    def _load_customers(self) -> None:
        response = self.customer_controller.get_all_customers()
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.customer_map.clear()
        display_values = []

        for customer in response.data or []:
            display = f"{customer.get('full_name')} | {customer.get('phone')} | ID:{customer.get('id')}"
            self.customer_map[display] = customer["id"]
            display_values.append(display)

        self.customer_combo["values"] = display_values
        if display_values and not self.customer_var.get():
            self.customer_combo.current(0)
            self._on_customer_selected()

    def _load_staff(self) -> None:
        response = self.user_controller.get_active_users()
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self.staff_map.clear()
        display_values = []

        for user in response.data or []:
            display = f"{user.get('username')} | {user.get('role_code')} | ID:{user.get('id')}"
            self.staff_map[display] = user["id"]
            display_values.append(display)

        self.staff_combo["values"] = display_values

    def _on_customer_selected(self, event=None) -> None:
        selected_customer = self.customer_var.get()
        customer_id = self.customer_map.get(selected_customer)

        self.vehicle_var.set("")
        self.vehicle_combo["values"] = []
        self.vehicle_map.clear()

        if not customer_id:
            return

        response = self.vehicle_controller.get_by_customer_id(customer_id)
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        display_values = []
        for vehicle in response.data or []:
            display = (
                f"{vehicle.get('plate_number')} | "
                f"{vehicle.get('make')} {vehicle.get('model')} | "
                f"ID:{vehicle.get('id')}"
            )
            self.vehicle_map[display] = vehicle["id"]
            display_values.append(display)

        self.vehicle_combo["values"] = display_values
        if display_values:
            self.vehicle_combo.current(0)

    def _create_work_order(self) -> None:
        customer_display = self.customer_var.get()
        vehicle_display = self.vehicle_var.get()
        staff_display = self.staff_var.get()

        customer_id = self.customer_map.get(customer_display)
        vehicle_id = self.vehicle_map.get(vehicle_display)
        staff_id = self.staff_map.get(staff_display) if staff_display else None

        if not customer_id or not vehicle_id:
            messagebox.showwarning(
                "Input Required",
                "Please select a customer and vehicle.",
            )
            return

        response = self.work_order_controller.create_work_order(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            issue_description=self.issue_var.get(),
            assigned_staff_id=staff_id,
            notes=self.notes_var.get() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self.issue_var.set("")
        self.notes_var.set("")
        self._load_all_work_orders()

    def _load_all_work_orders(self) -> None:
        response = self.work_order_controller.get_all_work_orders()

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

        self.selected_work_order_id_var.set(str(values[0]))
        self.selected_work_order_code_var.set(str(values[1]))
        self.status_var.set(str(values[5]))
        self.labor_cost_var.set(str(values[6]))

    def _update_status(self) -> None:
        internal_id = self.selected_work_order_id_var.get().strip()
        if not internal_id:
            messagebox.showwarning(
                "Selection Required",
                "Select a work order row first.",
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
                "Select a work order row first.",
            )
            return

        response = self.work_order_controller.set_labor_cost(
            work_order_id=int(internal_id),
            labor_cost=float(self.labor_cost_var.get() or 0),
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
                "Select a work order row first.",
            )
            return

        response = self.work_order_controller.add_part(
            work_order_id=int(internal_id),
            part_name=self.part_name_var.get(),
            quantity=int(self.part_quantity_var.get() or 1),
            unit_price=float(self.part_unit_price_var.get() or 0),
            part_source=self.part_source_var.get(),
            is_billable=self.part_billable_var.get(),
            notes=self.part_notes_var.get() or None,
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
        self._load_customers()
        self._load_staff()
        self._load_all_work_orders()