"""
ui/pages/forgot_password_page.py

Production-style Forgot Password page for GaragePulse.
Token is emailed to the user instead of being auto-passed into reset page.
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import messagebox, ttk

logger = logging.getLogger(__name__)


class ForgotPasswordPage(ttk.Frame):
    ENTRY_WIDTH = 34
    BUTTON_WIDTH = 34

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.auth_controller = app.get_controller("auth")

        self.identifier_var = tk.StringVar()

        self.bg_image = None
        self.bg_label = None
        self.identifier_entry = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.configure(style="App.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.background_frame = tk.Frame(self, bg="#dfe3e8")
        self.background_frame.grid(row=0, column=0, sticky="nsew")
        self.background_frame.grid_rowconfigure(0, weight=1)
        self.background_frame.grid_columnconfigure(0, weight=1)

        self._load_background_image()

        center_frame = tk.Frame(self.background_frame, bg="#dfe3e8")
        center_frame.grid(row=0, column=0)

        card = tk.Frame(
            center_frame,
            bg="#f2f4f7",
            padx=34,
            pady=30,
            highlightthickness=1,
            highlightbackground="#cbd2d9",
        )
        card.grid(row=0, column=0)
        card.grid_columnconfigure(0, weight=1)

        tk.Label(
            card,
            text="Forgot Password",
            font=("Segoe UI", 22, "bold"),
            bg="#f2f4f7",
            fg="#102a43",
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        tk.Label(
            card,
            text="Enter your email or username to receive a reset token by email.",
            font=("Segoe UI", 11),
            bg="#f2f4f7",
            fg="#52606d",
            anchor="w",
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 24))

        tk.Label(
            card,
            text="Email or Username",
            font=("Segoe UI", 11),
            bg="#f2f4f7",
            fg="#334e68",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 6))

        self.identifier_entry = tk.Entry(
            card,
            textvariable=self.identifier_var,
            font=("Segoe UI", 11),
            width=self.ENTRY_WIDTH,
            relief="solid",
            bd=1,
            bg="#ffffff",
            fg="#102a43",
            insertbackground="#102a43",
            highlightthickness=1,
            highlightbackground="#bcccdc",
            highlightcolor="#829ab1",
        )
        self.identifier_entry.grid(row=3, column=0, sticky="ew", pady=(0, 16), ipady=8)

        tk.Button(
            card,
            text="Request Reset",
            command=self._handle_request_reset,
            font=("Segoe UI", 11, "bold"),
            width=self.BUTTON_WIDTH,
            bg="#3e4c59",
            fg="white",
            activebackground="#52606d",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10,
        ).grid(row=4, column=0, sticky="ew", pady=(0, 16))

        tk.Button(
            card,
            text="Go to Reset Password",
            command=self._go_to_reset_password,
            font=("Segoe UI", 11, "bold"),
            width=self.BUTTON_WIDTH,
            bg="#3e4c59",
            fg="white",
            activebackground="#52606d",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10,
        ).grid(row=5, column=0, sticky="ew", pady=(0, 12))

        tk.Button(
            card,
            text="Back to Login",
            command=self._go_to_login,
            font=("Segoe UI", 10, "bold"),
            width=self.BUTTON_WIDTH,
            bg="#f2f4f7",
            fg="#3e4c59",
            activebackground="#f2f4f7",
            activeforeground="#243b53",
            relief="flat",
            bd=0,
            cursor="hand2",
        ).grid(row=6, column=0)

        self.identifier_entry.bind("<Return>", self._handle_enter_key)

    def _load_background_image(self) -> None:
        possible_paths = [
            os.path.join("assets", "images", "login_bg.png"),
            os.path.join("assets", "login_bg.png"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.bg_image = tk.PhotoImage(file=path)
                    self.bg_label = tk.Label(
                        self.background_frame,
                        image=self.bg_image,
                        bd=0,
                        highlightthickness=0,
                    )
                    self.bg_label.place(relx=0.5, rely=0.5, anchor="center")
                    return
                except Exception as exc:
                    logger.warning("Could not load forgot password background image: %s", exc)

    def _handle_enter_key(self, event=None) -> None:
        self._handle_request_reset()

    def _handle_request_reset(self) -> None:
        identifier = self.identifier_var.get().strip()

        if not identifier:
            messagebox.showwarning("Input Required", "Please enter your email or username.")
            if self.identifier_entry:
                self.identifier_entry.focus_set()
            return

        try:
            response = self.auth_controller.request_password_reset(identifier)
        except Exception as exc:
            logger.exception("Forgot password request failed: %s", exc)
            messagebox.showerror("Error", "An unexpected error occurred while requesting reset.")
            return

        if response.success:
            messagebox.showinfo("Success", response.message)
        else:
            messagebox.showerror("Error", response.message)

    def _go_to_reset_password(self) -> None:
        if "reset_password" not in self.app.pages:
            from ui.pages.reset_password_page import ResetPasswordPage
            self.app.register_page("reset_password", ResetPasswordPage)

        self.app.show_page("reset_password")

    def _go_to_login(self) -> None:
        self.app.show_page("login")

    def on_show(self) -> None:
        self.identifier_var.set("")
        self.after(100, self._focus_identifier)

    def _focus_identifier(self) -> None:
        if self.identifier_entry:
            self.identifier_entry.focus_set()