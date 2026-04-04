"""
ui/pages/login_page.py

Login page for GaragePulse.

Professor alignment:
- Login accepts email address or username
- Includes forgot password navigation
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class LoginPage(ttk.Frame):
    """
    Public login page for GaragePulse.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")
        self.app = app
        self.auth_controller = app.get_controller("auth")

        self.identifier_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        outer = ttk.Frame(self, style="App.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        card = ttk.Frame(outer, style="Card.TFrame", padding=32)
        card.grid(row=0, column=0)
        card.columnconfigure(0, weight=1)

        title = ttk.Label(card, text="GaragePulse", style="PageTitle.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        subtitle = ttk.Label(
            card,
            text="Sign in with your email address or username.",
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 20))

        identifier_label = ttk.Label(
            card,
            text="Email or Username",
            style="Body.TLabel",
        )
        identifier_label.grid(row=2, column=0, sticky="w", pady=(0, 6))

        identifier_entry = ttk.Entry(
            card,
            textvariable=self.identifier_var,
            width=40,
        )
        identifier_entry.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        identifier_entry.focus()

        password_label = ttk.Label(
            card,
            text="Password",
            style="Body.TLabel",
        )
        password_label.grid(row=4, column=0, sticky="w", pady=(0, 6))

        password_entry = ttk.Entry(
            card,
            textvariable=self.password_var,
            show="*",
            width=40,
        )
        password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 18))

        login_button = ttk.Button(
            card,
            text="Sign In",
            style="Primary.TButton",
            command=self._handle_login,
        )
        login_button.grid(row=6, column=0, sticky="ew", pady=(0, 12))

        forgot_button = ttk.Button(
            card,
            text="Forgot Password?",
            command=self._go_to_forgot_password,
        )
        forgot_button.grid(row=7, column=0, sticky="ew")

        self.bind_all("<Return>", self._handle_enter_key)

    def _handle_enter_key(self, event) -> None:
        self._handle_login()

    def _handle_login(self) -> None:
        identifier = self.identifier_var.get().strip()
        password = self.password_var.get()

        response = self.auth_controller.login(identifier, password)

        if not response.success:
            messagebox.showerror("Login Failed", response.message)
            return

        messagebox.showinfo("Success", response.message)
        logger.info("Login successful for user: %s", identifier)

        role_code = self.auth_controller.get_role_code()

        if "dashboard" not in self.app.pages:
            from ui.pages.dashboard_page import DashboardPage
            self.app.register_page("dashboard", DashboardPage)

        self.app.show_page("dashboard")

        logger.info("Redirected to dashboard for role=%s", role_code)

    def _go_to_forgot_password(self) -> None:
        if "forgot_password" not in self.app.pages:
            from ui.pages.forgot_password_page import ForgotPasswordPage
            self.app.register_page("forgot_password", ForgotPasswordPage)

        self.app.show_page("forgot_password")

    def on_show(self) -> None:
        """
        Reset sensitive fields whenever page is shown.
        """
        self.password_var.set("")