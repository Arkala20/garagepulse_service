"""
ui/pages/customers_page.py

Customers page for GaragePulse.

Professor alignment:
- Search customers by phone
- Add and view customers
- Simple production-style CRUD starter page
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class CustomersPage(ttk.Frame):
    """
    Customers management page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.customer_controller = app.get_controller("customer")

        self.search_var = tk.StringVar()

        self.full_name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_line_1_var = tk.StringVar()
        self.address_line_2_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.postal_code_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Customers",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            header,
            text="Back to Dashboard",
            command=lambda: self.app.show_page("dashboard"),
        ).grid(row=0, column=2, sticky="e")

        body = ttk.Frame(self, style="App.TFrame")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_form_panel(body)
        self._build_list_panel(body)

    def _build_form_panel(self, parent: ttk.Frame) -> None:
        form_card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        form_card.grid(row=0, column=0, sticky="nsw", padx=(0, 15))

        ttk.Label(
            form_card,
            text="Add Customer",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        fields = [
            ("Full Name", self.full_name_var),
            ("Phone", self.phone_var),
            ("Email", self.email_var),
            ("Address Line 1", self.address_line_1_var),
            ("Address Line 2", self.address_line_2_var),
            ("City", self.city_var),
            ("State", self.state_var),
            ("Postal Code", self.postal_code_var),
            ("Notes", self.notes_var),
        ]

        for index, (label_text, variable) in enumerate(fields, start=1):
            ttk.Label(form_card, text=label_text, style="Body.TLabel").grid(
                row=index * 2 - 1,
                column=0,
                sticky="w",
                pady=(0, 4),
            )

            ttk.Entry(
                form_card,
                textvariable=variable,
                width=30,
            ).grid(
                row=index * 2,
                column=0,
                sticky="ew",
                pady=(0, 10),
            )

        ttk.Button(
            form_card,
            text="Save Customer",
            style="Primary.TButton",
            command=self._handle_create_customer,
        ).grid(row=20, column=0, sticky="ew", pady=(10, 5))

        ttk.Button(
            form_card,
            text="Clear Form",
            command=self._clear_form,
        ).grid(row=21, column=0, sticky="ew")

    def _build_list_panel(self, parent: ttk.Frame) -> None:
        list_card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        list_card.grid(row=0, column=1, sticky="nsew")
        list_card.columnconfigure(0, weight=1)
        list_card.rowconfigure(2, weight=1)

        ttk.Label(
            list_card,
            text="Customer Records",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        search_frame = ttk.Frame(list_card)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(0, weight=1)

        ttk.Entry(
            search_frame,
            textvariable=self.search_var,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ttk.Button(
            search_frame,
            text="Search by Phone",
            command=self._handle_search,
        ).grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            search_frame,
            text="Load All",
            command=self._load_all_customers,
        ).grid(row=0, column=2)

        columns = (
            "id",
            "full_name",
            "phone",
            "email",
            "city",
            "state",
        )

        self.tree = ttk.Treeview(
            list_card,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=2, column=0, sticky="nsew")

        headings = {
            "id": "ID",
            "full_name": "Full Name",
            "phone": "Phone",
            "email": "Email",
            "city": "City",
            "state": "State",
        }

        widths = {
            "id": 70,
            "full_name": 180,
            "phone": 130,
            "email": 180,
            "city": 110,
            "state": 90,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(
            list_card,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _handle_create_customer(self) -> None:
        response = self.customer_controller.create_customer(
            full_name=self.full_name_var.get(),
            phone=self.phone_var.get(),
            email=self.email_var.get() or None,
            address_line_1=self.address_line_1_var.get() or None,
            address_line_2=self.address_line_2_var.get() or None,
            city=self.city_var.get() or None,
            state=self.state_var.get() or None,
            postal_code=self.postal_code_var.get() or None,
            notes=self.notes_var.get() or None,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        logger.info("Customer created successfully from UI.")
        self._clear_form()
        self._load_all_customers()

    def _handle_search(self) -> None:
        phone_fragment = self.search_var.get().strip()

        if not phone_fragment:
            messagebox.showwarning("Input Required", "Enter a phone number to search.")
            return

        response = self.customer_controller.search_by_phone(phone_fragment)

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate_tree(response.data or [])

    def _load_all_customers(self) -> None:
        response = self.customer_controller.get_all_customers()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate_tree(response.data or [])

    def _populate_tree(self, customers: list[dict]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for customer in customers:
            self.tree.insert(
                "",
                "end",
                values=(
                    customer.get("id", ""),
                    customer.get("full_name", ""),
                    customer.get("phone", ""),
                    customer.get("email", ""),
                    customer.get("city", ""),
                    customer.get("state", ""),
                ),
            )

    def _clear_form(self) -> None:
        self.full_name_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.address_line_1_var.set("")
        self.address_line_2_var.set("")
        self.city_var.set("")
        self.state_var.set("")
        self.postal_code_var.set("")
        self.notes_var.set("")

    def on_show(self) -> None:
        self._load_all_customers()