"""
services/work_order_service.py

Work order business logic for GaragePulse.
Aligned with schema.sql, corrected status history fields,
and corrected session exception handling.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from config.constants import WorkOrderStatus, WORK_ORDER_STATUS_LIST
from repositories.customer_repository import CustomerRepository
from repositories.user_repository import UserRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.work_order_part_repository import WorkOrderPartRepository
from repositories.work_order_repository import WorkOrderRepository
from repositories.work_order_status_repository import WorkOrderStatusRepository
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.id_generator import IDGenerator
from utils.response import ServiceResponse
from utils.validators import Validators


logger = logging.getLogger(__name__)


class WorkOrderService:
    """
    Business logic for work order operations.
    """

    def __init__(self) -> None:
        self.work_order_repo = WorkOrderRepository()
        self.status_repo = WorkOrderStatusRepository()
        self.parts_repo = WorkOrderPartRepository()
        self.customer_repo = CustomerRepository()
        self.vehicle_repo = VehicleRepository()
        self.user_repo = UserRepository()

    def _generate_next_work_order_code(self) -> str:
        """
        Generate the next Work Order ID.
        """
        existing = self.work_order_repo.get_all_work_orders(limit=100000, offset=0)
        next_sequence = len(existing) + 1
        return IDGenerator.generate_work_order_id(next_sequence)

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
        try:
            SessionService.require_authentication()

            Validators.require(issue_description, "Issue description")

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(message="Customer not found.")

            vehicle = self.vehicle_repo.get_by_id(vehicle_id)
            if not vehicle or not vehicle.get("is_active"):
                return ServiceResponse.error_response(message="Vehicle not found.")

            if vehicle["customer_id"] != customer_id:
                return ServiceResponse.error_response(
                    message="Selected vehicle does not belong to the selected customer."
                )

            if assigned_staff_id is not None:
                staff_user = self.user_repo.get_by_id(assigned_staff_id)
                if not staff_user or staff_user.get("is_deleted"):
                    return ServiceResponse.error_response(
                        message="Assigned staff user not found."
                    )

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            work_order_code = self._generate_next_work_order_code()

            work_order_id = self.work_order_repo.create_work_order(
                {
                    "work_order_id": work_order_code,
                    "customer_id": customer_id,
                    "vehicle_id": vehicle_id,
                    "assigned_staff_id": assigned_staff_id,
                    "issue_description": issue_description.strip(),
                    "labor_cost": 0.0,
                    "parts_total": 0.0,
                    "subtotal": 0.0,
                    "current_status": WorkOrderStatus.NEW,
                    "notes": (notes or "").strip() or None,
                    "created_by": actor_id,
                    "updated_by": actor_id,
                }
            )

            self.status_repo.add_status_history(
                {
                    "work_order_id": work_order_id,
                    "status_value": WorkOrderStatus.NEW,
                    "status_note": "Work order created",
                    "changed_by": actor_id,
                }
            )

            logger.info(
                "Work order created successfully: id=%s, work_order_id=%s",
                work_order_id,
                work_order_code,
            )

            return ServiceResponse.success_response(
                message="Work order created successfully.",
                data={
                    "id": work_order_id,
                    "work_order_id": work_order_code,
                    "status": WorkOrderStatus.NEW,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to create work order: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def update_work_order(
        self,
        work_order_id: int,
        issue_description: Optional[str] = None,
        assigned_staff_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Update editable work order fields.
        """
        try:
            SessionService.require_authentication()

            existing = self.work_order_repo.get_by_id(work_order_id)
            if not existing:
                return ServiceResponse.error_response(message="Work order not found.")

            update_data = {}

            if issue_description is not None:
                issue_description = issue_description.strip()
                Validators.require(issue_description, "Issue description")
                update_data["issue_description"] = issue_description

            if assigned_staff_id is not None:
                staff_user = self.user_repo.get_by_id(assigned_staff_id)
                if not staff_user or staff_user.get("is_deleted"):
                    return ServiceResponse.error_response(
                        message="Assigned staff user not found."
                    )
                update_data["assigned_staff_id"] = assigned_staff_id

            if notes is not None:
                update_data["notes"] = notes.strip() or None

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            update_data["updated_by"] = actor_id

            if len(update_data) == 1 and "updated_by" in update_data:
                return ServiceResponse.error_response(message="No fields to update.")

            self.work_order_repo.update_work_order(work_order_id, update_data)

            logger.info("Work order updated successfully: id=%s", work_order_id)
            return ServiceResponse.success_response(
                message="Work order updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update work order: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def update_status(
        self,
        work_order_id: int,
        new_status: str,
        status_note: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Update work order status and append status history entry.
        """
        try:
            SessionService.require_authentication()

            if new_status not in WORK_ORDER_STATUS_LIST:
                return ServiceResponse.error_response(
                    message="Invalid work order status."
                )

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            current_status = work_order["current_status"]
            if current_status == new_status:
                return ServiceResponse.error_response(
                    message="Work order already has this status."
                )

            self.work_order_repo.update_status(work_order_id, new_status)

            update_data = {}
            if new_status == WorkOrderStatus.COMPLETED:
                update_data["completed_at"] = datetime.now()

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            update_data["updated_by"] = actor_id

            if update_data:
                self.work_order_repo.update_work_order(work_order_id, update_data)

            self.status_repo.add_status_history(
                {
                    "work_order_id": work_order_id,
                    "status_value": new_status,
                    "status_note": (status_note or "").strip() or None,
                    "changed_by": actor_id,
                }
            )

            logger.info(
                "Work order status updated: id=%s, %s -> %s",
                work_order_id,
                current_status,
                new_status,
            )

            return ServiceResponse.success_response(
                message="Work order status updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update work order status: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

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
        Add a part line to a work order and refresh totals.
        """
        try:
            SessionService.require_authentication()

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            part_name = (part_name or "").strip()
            Validators.require(part_name, "Part name")
            Validators.validate_positive_number(quantity, "Quantity")
            Validators.validate_positive_number(unit_price, "Unit price")

            quantity = int(quantity)
            unit_price = float(unit_price)
            line_total = quantity * unit_price if is_billable else 0.0

            self.parts_repo.create_part(
                {
                    "work_order_id": work_order_id,
                    "part_name": part_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "part_source": part_source,
                    "is_billable": 1 if is_billable else 0,
                    "line_total": line_total,
                    "notes": (notes or "").strip() or None,
                }
            )

            self._refresh_work_order_totals(work_order_id)

            logger.info(
                "Part added to work order: id=%s, part=%s",
                work_order_id,
                part_name,
            )
            return ServiceResponse.success_response(
                message="Part added successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to add part: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def set_labor_cost(
        self,
        work_order_id: int,
        labor_cost: float,
    ) -> ServiceResponse:
        """
        Set labor cost and refresh subtotal.
        """
        try:
            SessionService.require_authentication()

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            Validators.validate_positive_number(labor_cost, "Labor cost")
            labor_cost = float(labor_cost)

            parts_total = self.parts_repo.calculate_parts_total(work_order_id)
            subtotal = labor_cost + parts_total

            self.work_order_repo.update_costs(
                work_order_id=work_order_id,
                labor_cost=labor_cost,
                parts_total=parts_total,
                subtotal=subtotal,
            )

            logger.info("Labor cost updated for work order: id=%s", work_order_id)
            return ServiceResponse.success_response(
                message="Labor cost updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to set labor cost: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def assign_staff(
        self,
        work_order_id: int,
        staff_id: int,
    ) -> ServiceResponse:
        """
        Assign a staff user to a work order.
        """
        try:
            SessionService.require_authentication()

            work_order = self.work_order_repo.get_by_id(work_order_id)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            staff_user = self.user_repo.get_by_id(staff_id)
            if not staff_user or staff_user.get("is_deleted"):
                return ServiceResponse.error_response(message="Staff user not found.")

            self.work_order_repo.assign_staff(work_order_id, staff_id)

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            self.work_order_repo.update_work_order(
                work_order_id,
                {"updated_by": actor_id},
            )

            logger.info(
                "Staff assigned to work order: work_order_id=%s, staff_id=%s",
                work_order_id,
                staff_id,
            )

            return ServiceResponse.success_response(
                message="Staff assigned successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to assign staff: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_work_order(self, work_order_code: str) -> ServiceResponse:
        """
        Get a work order by business Work Order ID with parts and status history.
        """
        try:
            SessionService.require_authentication()

            work_order = self.work_order_repo.get_by_work_order_id(work_order_code)
            if not work_order:
                return ServiceResponse.error_response(message="Work order not found.")

            parts = self.parts_repo.get_by_work_order_id(work_order["id"])
            status_history = self.status_repo.get_status_history(work_order["id"])

            return ServiceResponse.success_response(
                message="Work order retrieved successfully.",
                data={
                    "work_order": work_order,
                    "parts": parts,
                    "status_history": status_history,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve work order: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_all_work_orders(self) -> ServiceResponse:
        """
        Get all work orders.
        """
        try:
            SessionService.require_authentication()

            work_orders = self.work_order_repo.get_all_work_orders()

            return ServiceResponse.success_response(
                message="Work orders retrieved successfully.",
                data=work_orders,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve work orders: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_active_work_orders(self) -> ServiceResponse:
        """
        Get active work orders.
        """
        try:
            SessionService.require_authentication()

            work_orders = self.work_order_repo.get_active_work_orders()

            return ServiceResponse.success_response(
                message="Active work orders retrieved successfully.",
                data=work_orders,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve active work orders: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_dashboard_stats(self) -> ServiceResponse:
        """
        Get work-order-based dashboard statistics.
        """
        try:
            SessionService.require_authentication()

            active_orders = self.work_order_repo.count_active_work_orders()
            completed_today = self.work_order_repo.count_completed_today()

            return ServiceResponse.success_response(
                message="Dashboard statistics retrieved successfully.",
                data={
                    "active_work_orders": active_orders,
                    "completed_today": completed_today,
                },
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to get dashboard stats: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def _refresh_work_order_totals(self, work_order_id: int) -> None:
        """
        Internal helper to recalculate parts_total and subtotal.
        """
        work_order = self.work_order_repo.get_by_id(work_order_id)
        if not work_order:
            raise ValueError("Work order not found.")

        labor_cost = float(work_order.get("labor_cost") or 0.0)
        parts_total = float(self.parts_repo.calculate_parts_total(work_order_id))
        subtotal = labor_cost + parts_total

        self.work_order_repo.update_costs(
            work_order_id=work_order_id,
            labor_cost=labor_cost,
            parts_total=parts_total,
            subtotal=subtotal,
        )