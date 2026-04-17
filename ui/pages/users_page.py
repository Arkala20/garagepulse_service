"""
ui/pages/users_page.py

Active Accounts + Staff Registration page for GaragePulse.

Updates:
- mandatory markers for required registration fields
- separate Activate User and Deactivate User buttons
- selected user info row separated from action buttons row
- cleaner production-style workflow
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from ui.shared.app_shell import AppShell


logger = logging.getLogger(__name__)


class UsersPage(AppShell):
    """
    Active Accounts and Staff Registration page.
    """

    LEFT_PANEL_WIDTH = 360

    def __init__(self, parent, app) -> None:
        super().__init__(
            parent=parent,
            app=app,
            active_page_name="users",
            page_title="Active Accounts",
        )

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
        self.selected_status_var = tk.StringVar()

        self.activate_button = None
        self.deactivate_button = None

        self._build_page_content()

    def _build_page_content(self) -> None:
        self.content.grid_columnconfigure(0, weight=0, minsize=self.LEFT_PANEL_WIDTH)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        left_card = tk.Frame(self.content, bg=self.CARD_BG, width=self.LEFT_PANEL_WIDTH)
        left_card.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        left_card.grid_propagate(False)

        right_card = tk.Frame(self.content, bg=self.CARD_BG)
        right_card.grid(row=0, column=1, sticky="nsew")

        self._build_left_panel(left_card)
        self._build_right_panel(right_card)

    def _build_left_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)

        row = 0

        tk.Label(
            parent,
            text="Staff Registration",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=18, pady=(18, 14))

        fields = [
            ("First Name", self.first_name_var, True),
            ("Last Name", self.last_name_var, True),
            ("Username", self.username_var, True),
            ("Email", self.email_var, True),
            ("Phone", self.phone_var, False),
            ("Password", self.password_var, True),
        ]

        for label_text, variable, required in fields:
            row += 1
            self._add_label(parent, row, label_text, required=required)
            row += 1

            entry_kwargs = {
                "textvariable": variable,
                "font": ("Segoe UI", 10),
                "relief": "solid",
                "bd": 1,
            }
            if label_text == "Password":
                entry_kwargs["show"] = "*"

            tk.Entry(parent, **entry_kwargs).grid(
                row=row, column=0, sticky="ew", padx=18, pady=(0, 10)
            )

        row += 1
        self._add_label(parent, row, "Role", required=True)
        row += 1
        ttk.Combobox(
            parent,
            textvariable=self.role_var,
            values=["STAFF", "ADMIN"],
            state="readonly",
        ).grid(row=row, column=0, sticky="ew", padx=18, pady=(0, 12))

        row += 1
        tk.Button(
            parent,
            text="Create Staff Account",
            command=self._register_staff,
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
        ).grid(row=row, column=0, sticky="ew", padx=18, pady=(4, 8))

        row += 1
        tk.Button(
            parent,
            text="Clear Form",
            command=self._clear_form,
            font=("Segoe UI", 10),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
        ).grid(row=row, column=0, sticky="ew", padx=18, pady=(0, 16))

    def _build_right_panel(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(4, weight=1)

        tk.Label(
            parent,
            text="User Accounts",
            font=("Segoe UI", 18, "bold"),
            bg=self.CARD_BG,
            fg=self.TITLE_COLOR,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 12))

        filter_row = tk.Frame(parent, bg=self.CARD_BG)
        filter_row.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        filter_row.grid_columnconfigure(10, weight=1)

        tk.Label(
            filter_row,
            text="Filter:",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=0, column=0, padx=(0, 6))

        ttk.Combobox(
            filter_row,
            textvariable=self.filter_var,
            values=["ALL", "ACTIVE", "INACTIVE"],
            state="readonly",
            width=12,
        ).grid(row=0, column=1, padx=(0, 8))

        tk.Button(
            filter_row,
            text="Apply",
            command=self._apply_filter,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
        ).grid(row=0, column=2, padx=(0, 8))

        tk.Button(
            filter_row,
            text="Refresh",
            command=self._load_all_users,
            font=("Segoe UI", 10, "bold"),
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
        ).grid(row=0, column=3, padx=(0, 8))

        selected_row = tk.Frame(parent, bg=self.CARD_BG)
        selected_row.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))

        tk.Label(
            selected_row,
            text="Selected User ID:",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=0, column=0, padx=(0, 6))

        tk.Entry(
            selected_row,
            textvariable=self.selected_user_id_var,
            state="readonly",
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            width=10,
        ).grid(row=0, column=1, padx=(0, 10))

        tk.Label(
            selected_row,
            text="Username:",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=0, column=2, padx=(0, 6))

        tk.Entry(
            selected_row,
            textvariable=self.selected_username_var,
            state="readonly",
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            width=18,
        ).grid(row=0, column=3, padx=(0, 10))

        tk.Label(
            selected_row,
            text="Status:",
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=0, column=4, padx=(0, 6))

        tk.Entry(
            selected_row,
            textvariable=self.selected_status_var,
            state="readonly",
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            width=10,
        ).grid(row=0, column=5, padx=(0, 10))

        action_row = tk.Frame(parent, bg=self.CARD_BG)
        action_row.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 12))

        self.activate_button = tk.Button(
            action_row,
            text="Activate User",
            command=self._activate_selected_user,
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.activate_button.grid(row=0, column=0, padx=(0, 10))

        self.deactivate_button = tk.Button(
            action_row,
            text="Deactivate User",
            command=self._deactivate_selected_user,
            font=("Segoe UI", 10, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )
        self.deactivate_button.grid(row=0, column=1)

        table_frame = tk.Frame(parent, bg=self.CARD_BG)
        table_frame.grid(row=4, column=0, sticky="nsew", padx=18, pady=(0, 18))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

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
            table_frame,
            columns=columns,
            show="headings",
            height=18,
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
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
            "username": 140,
            "email": 200,
            "role_code": 100,
            "is_active": 90,
            "first_name": 140,
            "last_name": 140,
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

    def _add_label(self, parent: tk.Frame, row: int, text: str, required: bool = False) -> None:
        label_text = f"{text} *" if required else text
        tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10),
            bg=self.CARD_BG,
            fg=self.BODY_COLOR,
        ).grid(row=row, column=0, sticky="w", padx=18, pady=(0, 4))

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
            response.message + "\n\nUse Activate User to enable the account when ready.",
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

        self.selected_user_id_var.set("")
        self.selected_username_var.set("")
        self.selected_status_var.set("")
        self._refresh_action_buttons()

    def _on_row_selected(self, event=None) -> None:
        selected = self.tree.focus()
        if not selected:
            selection = self.tree.selection()
            if not selection:
                return
            selected = selection[0]

        values = self.tree.item(selected, "values")
        if not values:
            return

        self.selected_user_id_var.set(str(values[0]))
        self.selected_username_var.set(str(values[1]))
        self.selected_status_var.set(str(values[4]))
        self._refresh_action_buttons()

    def _refresh_action_buttons(self) -> None:
        status = self.selected_status_var.get().strip().lower()
        has_user = bool(self.selected_user_id_var.get().strip())

        if not has_user:
            self.activate_button.configure(state="disabled")
            self.deactivate_button.configure(state="disabled")
            return

        if status == "yes":
            self.activate_button.configure(state="disabled")
            self.deactivate_button.configure(state="normal")
        else:
            self.activate_button.configure(state="normal")
            self.deactivate_button.configure(state="disabled")

    def _activate_selected_user(self) -> None:
        user_id = self.selected_user_id_var.get().strip()

        if not user_id:
            messagebox.showwarning("Selection Required", "Select a user row first.")
            return

        response = self.user_controller.activate_user(int(user_id))

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._apply_filter()

    def _deactivate_selected_user(self) -> None:
        user_id = self.selected_user_id_var.get().strip()

        if not user_id:
            messagebox.showwarning("Selection Required", "Select a user row first.")
            return

        response = self.user_controller.deactivate_user(int(user_id))

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", response.message)
        self._apply_filter()

    def on_show(self) -> None:
        self._build_sidebar()
        self.filter_var.set("ALL")
        self.selected_user_id_var.set("")
        self.selected_username_var.set("")
        self.selected_status_var.set("")
        self._load_all_users()
        self._refresh_action_buttons()