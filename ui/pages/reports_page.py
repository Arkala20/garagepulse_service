"""
ui/pages/reports_page.py

Reports page for GaragePulse.

Professor alignment:
- Reports can be scaffold only for now
"""

from __future__ import annotations

import logging
from tkinter import ttk


logger = logging.getLogger(__name__)


class ReportsPage(ttk.Frame):
    """
    Reports scaffold page.
    """

    def __init__(self, parent: ttk.Frame, app) -> None:
        super().__init__(parent, style="App.TFrame")
        self.app = app
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.columnconfigure(1, weight=1)

        ttk.Label(
            header,
            text="Reports",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            header,
            text="Back to Dashboard",
            command=lambda: self.app.show_page("dashboard"),
        ).grid(row=0, column=2, sticky="e")

        content = ttk.Frame(self, style="Card.TFrame", padding=24)
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        content.columnconfigure(0, weight=1)

        ttk.Label(
            content,
            text="Reports Module",
            style="PageTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(
            content,
            text=(
                "This page is intentionally scaffolded for now.\n\n"
                "Future enhancements can include:\n"
                "- revenue trend charts\n"
                "- work order status distribution\n"
                "- top customers\n"
                "- CSV/Excel exports using pandas\n"
                "- printable summaries"
            ),
            style="Body.TLabel",
            justify="left",
        ).grid(row=1, column=0, sticky="w")

    def on_show(self) -> None:
        logger.info("Reports page opened.")