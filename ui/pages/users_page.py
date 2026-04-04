"""
ui/pages/users_page.py

Production-style Active Accounts + Staff Registration page for GaragePulse.

Fixes:
- activation controls always visible
- selected user ID shown above table
- better owner/admin workflow
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class UsersPage(ttk.Frame):
    """
    Active Accounts and Staff Registration page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")

        self.app = app
        self.user_controller = app.get_controller("user")

        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.role_var = tk.StringVar(value="STAFF")

        self.filter_var = tk.StringVar(value="ALL")
        self.selected_user_id_var = tk.StringVar()
        self.selected_username_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Active Accounts",
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
            text="Staff Registration",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        row = 1
        self._add_label(panel, row, "First Name")
        row += 1
        ttk.Entry(panel, textvariable=self.first_name_var, width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Last Name")
        row += 1
        ttk.Entry(panel, textvariable=self.last_name_var, width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Username")
        row += 1
        ttk.Entry(panel, textvariable=self.username_var, width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Email")
        row += 1
        ttk.Entry(panel, textvariable=self.email_var, width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Phone")
        row += 1
        ttk.Entry(panel, textvariable=self.phone_var, width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Password")
        row += 1
        ttk.Entry(panel, textvariable=self.password_var, show="*", width=34).grid(
            row=row, column=0, sticky="ew", pady=(0, 8)
        )

        row += 1
        self._add_label(panel, row, "Role")
        row += 1
        ttk.Combobox(
            panel,
            textvariable=self.role_var,
            values=["STAFF", "ADMIN"],
            state="readonly",
            width=32,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 10))

        row += 1
        ttk.Button(
            panel,
            text="Create Staff Account",
            style="Primary.TButton",
            command=self._register_staff,
        ).grid(row=row, column=0, sticky="ew", pady=(4, 8))

        row += 1
        ttk.Button(
            panel,
            text="Clear Form",
            command=self._clear_form,
        ).grid(row=row, column=0, sticky="ew")

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent, style="Card.TFrame", padding=20)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        ttk.Label(
            container,
            text="User Accounts",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        controls = ttk.Frame(container)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure(8, weight=1)

        ttk.Label(controls, text="Filter:", style="Body.TLabel").grid(row=0, column=0, padx=(0, 6))
        ttk.Combobox(
            controls,
            textvariable=self.filter_var,
            values=["ALL", "ACTIVE", "INACTIVE"],
            state="readonly",
            width=12,
        ).grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            controls,
            text="Apply",
            command=self._apply_filter,
        ).grid(row=0, column=2, padx=(0, 12))

        ttk.Label(controls, text="Selected User ID:", style="Body.TLabel").grid(row=0, column=3, padx=(0, 6))
        ttk.Entry(
            controls,
            textvariable=self.selected_user_id_var,
            state="readonly",
            width=10,
        ).grid(row=0, column=4, padx=(0, 8))

        ttk.Label(controls, text="Username:", style="Body.TLabel").grid(row=0, column=5, padx=(0, 6))
        ttk.Entry(
            controls,
            textvariable=self.selected_username_var,
            state="readonly",
            width=18,
        ).grid(row=0, column=6, padx=(0, 12))

        ttk.Button(
            controls,
            text="Activate Selected",
            command=self._activate_selected,
        ).grid(row=0, column=7, padx=(0, 8))

        ttk.Button(
            controls,
            text="Deactivate Selected",
            command=self._deactivate_selected,
        ).grid(row=0, column=8, sticky="w", padx=(0, 8))

        ttk.Button(
            controls,
            text="Refresh",
            command=self._load_all_users,
        ).grid(row=0, column=9, sticky="e")

        columns = (
            "id",
            "username",
            "email",
            "role_code",
            "is_active",
            "first_name",
            "last_name",
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
            "username": "Username",
            "email": "Email",
            "role_code": "Role",
            "is_active": "Active",
            "first_name": "First Name",
            "last_name": "Last Name",
        }

        widths = {
            "id": 70,
            "username": 120,
            "email": 180,
            "role_code": 90,
            "is_active": 80,
            "first_name": 120,
            "last_name": 120,
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

    def _register_staff(self) -> None:
        response = self.user_controller.register_staff(
            first_name=self.first_name_var.get(),
            last_name=self.last_name_var.get(),
            username=self.username_var.get(),
            email=self.email_var.get(),
            phone=self.phone_var.get() or None,
            password=self.password_var.get(),
            role_code=self.role_var.get(),
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo(
            "Success",
            response.message + "\n\nActivate the account from this page when ready.",
        )
        self._clear_form()
        self._load_all_users()

    def _clear_form(self) -> None:
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.username_var.set("")
        self.email_var.set("")
        self.phone_var.set("")
        self.password_var.set("")
        self.role_var.set("STAFF")

    def _load_all_users(self) -> None:
        response = self.user_controller.get_all_staff()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate(response.data or [])

    def _load_active_users(self) -> None:
        response = self.user_controller.get_active_users()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate(response.data or [])

    def _load_inactive_users(self) -> None:
        response = self.user_controller.get_inactive_users()

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        self._populate(response.data or [])

    def _apply_filter(self) -> None:
        filter_value = self.filter_var.get()

        if filter_value == "ACTIVE":
            self._load_active_users()
        elif filter_value == "INACTIVE":
            self._load_inactive_users()
        else:
            self._load_all_users()

    def _populate(self, users: list[dict]) -> None:
        self.tree.delete(*self.tree.get_children())

        for user in users:
            self.tree.insert(
                "",
                "end",
                values=(
                    user.get("id", ""),
                    user.get("username", ""),
                    user.get("email", ""),
                    user.get("role_code", ""),
                    "Yes" if user.get("is_active") else "No",
                    user.get("first_name", ""),
                    user.get("last_name", ""),
                ),
            )

    def _on_row_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            return

        values = self.tree.item(selected, "values")
        if not values:
            return

        self.selected_user_id_var.set(str(values[0]))
        self.selected_username_var.set(str(values[1]))

    def _activate_selected(self) -> None:
        user_id = self.selected_user_id_var.get().strip()
        if not user_id:
            messagebox.showwarning(
                "Selection Required",
                "Select a user row first.",
            )
            return

        response = self.user_controller.activate_user(int(user_id))

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._apply_filter()

    def _deactivate_selected(self) -> None:
        user_id = self.selected_user_id_var.get().strip()
        if not user_id:
            messagebox.showwarning(
                "Selection Required",
                "Select a user row first.",
            )
            return

        response = self.user_controller.deactivate_user(int(user_id))

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._apply_filter()

    def on_show(self) -> None:
        self.filter_var.set("ALL")
        self.selected_user_id_var.set("")
        self.selected_username_var.set("")
        self._load_all_users()