"""
ui/pages/reset_password_page.py

Reset Password page for GaragePulse.
- validates token before reset
- trims spaces safely
- shows clearer errors
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

        ttk.Label(card, text="Reset Token", style="Body.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )

        self.token_entry = ttk.Entry(card, textvariable=self.token_var, width=48)
        self.token_entry.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        ttk.Label(card, text="New Password", style="Body.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 6)
        )

        self.password_entry = ttk.Entry(
            card,
            textvariable=self.password_var,
            show="*",
            width=48,
        )
        self.password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 14))

        ttk.Label(card, text="Confirm Password", style="Body.TLabel").grid(
            row=6, column=0, sticky="w", pady=(0, 6)
        )

        self.confirm_entry = ttk.Entry(
            card,
            textvariable=self.confirm_password_var,
            show="*",
            width=48,
        )
        self.confirm_entry.grid(row=7, column=0, sticky="ew", pady=(0, 18))

        ttk.Button(
            card,
            text="Reset Password",
            style="Primary.TButton",
            command=self._handle_reset_password,
        ).grid(row=8, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(
            card,
            text="Back to Login",
            command=self._go_to_login,
        ).grid(row=9, column=0, sticky="ew")

    def _handle_reset_password(self) -> None:
        token = self.token_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()

        if not token:
            messagebox.showwarning("Input Required", "Please enter the reset token.")
            self.token_entry.focus_set()
            return

        # Step 1: validate token first for clearer debugging
        validation = self.auth_controller.validate_reset_token(token)
        if not validation.success:
            messagebox.showerror(
                "Error",
                f"{validation.message}\n\n"
                f"Token being checked:\n{repr(token)}"
            )
            return

        # Step 2: perform actual password reset
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
        self.token_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")