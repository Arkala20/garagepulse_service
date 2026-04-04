"""
ui/pages/reset_password_page.py

Reset Password page for GaragePulse.

Professor alignment:
- User enters reset token
- New password + confirm password
- Proper reset flow
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class ResetPasswordPage(ttk.Frame):
    """
    Reset password page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")
        self.app = app
        self.auth_controller = app.get_controller("auth")

        self.token_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

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

        title = ttk.Label(card, text="Reset Password", style="PageTitle.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        subtitle = ttk.Label(
            card,
            text="Enter your reset token and new password.",
            style="Body.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 20))

        token_label = ttk.Label(card, text="Reset Token", style="Body.TLabel")
        token_label.grid(row=2, column=0, sticky="w", pady=(0, 6))

        token_entry = ttk.Entry(card, textvariable=self.token_var, width=40)
        token_entry.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        password_label = ttk.Label(card, text="New Password", style="Body.TLabel")
        password_label.grid(row=4, column=0, sticky="w", pady=(0, 6))

        password_entry = ttk.Entry(
            card,
            textvariable=self.password_var,
            show="*",
            width=40,
        )
        password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 14))

        confirm_label = ttk.Label(card, text="Confirm Password", style="Body.TLabel")
        confirm_label.grid(row=6, column=0, sticky="w", pady=(0, 6))

        confirm_entry = ttk.Entry(
            card,
            textvariable=self.confirm_password_var,
            show="*",
            width=40,
        )
        confirm_entry.grid(row=7, column=0, sticky="ew", pady=(0, 18))

        reset_button = ttk.Button(
            card,
            text="Reset Password",
            style="Primary.TButton",
            command=self._handle_reset_password,
        )
        reset_button.grid(row=8, column=0, sticky="ew", pady=(0, 10))

        back_button = ttk.Button(
            card,
            text="Back to Login",
            command=self._go_to_login,
        )
        back_button.grid(row=9, column=0, sticky="ew")

    def set_token(self, token: str) -> None:
        """
        Called from Forgot Password page to prefill token.
        """
        self.token_var.set(token)

    def _handle_reset_password(self) -> None:
        token = self.token_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()

        response = self.auth_controller.reset_password(
            reset_token=token,
            new_password=password,
            confirm_password=confirm_password,
        )

        if not response.success:
            messagebox.showerror("Error", response.message)
            return

        messagebox.showinfo("Success", "Password reset successful. Please login.")
        logger.info("Password reset successful")

        self._go_to_login()

    def _go_to_login(self) -> None:
        self.app.show_page("login")

    def on_show(self) -> None:
        """
        Clear sensitive fields when page is shown.
        """
        self.password_var.set("")
        self.confirm_password_var.set("")