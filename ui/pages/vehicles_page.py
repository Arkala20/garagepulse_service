"""
ui/pages/vehicles_page.py

Production-style Vehicles page for GaragePulse.

Upgrades from prototype:
- customer selection via dropdown instead of manual customer ID entry
- search by plate / vehicle number
- prioritized vehicle loading
- row selection support
- cleaner displayed columns
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class VehiclesPage(ttk.Frame):
    """
    Vehicles management page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.vehicle_controller = app.get_controller("vehicle")
        self.customer_controller = app.get_controller("customer")

        self.search_var = tk.StringVar()

        self.customer_var = tk.StringVar()
        self.make_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.vin_var = tk.StringVar()
        self.plate_var = tk.StringVar()
        self.color_var = tk.StringVar()
        self.mileage_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        self.customer_map: dict[str, int] = {}
        self.selected_vehicle_id_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Vehicles",
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

        self._build_form_panel(body)
        self._build_table_panel(body)

    def _build_form_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=18)
        panel.grid(row=0, column=0, sticky="nsw", padx=(0, 15))

        ttk.Label(
            panel,
            text="Add Vehicle",
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

        row += 1
        self._add_label(panel, row, "Make")
        row += 1
        ttk.Entry(panel, textvariable=self.make_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Model")
        row += 1
        ttk.Entry(panel, textvariable=self.model_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Year")
        row += 1
        ttk.Entry(panel, textvariable=self.year_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "VIN")
        row += 1
        ttk.Entry(panel, textvariable=self.vin_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Plate Number")
        row += 1
        ttk.Entry(panel, textvariable=self.plate_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Color")
        row += 1
        ttk.Entry(panel, textvariable=self.color_var, width=36).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Mileage")
        row += 1
        ttk.Entry(panel, textvariable=self.mileage_var, width=36).grid(
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
            text="Save Vehicle",
            style="Primary.TButton",
            command=self._create_vehicle,
        ).grid(row=row, column=0, sticky="ew", pady=(4, 6))

        row += 1
        ttk.Button(
            panel,
            text="Clear",
            command=self._clear_form,
        ).grid(row=row, column=0, sticky="ew")

    def _build_table_panel(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent, style="Card.TFrame", padding=20)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Vehicle Records",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        search_frame = ttk.Frame(container)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(0, weight=1)

        ttk.Entry(
            search_frame,
            textvariable=self.search_var,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Button(
            search_frame,
            text="Search Plate",
            command=self._search,
        ).grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            search_frame,
            text="Load Prioritized",
            command=self._load_prioritized,
        ).grid(row=0, column=2)

        columns = (
            "id",
            "customer_name",
            "make",
            "model",
            "vehicle_year",
            "plate_number",
            "vin",
            "current_status",
        )

        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=2, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

        headings = {
            "id": "ID",
            "customer_name": "Customer",
            "make": "Make",
            "model": "Model",
            "vehicle_year": "Year",
            "plate_number": "Plate Number",
            "vin": "VIN",
            "current_status": "Status",
        }

        widths = {
            "id": 70,
            "customer_name": 150,
            "make": 120,
            "model": 120,
            "vehicle_year": 80,
            "plate_number": 120,
            "vin": 150,
            "current_status": 110,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

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

    def _create_vehicle(self) -> None:
        customer_display = self.customer_var.get()
        customer_id = self.customer_map.get(customer_display)

        if not customer_id:
            messagebox.showwarning(
                "Input Required",
                "Please select a customer.",
            )
            return

        try:
            response = self.vehicle_controller.create_vehicle(
                customer_id=customer_id,
                make=self.make_var.get(),
                model=self.model_var.get(),
                vehicle_year=int(self.year_var.get()) if self.year_var.get() else None,
                vin=self.vin_var.get() or None,
                plate_number=self.plate_var.get(),
                color=self.color_var.get() or None,
                mileage=int(self.mileage_var.get()) if self.mileage_var.get() else None,
                notes=self.notes_var.get() or None,
            )

            if not response.success:
                messagebox.showerror("Error", response.message)
                return

            messagebox.showinfo("Success", response.message)
            self._clear_form()
            self._load_prioritized()

        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _search(self) -> None:
        plate_fragment = self.search_var.get().strip()

        if not plate_fragment:
            messagebox.showwarning(
                "Input Required",
                "Enter a plate number to search.",
            )
            return

        response = self.vehicle_controller.search_by_plate(plate_fragment)

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate(response.data or [])

    def _load_prioritized(self) -> None:
        response = self.vehicle_controller.get_prioritized_vehicle_list()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate(response.data or [])

    def _populate(self, data: list[dict]) -> None:
        self.tree.delete(*self.tree.get_children())

        for row in data:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get("id", ""),
                    row.get("customer_name", ""),
                    row.get("make", ""),
                    row.get("model", ""),
                    row.get("vehicle_year", ""),
                    row.get("plate_number", ""),
                    row.get("vin", ""),
                    row.get("current_status", ""),
                ),
            )

    def _on_row_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        if not values:
            return

        self.selected_vehicle_id_var.set(str(values[0]))

    def _clear_form(self) -> None:
        self.customer_var.set("")
        self.make_var.set("")
        self.model_var.set("")
        self.year_var.set("")
        self.vin_var.set("")
        self.plate_var.set("")
        self.color_var.set("")
        self.mileage_var.set("")
        self.notes_var.set("")

        if self.customer_combo["values"]:
            self.customer_combo.current(0)

    def on_show(self) -> None:
        self._load_customers()
        self._load_prioritized()