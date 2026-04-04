"""
services/dashboard_service.py

Dashboard service for GaragePulse.
Provides stable summary metrics for the Owner/Admin dashboard.
"""

from __future__ import annotations

import logging

from repositories.invoice_repository import InvoiceRepository
from repositories.user_repository import UserRepository
from repositories.work_order_repository import WorkOrderRepository
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class DashboardService:
    """
    Business logic for dashboard aggregation.
    """

    def __init__(self) -> None:
        self.work_order_repo = WorkOrderRepository()
        self.invoice_repo = InvoiceRepository()
        self.user_repo = UserRepository()

    def get_dashboard_summary(self) -> ServiceResponse:
        """
        Return main dashboard summary cards.

        Includes:
        - total revenue
        - active work orders
        - completed jobs today
        - pending payments
        """
        try:
            SessionService.require_authentication()

            total_revenue = self.invoice_repo.get_total_revenue()
            active_work_orders = self.work_order_repo.count_active_work_orders()
            completed_today = self.work_order_repo.count_completed_today()
            pending_payments = self.invoice_repo.get_pending_payments_count()

            return ServiceResponse.success_response(
                message="Dashboard summary retrieved successfully.",
                data={
                    "total_revenue": float(total_revenue or 0.0),
                    "active_work_orders": int(active_work_orders or 0),
                    "completed_today": int(completed_today or 0),
                    "pending_payments": int(pending_payments or 0),
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Dashboard auth error: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Dashboard summary failed: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to load dashboard summary."
            )

    def get_recent_activity(self, limit: int = 10) -> ServiceResponse:
        """
        Placeholder-safe recent activity response for now.
        """
        try:
            SessionService.require_authentication()

            activities = self.work_order_repo.get_all_work_orders(limit=limit, offset=0)

            return ServiceResponse.success_response(
                message="Recent activity retrieved successfully.",
                data=activities,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Recent activity auth error: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Recent activity failed: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to load recent activity."
            )

    def get_staff_overview(self) -> ServiceResponse:
        """
        Return staff overview metrics.
        """
        try:
            SessionService.require_authentication()

            all_staff = self.user_repo.get_all_staff()
            active_staff = self.user_repo.get_active_users()
            inactive_staff = self.user_repo.get_inactive_users()

            return ServiceResponse.success_response(
                message="Staff overview retrieved successfully.",
                data={
                    "total_staff": len(all_staff),
                    "active_staff": len(active_staff),
                    "inactive_staff": len(inactive_staff),
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Staff overview auth error: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Staff overview failed: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to load staff overview."
            )

    def get_revenue_trend(self, days: int = 7) -> ServiceResponse:
        """
        Placeholder-safe revenue trend response for now.
        """
        try:
            SessionService.require_authentication()

            return ServiceResponse.success_response(
                message="Revenue trend retrieved successfully.",
                data=[],
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Revenue trend auth error: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Revenue trend failed: %s", exc)
            return ServiceResponse.error_response(
                message="Failed to load revenue trend."
            )