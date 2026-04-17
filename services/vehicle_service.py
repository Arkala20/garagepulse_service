"""
services/vehicle_service.py
"""

from __future__ import annotations

import logging
from typing import Optional

from repositories.customer_repository import CustomerRepository
from repositories.vehicle_repository import VehicleRepository
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class VehicleService:
    def __init__(self) -> None:
        self.vehicle_repo = VehicleRepository()
        self.customer_repo = CustomerRepository()

    def create_vehicle(
        self,
        customer_id: int,
        make: str,
        model: str,
        vehicle_year: Optional[int] = None,
        vin: Optional[str] = None,
        plate_number: Optional[str] = None,
        color: Optional[str] = None,
        mileage: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(message="Customer not found.")

            make = (make or "").strip()
            model = (model or "").strip()
            vin = (vin or "").strip() or None
            plate_number = (plate_number or "").strip() or None
            color = (color or "").strip() or None
            notes = (notes or "").strip() or None

            if not make:
                return ServiceResponse.error_response(message="Make is required.")
            if not model:
                return ServiceResponse.error_response(message="Model is required.")

            if plate_number:
                existing = self.vehicle_repo.get_by_plate_number(plate_number)
                if existing:
                    return ServiceResponse.error_response(
                        message="A vehicle with this plate number already exists."
                    )

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None

            vehicle_id = self.vehicle_repo.create_vehicle(
                {
                    "customer_id": customer_id,
                    "make": make,
                    "model": model,
                    "vehicle_year": vehicle_year,
                    "vin": vin,
                    "plate_number": plate_number,
                    "color": color,
                    "mileage": mileage,
                    "notes": notes,
                    "is_active": 1,
                    "created_by": actor_id,
                    "updated_by": actor_id,
                }
            )

            return ServiceResponse.success_response(
                message="Vehicle created successfully.",
                data={"vehicle_id": vehicle_id},
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to create vehicle: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def update_vehicle(
        self,
        vehicle_id: int,
        make: Optional[str] = None,
        model: Optional[str] = None,
        vehicle_year: Optional[int] = None,
        vin: Optional[str] = None,
        plate_number: Optional[str] = None,
        color: Optional[str] = None,
        mileage: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            existing = self.vehicle_repo.get_by_id(vehicle_id)
            if not existing or not existing.get("is_active"):
                return ServiceResponse.error_response(message="Vehicle not found.")

            update_data = {}

            if make is not None:
                make = make.strip()
                if not make:
                    return ServiceResponse.error_response(message="Make is required.")
                update_data["make"] = make

            if model is not None:
                model = model.strip()
                if not model:
                    return ServiceResponse.error_response(message="Model is required.")
                update_data["model"] = model

            if vehicle_year is not None:
                update_data["vehicle_year"] = vehicle_year

            if vin is not None:
                update_data["vin"] = vin.strip() or None

            if plate_number is not None:
                plate_number = plate_number.strip() or None
                if plate_number:
                    duplicate = self.vehicle_repo.get_by_plate_number(plate_number)
                    if duplicate and int(duplicate["id"]) != int(vehicle_id):
                        return ServiceResponse.error_response(
                            message="A vehicle with this plate number already exists."
                        )
                update_data["plate_number"] = plate_number

            if color is not None:
                update_data["color"] = color.strip() or None

            if mileage is not None:
                update_data["mileage"] = mileage

            if notes is not None:
                update_data["notes"] = notes.strip() or None

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            update_data["updated_by"] = actor_id

            self.vehicle_repo.update_vehicle(vehicle_id, update_data)

            return ServiceResponse.success_response(
                message="Vehicle updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update vehicle: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_vehicle(self, vehicle_id: int) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            vehicle = self.vehicle_repo.get_by_id(vehicle_id)
            if not vehicle or not vehicle.get("is_active"):
                return ServiceResponse.error_response(message="Vehicle not found.")

            return ServiceResponse.success_response(
                message="Vehicle retrieved successfully.",
                data=vehicle,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to get vehicle: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_by_customer_id(self, customer_id: int) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            vehicles = self.vehicle_repo.get_by_customer_id(customer_id)

            return ServiceResponse.success_response(
                message="Vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to get vehicles by customer: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def search_by_plate(self, plate_fragment: str) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            plate_fragment = (plate_fragment or "").strip()
            if not plate_fragment:
                return ServiceResponse.error_response(
                    message="Enter a plate number to search."
                )

            vehicles = self.vehicle_repo.search_by_plate(plate_fragment)

            return ServiceResponse.success_response(
                message="Vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to search vehicles: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_prioritized_vehicle_list(self) -> ServiceResponse:
        try:
            SessionService.require_authentication()

            vehicles = self.vehicle_repo.get_prioritized_vehicle_list()

            return ServiceResponse.success_response(
                message="Vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to get prioritized vehicles: %s", exc)
            return ServiceResponse.error_response(message=str(exc))