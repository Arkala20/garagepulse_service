"""
controllers/dashboard_controller.py

Dashboard controller for GaragePulse.
Bridges UI with DashboardService for summary cards,
recent activity, staff overview, and charts.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.dashboard_service import DashboardService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class DashboardController:
    """
    Controller for dashboard-related UI actions.
    """

    def __init__(self) -> None:
        self.dashboard_service = DashboardService()

    def get_dashboard_summary(self) -> ServiceResponse:
        """
        Fetch dashboard summary cards.

        Includes:
        - total revenue
        - active work orders
        - completed today
        - pending payments
        """
        logger.debug("Fetching dashboard summary")

        return self.dashboard_service.get_dashboard_summary()

    def get_recent_activity(self, limit: int = 10) -> ServiceResponse:
        """
        Fetch recent activity for dashboard.
        """
        logger.debug("Fetching recent activity limit=%s", limit)

        return self.dashboard_service.get_recent_activity(limit=limit)

    def get_staff_overview(self) -> ServiceResponse:
        """
        Fetch staff overview metrics.
        """
        logger.debug("Fetching staff overview")

        return self.dashboard_service.get_staff_overview()

    def get_revenue_trend(self, days: int = 7) -> ServiceResponse:
        """
        Fetch revenue trend data for charts.

        Used with matplotlib in UI.
        """
        logger.debug("Fetching revenue trend days=%s", days)

        return self.dashboard_service.get_revenue_trend(days=days)