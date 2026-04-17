"""
ui/pages/vehicles_page.py

Vehicle Management page for GaragePulse using shared AppShell.

Features:
- search-based customer lookup
- customer search box with search icon style
- cleaner balanced layout
- add + update support
- hidden internal vehicle ID for update logic
- search by plate / customer / VIN
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class VehiclesPage(AppShell):
    """
    Vehicles management page with shared app shell.
    """

    LEFT_PANEL_WIDTH = 280

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="vehicles",
            page_title="Vehicle Management",
        )

        self.vehicle_controller = app.get_controller("vehicle")
        self.customer_controller = app.get_controller("customer")

        self.selected_vehicle_id_var = tk.StringVar()
        self.selected_customer_id_var = tk.StringVar()

        self.search_var = tk.StringVar()
        self.customer_search_var = tk.StringVar()

        self.customer_name_var = tk.StringVar()
        self.customer_phone_var = tk.StringVar()

        self.make_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.vin_var = tk.StringVar()
        self.plate_number_var = tk.StringVar()
        self.color_var = tk.StringVar()
        self.mileage_var = tk.StringVar()
        self.notes_var = tk.StringVar()

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

        self._build_scrollable_form_panel(left_outer)
        self._build_list_panel(right_card)

    def _build_scrollable_form_panel(self, parent: tk.Frame) -> None:
        container = tk.Frame(parent, bg=self.CARD_BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            bg=self.CARD_BG,
            highlightthickness=0,
            width=self.LEFT_PANEL_WIDTH - 20,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.CARD_BG)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._build_form_panel(scrollable)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _create_form_entry(
        self,
        parent: tk.Widget,
        textvariable: tk.StringVar | None = None,
        readonly: bool = False,
    ) -> tk.Entry:
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            width=28,
        )

        if readonly:
            entry.configure(
                state="readonly",
                readonlybackground="#f8fafc",
            )

        return entry

    def _build_form_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text="Add / Edit Vehicle",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self.loaded_vehicle_label = tk.Label(
            parent,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.CARD_BG,
            fg="#2563eb",
        )
        self.loaded_vehicle_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 0))
        self.loaded_vehicle_label.grid_remove()

        row = 2

        tk.Label(
            parent,
            text="Customer Search",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(0, 4))
        row += 1

        search_outer = tk.Frame(
            parent,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#6b7280",
            bd=0,
        )
        search_outer.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12))
        search_outer.grid_columnconfigure(0, weight=1)
        row += 1

        self.customer_search_entry = tk.Entry(
            search_outer,
            textvariable=self.customer_search_var,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            bg="#ffffff",
            fg="#0f172a",
            insertbackground="#0f172a",
        )
        self.customer_search_entry.grid(row=0, column=0, sticky="ew", padx=(10, 0), pady=6, ipady=4)
        self.customer_search_entry.bind("<Return>", self._handle_customer_search)

        icon_btn = tk.Label(
            search_outer,
            text="🔍",
            font=("Segoe UI Emoji", 11),
            bg="#ffffff",
            fg="#0ea5e9",
            cursor="hand2",
        )
        icon_btn.grid(row=0, column=1, padx=(6, 10), pady=6)
        icon_btn.bind("<Button-1>", lambda e: self._handle_customer_search())

        tk.Label(
            parent,
            text="Customer Name *",
            font=("Segoe UI", 10, "bold"),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(0, 4))
        row += 1

        self.customer_name_entry = self._create_form_entry(
            parent,
            textvariable=self.customer_name_var,
            readonly=True,
        )
        self.customer_name_entry.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12), ipady=4)
        row += 1

        tk.Label(
            parent,
            text="Customer Phone",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(0, 4))
        row += 1

        self.customer_phone_entry = self._create_form_entry(
            parent,
            textvariable=self.customer_phone_var,
            readonly=True,
        )
        self.customer_phone_entry.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12), ipady=4)
        row += 1

        form_fields = [
            ("Make *", self.make_var, "make"),
            ("Model *", self.model_var, "model"),
            ("Year *", self.year_var, "year"),
            ("VIN *", self.vin_var, "vin"),
            ("Plate Number *", self.plate_number_var, "plate_number"),
            ("Color", self.color_var, "color"),
            ("Mileage", self.mileage_var, "mileage"),
            ("Notes", self.notes_var, "notes"),
        ]

        for label_text, variable, field_key in form_fields:
            tk.Label(
                parent,
                text=label_text,
                font=("Segoe UI", 10, "bold" if "*" in label_text else "normal"),
                bg=self.CARD_BG,
                fg=self.BODY_COLOR,
            ).grid(row=row, column=0, sticky="w", padx=20, pady=(0, 4))
            row += 1

            entry = self._create_form_entry(parent, textvariable=variable)
            entry.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12), ipady=4)

            if field_key == "make":
                self.make_entry = entry
            elif field_key == "model":
                self.model_entry = entry
            elif field_key == "year":
                self.year_entry = entry
            elif field_key == "vin":
                self.vin_entry = entry
                entry.bind("<Return>", self._handle_type_and_load)
            elif field_key == "plate_number":
                self.plate_entry = entry
                entry.bind("<Return>", self._handle_type_and_load)

            row += 1

        button_bar = tk.Frame(parent, bg=self.CARD_BG)
        button_bar.grid(row=row, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_bar.grid_columnconfigure(0, weight=1)
        button_bar.grid_columnconfigure(1, weight=1)

        tk.Button(
            button_bar,
            text="Save Vehicle",
            command=self._handle_create_or_update_vehicle,
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
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        tk.Button(
            button_bar,
            text="Clear Form",
            command=self._clear_form,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            padx=12,
            pady=12,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_list_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        tk.Label(
            parent,
            text="Vehicle Records",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 14))

        search_frame = tk.Frame(parent, bg=self.CARD_BG)
        search_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        search_frame.grid_columnconfigure(0, weight=1)

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=4)
        search_entry.bind("<Return>", self._handle_search)

        tk.Button(
            search_frame,
            text="Search",
            command=self._handle_search,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
        ).grid(row=0, column=1, padx=(0, 8))

        tk.Button(
            search_frame,
            text="Clear Search",
            command=self._clear_search,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
        ).grid(row=0, column=2)

        table_frame = tk.Frame(parent, bg=self.CARD_BG)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = (
            "customer_name",
            "phone",
            "make",
            "model",
            "year",
            "plate_number",
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
            "customer_name": "Customer Name",
            "phone": "Phone",
            "make": "Make",
            "model": "Model",
            "year": "Year",
            "plate_number": "Plate Number",
        }

        widths = {
            "customer_name": 170,
            "phone": 130,
            "make": 110,
            "model": 130,
            "year": 80,
            "plate_number": 130,
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

    def _handle_customer_search(self, event=None) -> None:
        search_text = self.customer_search_var.get().strip()

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

        if len(matches) > 1:
            messagebox.showinfo(
                "Multiple Matches",
                "Multiple customers found. Please refine the customer search with full name or phone.",
            )
            return

        customer = matches[0]
        self.selected_customer_id_var.set(str(customer.get("id", "")))
        self.customer_name_var.set(str(customer.get("full_name", "") or ""))
        self.customer_phone_var.set(str(customer.get("phone", "") or ""))

    def _load_vehicle_into_form(self, vehicle: dict) -> None:
        self.selected_vehicle_id_var.set(str(vehicle.get("id", "")))
        self.loaded_vehicle_label.config(
            text=f"Editing vehicle: {vehicle.get('plate_number', '') or vehicle.get('make', '')}"
        )
        self.loaded_vehicle_label.grid()

        self.selected_customer_id_var.set(str(vehicle.get("customer_id", "") or ""))
        self.customer_name_var.set(str(vehicle.get("customer_name", "") or ""))
        self.customer_phone_var.set(str(vehicle.get("phone", "") or ""))
        self.make_var.set(str(vehicle.get("make", "") or ""))
        self.model_var.set(str(vehicle.get("model", "") or ""))
        self.year_var.set(str(vehicle.get("vehicle_year", "") or ""))
        self.vin_var.set(str(vehicle.get("vin", "") or ""))
        self.plate_number_var.set(str(vehicle.get("plate_number", "") or ""))
        self.color_var.set(str(vehicle.get("color", "") or ""))
        self.mileage_var.set(str(vehicle.get("mileage", "") or ""))
        self.notes_var.set(str(vehicle.get("notes", "") or ""))

    def _populate_tree(self, vehicles: list[dict]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for vehicle in vehicles:
            vehicle_id = str(vehicle.get("id", ""))

            self.tree.insert(
                "",
                "end",
                iid=vehicle_id,
                values=(
                    vehicle.get("customer_name", ""),
                    vehicle.get("phone", ""),
                    vehicle.get("make", ""),
                    vehicle.get("model", ""),
                    vehicle.get("vehicle_year", ""),
                    vehicle.get("plate_number", ""),
                ),
            )

    def _load_all_vehicles(self) -> None:
        response = self.vehicle_controller.get_prioritized_vehicle_list()
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate_tree(response.data or [])

    def _handle_type_and_load(self, event=None) -> None:
        candidates = []

        if self.plate_number_var.get().strip():
            candidates.append(("plate", self.plate_number_var.get().strip()))
        if self.vin_var.get().strip():
            candidates.append(("vin", self.vin_var.get().strip()))
        if self.customer_name_var.get().strip():
            candidates.append(("customer", self.customer_name_var.get().strip()))
        if self.customer_phone_var.get().strip():
            candidates.append(("customer", self.customer_phone_var.get().strip()))

        if not candidates:
            messagebox.showwarning(
                "Search Required",
                "Type plate number, VIN, customer name, or phone and press Enter.",
            )
            return

        for kind, term in candidates:
            matches = []

            if kind == "plate":
                response = self.vehicle_controller.search_by_plate(term)
                if response.success:
                    matches = response.data or []

            elif kind == "vin":
                response = self.vehicle_controller.get_prioritized_vehicle_list()
                if response.success:
                    matches = [
                        row for row in (response.data or [])
                        if str(row.get("vin", "")).strip().lower() == term.lower()
                    ]

            elif kind == "customer":
                response = self.vehicle_controller.get_prioritized_vehicle_list()
                if response.success:
                    lower_term = term.lower()
                    matches = [
                        row for row in (response.data or [])
                        if lower_term in str(row.get("customer_name", "")).lower()
                        or lower_term in str(row.get("phone", "")).lower()
                    ]

            if len(matches) == 1:
                self._load_vehicle_into_form(matches[0])
                return

            if len(matches) > 1:
                self._populate_tree(matches)
                messagebox.showinfo(
                    "Multiple Matches",
                    "Multiple vehicles found. Please select the correct vehicle from the records table on the right.",
                )
                return

        messagebox.showinfo(
            "No Match Found",
            "No matching vehicle was found. You can continue entering details to create a new vehicle.",
        )

    def _handle_create_or_update_vehicle(self) -> None:
        vehicle_id = self.selected_vehicle_id_var.get().strip()
        customer_id = self.selected_customer_id_var.get().strip()

        if not customer_id:
            messagebox.showwarning(
                "Input Required",
                "Please search and select a valid customer.",
            )
            self.customer_search_entry.focus_set()
            return

        if not self.make_var.get().strip():
            messagebox.showwarning("Input Required", "Make is required.")
            self.make_entry.focus_set()
            return

        if not self.model_var.get().strip():
            messagebox.showwarning("Input Required", "Model is required.")
            self.model_entry.focus_set()
            return

        year_text = self.year_var.get().strip()
        if not year_text:
            messagebox.showwarning("Input Required", "Year is required.")
            self.year_entry.focus_set()
            return

        try:
            vehicle_year = int(year_text)
        except ValueError:
            messagebox.showwarning("Invalid Input", "Year must be a number.")
            self.year_entry.focus_set()
            return

        vin = self.vin_var.get().strip()
        if not vin:
            messagebox.showwarning("Input Required", "VIN is required.")
            self.vin_entry.focus_set()
            return

        plate_number = self.plate_number_var.get().strip()
        if not plate_number:
            messagebox.showwarning("Input Required", "Plate Number is required.")
            self.plate_entry.focus_set()
            return

        mileage = None
        if self.mileage_var.get().strip():
            try:
                mileage = int(self.mileage_var.get().strip())
            except ValueError:
                messagebox.showwarning("Invalid Input", "Mileage must be a number.")
                return

        if vehicle_id:
            response = self.vehicle_controller.update_vehicle(
                vehicle_id=int(vehicle_id),
                make=self.make_var.get().strip(),
                model=self.model_var.get().strip(),
                vehicle_year=vehicle_year,
                vin=vin,
                plate_number=plate_number,
                color=self.color_var.get().strip() or None,
                mileage=mileage,
                notes=self.notes_var.get().strip() or None,
            )
        else:
            response = self.vehicle_controller.create_vehicle(
                customer_id=int(customer_id),
                make=self.make_var.get().strip(),
                model=self.model_var.get().strip(),
                vehicle_year=vehicle_year,
                vin=vin,
                plate_number=plate_number,
                color=self.color_var.get().strip() or None,
                mileage=mileage,
                notes=self.notes_var.get().strip() or None,
            )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._clear_form()
        self._load_all_vehicles()

    def _handle_search(self, event=None) -> None:
        search_text = self.search_var.get().strip()
        if not search_text:
            self._load_all_vehicles()
            return

        response = self.vehicle_controller.get_prioritized_vehicle_list()
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        lower_search = search_text.lower()
        filtered = [
            row
            for row in (response.data or [])
            if lower_search in str(row.get("plate_number", "")).lower()
            or lower_search in str(row.get("vin", "")).lower()
            or lower_search in str(row.get("customer_name", "")).lower()
            or lower_search in str(row.get("phone", "")).lower()
        ]

        self._populate_tree(filtered)

    def _clear_search(self) -> None:
        self.search_var.set("")
        self._load_all_vehicles()

    def _on_row_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        response = self.vehicle_controller.get_vehicle(int(selected))
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        vehicle = response.data or {}
        self._load_vehicle_into_form(vehicle)

    def _clear_form(self) -> None:
        self.selected_vehicle_id_var.set("")
        self.selected_customer_id_var.set("")
        self.loaded_vehicle_label.config(text="")
        self.loaded_vehicle_label.grid_remove()
        self.customer_search_var.set("")
        self.customer_name_var.set("")
        self.customer_phone_var.set("")
        self.make_var.set("")
        self.model_var.set("")
        self.year_var.set("")
        self.vin_var.set("")
        self.plate_number_var.set("")
        self.color_var.set("")
        self.mileage_var.set("")
        self.notes_var.set("")
        self.customer_search_entry.focus_set()

    def on_show(self) -> None:
        self._build_sidebar()
        self._load_all_vehicles()