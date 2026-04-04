"""
ui/pages/forgot_password_page.py

Forgot Password page for GaragePulse.

Professor alignment:
- User can request reset using email or username
- Leads to reset password page with token
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class ForgotPasswordPage(ttk.Frame):
    """
    Forgot password page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")
        self.app = app
        self.auth_controller = app.get_controller("auth")

        self.identifier_var = tk.StringVar()
        self.token_var = tk.StringVar()

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

        title = ttk.Label(card, text="Forgot Password", style="PageTitle.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        subtitle = ttk.Label(
            card,
            text="Enter your email or username to receive a reset token.",
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 20))

        identifier_label = ttk.Label(card, text="Email or Username", style="Body.TLabel")
        identifier_label.grid(row=2, column=0, sticky="w", pady=(0, 6))

        identifier_entry = ttk.Entry(card, textvariable=self.identifier_var, width=40)
        identifier_entry.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        identifier_entry.focus()

        request_button = ttk.Button(
            card,
            text="Request Reset",
            style="Primary.TButton",
            command=self._handle_request_reset,
        )
        request_button.grid(row=4, column=0, sticky="ew", pady=(0, 16))

        token_label = ttk.Label(card, text="Reset Token", style="Body.TLabel")
        token_label.grid(row=5, column=0, sticky="w", pady=(0, 6))

        token_entry = ttk.Entry(card, textvariable=self.token_var, width=40)
        token_entry.grid(row=6, column=0, sticky="ew", pady=(0, 14))

        proceed_button = ttk.Button(
            card,
            text="Proceed to Reset Password",
            command=self._go_to_reset_password,
        )
        proceed_button.grid(row=7, column=0, sticky="ew", pady=(0, 10))

        back_button = ttk.Button(
            card,
            text="Back to Login",
            command=self._go_to_login,
        )
        back_button.grid(row=8, column=0, sticky="ew")

    def _handle_request_reset(self) -> None:
        identifier = self.identifier_var.get().strip()

        response = self.auth_controller.request_password_reset(identifier)

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        token = response.data.get("reset_token")

        # DEV MODE: show token (since no email integration)
        self.token_var.set(token)

        messagebox.showinfo(
            "Success",
            "Reset token generated.\n(Shown here for development purposes.)",
        )

        logger.info("Password reset token generated for %s", identifier)

    def _go_to_reset_password(self) -> None:
        token = self.token_var.get().strip()

        if not token:
            messagebox.showwarning("Input Required", "Enter the reset token.")
            return

        if "reset_password" not in self.app.pages:
            from ui.pages.reset_password_page import ResetPasswordPage
            self.app.register_page("reset_password", ResetPasswordPage)

        page = self.app.pages["reset_password"]
        page.set_token(token)

        self.app.show_page("reset_password")

    def _go_to_login(self) -> None:
        self.app.show_page("login")

    def on_show(self) -> None:
        self.identifier_var.set("")
        self.token_var.set("")