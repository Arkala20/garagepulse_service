"""
controllers/work_order_controller.py

Work Order controller for GaragePulse.
Handles creation, updates, status changes, parts, labor,
and retrieval of work orders.

Professor alignment:
- Uses "Work Order ID" terminology everywhere
"""

from __future__ import annotations

import logging
from typing import Optional

from services.work_order_service import WorkOrderService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class WorkOrderController:
    """
    Controller for work order UI actions.
    """

    def __init__(self) -> None:
        self.work_order_service = WorkOrderService()

    def create_work_order(
        self,
        customer_id: int,
        vehicle_id: int,
        issue_description: str,
        assigned_staff_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Create a new work order.
        """
        logger.info(
            "Creating work order for customer_id=%s vehicle_id=%s",
            customer_id,
            vehicle_id,
        )

        return self.work_order_service.create_work_order(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            issue_description=issue_description,
            assigned_staff_id=assigned_staff_id,
            notes=notes,
        )

    def update_work_order(
        self,
        work_order_id: int,
        issue_description: Optional[str] = None,
        assigned_staff_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Update work order details.
        """
        logger.info("Updating work order id=%s", work_order_id)

        return self.work_order_service.update_work_order(
            work_order_id=work_order_id,
            issue_description=issue_description,
            assigned_staff_id=assigned_staff_id,
            notes=notes,
        )

    def update_status(
        self,
        work_order_id: int,
        new_status: str,
        status_note: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Update work order status.
        """
        logger.info(
            "Updating work order status id=%s -> %s",
            work_order_id,
            new_status,
        )

        return self.work_order_service.update_status(
            work_order_id=work_order_id,
            new_status=new_status,
            status_note=status_note,
        )

    def add_part(
        self,
        work_order_id: int,
        part_name: str,
        quantity: int,
        unit_price: float,
        part_source: str = "SHOP",
        is_billable: bool = True,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Add a part to a work order.
        """
        logger.info(
            "Adding part to work_order_id=%s part=%s",
            work_order_id,
            part_name,
        )

        return self.work_order_service.add_part(
            work_order_id=work_order_id,
            part_name=part_name,
            quantity=quantity,
            unit_price=unit_price,
            part_source=part_source,
            is_billable=is_billable,
            notes=notes,
        )

    def set_labor_cost(
        self,
        work_order_id: int,
        labor_cost: float,
    ) -> ServiceResponse:
        """
        Set labor cost for a work order.
        """
        logger.info(
            "Setting labor cost for work_order_id=%s cost=%s",
            work_order_id,
            labor_cost,
        )

        return self.work_order_service.set_labor_cost(
            work_order_id=work_order_id,
            labor_cost=labor_cost,
        )

    def assign_staff(
        self,
        work_order_id: int,
        staff_id: int,
    ) -> ServiceResponse:
        """
        Assign staff to a work order.
        """
        logger.info(
            "Assigning staff_id=%s to work_order_id=%s",
            staff_id,
            work_order_id,
        )

        return self.work_order_service.assign_staff(
            work_order_id=work_order_id,
            staff_id=staff_id,
        )

    def get_work_order(self, work_order_code: str) -> ServiceResponse:
        """
        Get work order by business Work Order ID.
        """
        logger.debug("Fetching work order code=%s", work_order_code)

        return self.work_order_service.get_work_order(work_order_code)

    def get_all_work_orders(self) -> ServiceResponse:
        """
        Retrieve all work orders.
        """
        logger.debug("Fetching all work orders")

        return self.work_order_service.get_all_work_orders()

    def get_active_work_orders(self) -> ServiceResponse:
        """
        Retrieve active work orders.
        """
        logger.debug("Fetching active work orders")

        return self.work_order_service.get_active_work_orders()

    def get_dashboard_stats(self) -> ServiceResponse:
        """
        Retrieve work-order-related dashboard stats.
        """
        logger.debug("Fetching work order dashboard stats")

        return self.work_order_service.get_dashboard_stats()