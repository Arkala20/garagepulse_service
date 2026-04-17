"""
ui/pages/login_page.py

Production-style Login page for GaragePulse.
- accepts email or username
- background garage image
- softer realistic login card
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import messagebox, ttk


logger = logging.getLogger(__name__)


class LoginPage(ttk.Frame):
    ENTRY_WIDTH = 34
    BUTTON_WIDTH = 34

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.auth_controller = app.get_controller("auth")

        self.identifier_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.bg_image = None
        self.bg_label = None
        self.identifier_entry = None
        self.password_entry = None

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

        brand_label = tk.Label(
            card,
            text="GaragePulse",
            font=("Segoe UI", 22, "bold"),
            bg="#f2f4f7",
            fg="#102a43",
            anchor="w",
        )
        brand_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        subtitle = tk.Label(
            card,
            text="Sign in with your email address or username.",
            font=("Segoe UI", 11),
            bg="#f2f4f7",
            fg="#52606d",
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="ew", pady=(0, 24))

        identifier_label = tk.Label(
            card,
            text="Email or Username",
            font=("Segoe UI", 11),
            bg="#f2f4f7",
            fg="#334e68",
            anchor="w",
        )
        identifier_label.grid(row=2, column=0, sticky="ew", pady=(0, 6))

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

        password_label = tk.Label(
            card,
            text="Password",
            font=("Segoe UI", 11),
            bg="#f2f4f7",
            fg="#334e68",
            anchor="w",
        )
        password_label.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        self.password_entry = tk.Entry(
            card,
            textvariable=self.password_var,
            show="*",
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
        self.password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 22), ipady=8)

        sign_in_button = tk.Button(
            card,
            text="Sign In",
            command=self._handle_login,
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
        )
        sign_in_button.grid(row=6, column=0, sticky="ew", pady=(0, 12))

        forgot_button = tk.Button(
            card,
            text="Forgot Password?",
            command=self._go_to_forgot_password,
            font=("Segoe UI", 10, "bold"),
            bg="#f2f4f7",
            fg="#3e4c59",
            activebackground="#f2f4f7",
            activeforeground="#243b53",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        forgot_button.grid(row=7, column=0, pady=(0, 0))

        self.identifier_entry.bind("<Return>", self._handle_enter_key)
        self.password_entry.bind("<Return>", self._handle_enter_key)

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
                    logger.warning("Could not load login background image: %s", exc)

    def _handle_enter_key(self, event=None) -> None:
        self._handle_login()

    def _handle_login(self) -> None:
        identifier = self.identifier_var.get().strip()
        password = self.password_var.get()

        if not identifier:
            messagebox.showerror("Validation Error", "Please enter your email or username.")
            self.identifier_entry.focus_set()
            return

        if not password:
            messagebox.showerror("Validation Error", "Please enter your password.")
            self.password_entry.focus_set()
            return

        try:
            response = self.auth_controller.login(identifier, password)
        except Exception as exc:
            logger.exception("Login failed due to unexpected error: %s", exc)
            messagebox.showerror("Login Error", "An unexpected error occurred while trying to sign in.")
            return

        if not response.success:
            messagebox.showerror("Login Failed", response.message)
            return

        logger.info("Login successful for user: %s", identifier)
        messagebox.showinfo("Success", response.message)

        if "dashboard" not in self.app.pages:
            from ui.pages.dashboard_page import DashboardPage
            self.app.register_page("dashboard", DashboardPage)

        self.app.show_page("dashboard")

    def _go_to_forgot_password(self) -> None:
        if "forgot_password" not in self.app.pages:
            from ui.pages.forgot_password_page import ForgotPasswordPage
            self.app.register_page("forgot_password", ForgotPasswordPage)

        self.app.show_page("forgot_password")

    def on_show(self) -> None:
        self.identifier_var.set("")
        self.password_var.set("")
        self.after(100, self._focus_identifier)

    def _focus_identifier(self) -> None:
        if self.identifier_entry:
            self.identifier_entry.focus_set()