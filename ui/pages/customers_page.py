"""
ui/pages/customers_page.py

Customer Management page for GaragePulse using shared AppShell.

Features:
- cleaner balanced layout
- mandatory markers on key fields
- create + update support
- search and selection support
- hidden internal customer ID for update logic
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class CustomersPage(AppShell):
    """
    Customers management page with shared app shell.
    """

    LEFT_PANEL_WIDTH = 300

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="customers",
            page_title="Customer Management",
        )

        self.customer_controller = app.get_controller("customer")

        self.search_var = tk.StringVar()
        self.selected_customer_id_var = tk.StringVar()  # hidden, used for update logic

        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_line_1_var = tk.StringVar()
        self.address_line_2_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.postal_code_var = tk.StringVar()
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
        left_outer.grid(row=0, column=0, sticky="ns", padx=(0, 16))
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

    def _build_form_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            parent,
            text="Add / Edit Customer",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self.loaded_customer_label = tk.Label(
            parent,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.CARD_BG,
            fg="#2563eb",
        )
        self.loaded_customer_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 2))

        row = 2

        form_fields = [
            ("First Name *", self.first_name_var, "first_name"),
            ("Last Name *", self.last_name_var, "last_name"),
            ("Phone *", self.phone_var, "phone"),
            ("Email", self.email_var, "email"),
            ("Address Line 1", self.address_line_1_var, "address_line_1"),
            ("Address Line 2", self.address_line_2_var, "address_line_2"),
            ("City", self.city_var, "city"),
            ("State", self.state_var, "state"),
            ("Postal Code", self.postal_code_var, "postal_code"),
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

            entry = tk.Entry(
                parent,
                textvariable=variable,
                font=("Segoe UI", 10),
                relief="solid",
                bd=1,
            )
            entry.grid(row=row, column=0, sticky="ew", padx=20, pady=(0, 12), ipady=4)

            if field_key == "first_name":
                self.first_name_entry = entry
                entry.bind("<Return>", self._handle_type_and_load)
            elif field_key == "last_name":
                self.last_name_entry = entry
                entry.bind("<Return>", self._handle_type_and_load)
            elif field_key == "phone":
                self.phone_entry = entry
                entry.bind("<Return>", self._handle_type_and_load)

            row += 1

        button_bar = tk.Frame(parent, bg=self.CARD_BG)
        button_bar.grid(row=row, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_bar.grid_columnconfigure(0, weight=1)
        button_bar.grid_columnconfigure(1, weight=1)

        tk.Button(
            button_bar,
            text="Save Customer",
            command=self._handle_create_or_update_customer,
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
            text="Customer Records",
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
            "first_name",
            "last_name",
            "phone",
            "email",
            "city",
            "state",
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
            "first_name": "First Name",
            "last_name": "Last Name",
            "phone": "Phone",
            "email": "Email",
            "city": "City",
            "state": "State",
        }

        widths = {
            "first_name": 150,
            "last_name": 150,
            "phone": 140,
            "email": 260,
            "city": 140,
            "state": 100,
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

    def _build_full_name(self) -> str:
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        return f"{first_name} {last_name}".strip()

    def _split_full_name(self, full_name: str) -> tuple[str, str]:
        parts = (full_name or "").strip().split()
        if not parts:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])

    def _load_customer_into_form(self, customer: dict) -> None:
        first_name, last_name = self._split_full_name(customer.get("full_name", ""))

        self.selected_customer_id_var.set(str(customer.get("id", "")))
        self.loaded_customer_label.config(
            text=f"Editing customer: {customer.get('full_name', '')}"
        )
        self.first_name_var.set(first_name)
        self.last_name_var.set(last_name)
        self.phone_var.set("" if customer.get("phone") is None else str(customer.get("phone")))
        self.email_var.set("" if customer.get("email") is None else str(customer.get("email")))
        self.address_line_1_var.set("" if customer.get("address_line_1") is None else str(customer.get("address_line_1")))
        self.address_line_2_var.set("" if customer.get("address_line_2") is None else str(customer.get("address_line_2")))
        self.city_var.set("" if customer.get("city") is None else str(customer.get("city")))
        self.state_var.set("" if customer.get("state") is None else str(customer.get("state")))
        self.postal_code_var.set("" if customer.get("postal_code") is None else str(customer.get("postal_code")))
        self.notes_var.set("" if customer.get("notes") is None else str(customer.get("notes")))

    def _handle_type_and_load(self, event=None) -> None:
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        phone = self.phone_var.get().strip()

        search_candidates = []
        if phone:
            search_candidates.append(phone)

        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            search_candidates.append(full_name)
        if first_name:
            search_candidates.append(first_name)
        if last_name:
            search_candidates.append(last_name)

        if not search_candidates:
            messagebox.showwarning(
                "Search Required",
                "Type first name, last name, or phone and press Enter.",
            )
            return

        for term in search_candidates:
            response = self.customer_controller.search_customers(term)
            if not response.success:
                continue

            matches = response.data or []
            if len(matches) == 1:
                self._load_customer_into_form(matches[0])
                return

            if len(matches) > 1:
                self._populate_tree(matches)
                messagebox.showinfo(
                    "Multiple Matches",
                    "Multiple customers found. Please select the correct customer from the records table on the right.",
                )
                return

        messagebox.showinfo(
            "No Match Found",
            "No matching customer was found. You can continue entering details to create a new customer.",
        )

    def _handle_create_or_update_customer(self) -> None:
        customer_id = self.selected_customer_id_var.get().strip()
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        phone = self.phone_var.get().strip()
        full_name = self._build_full_name()

        if not first_name:
            messagebox.showwarning("Input Required", "First name is required.")
            self.first_name_entry.focus_set()
            return

        if not last_name:
            messagebox.showwarning("Input Required", "Last name is required.")
            self.last_name_entry.focus_set()
            return

        if not phone:
            messagebox.showwarning("Input Required", "Phone is required.")
            self.phone_entry.focus_set()
            return

        if customer_id:
            response = self.customer_controller.update_customer(
                customer_id=int(customer_id),
                full_name=full_name,
                phone=phone,
                email=self.email_var.get().strip() or None,
                address_line_1=self.address_line_1_var.get().strip() or None,
                address_line_2=self.address_line_2_var.get().strip() or None,
                city=self.city_var.get().strip() or None,
                state=self.state_var.get().strip() or None,
                postal_code=self.postal_code_var.get().strip() or None,
                notes=self.notes_var.get().strip() or None,
            )
        else:
            response = self.customer_controller.create_customer(
                full_name=full_name,
                phone=phone,
                email=self.email_var.get().strip() or None,
                address_line_1=self.address_line_1_var.get().strip() or None,
                address_line_2=self.address_line_2_var.get().strip() or None,
                city=self.city_var.get().strip() or None,
                state=self.state_var.get().strip() or None,
                postal_code=self.postal_code_var.get().strip() or None,
                notes=self.notes_var.get().strip() or None,
            )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._clear_form()
        self._load_all_customers()

    def _handle_search(self, event=None) -> None:
        search_text = self.search_var.get().strip()

        if not search_text:
            self._load_all_customers()
            return

        response = self.customer_controller.search_customers(search_text)

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate_tree(response.data or [])

    def _clear_search(self) -> None:
        self.search_var.set("")
        self._load_all_customers()

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
            customer_id = str(customer.get("id", ""))
            first_name, last_name = self._split_full_name(customer.get("full_name", ""))

            self.tree.insert(
                "",
                "end",
                iid=customer_id,
                values=(
                    first_name,
                    last_name,
                    customer.get("phone", ""),
                    customer.get("email", ""),
                    customer.get("city", ""),
                    customer.get("state", ""),
                ),
            )

    def _on_row_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        response = self.customer_controller.get_customer(int(selected))
        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        customer = response.data or {}
        self._load_customer_into_form(customer)

    def _clear_form(self) -> None:
        self.selected_customer_id_var.set("")
        self.loaded_customer_label.config(text="")
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.address_line_1_var.set("")
        self.address_line_2_var.set("")
        self.city_var.set("")
        self.state_var.set("")
        self.postal_code_var.set("")
        self.notes_var.set("")
        self.first_name_entry.focus_set()

    def on_show(self) -> None:
        self._build_sidebar()
        self._load_all_customers()