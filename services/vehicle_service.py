"""
services/vehicle_service.py

Vehicle service for GaragePulse.
Handles business logic for vehicle operations, customer linkage,
plate search, prioritized listing, and corrected session exception handling.
"""

from __future__ import annotations

import logging
from typing import Optional

from repositories.customer_repository import CustomerRepository
from repositories.vehicle_repository import VehicleRepository
from services.session_service import SessionService
from utils.exceptions import AuthenticationError, AuthorizationError
from utils.response import ServiceResponse
from utils.validators import Validators


logger = logging.getLogger(__name__)


class VehicleService:
    """
    Business logic for vehicle management.
    """

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
        plate_number: str = "",
        color: Optional[str] = None,
        mileage: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Create a new vehicle linked to a customer.
        """
        try:
            SessionService.require_authentication()

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(
                    message="Customer not found."
                )

            make = (make or "").strip()
            model = (model or "").strip()
            vin = (vin or "").strip().upper() if vin else None
            plate_number = (plate_number or "").strip().upper()
            color = (color or "").strip() if color else None
            notes = (notes or "").strip() if notes else None

            Validators.require(make, "Make")
            Validators.require(model, "Model")
            Validators.validate_plate_number(plate_number)
            Validators.validate_vin(vin)
            Validators.validate_vehicle_year(vehicle_year)

            if mileage is not None:
                Validators.validate_positive_number(mileage, "Mileage")

            existing_plate = self.vehicle_repo.get_by_plate_number(plate_number)
            if existing_plate:
                return ServiceResponse.error_response(
                    message="A vehicle with this plate number already exists."
                )

            if vin:
                existing_vin = self.vehicle_repo.get_by_vin(vin)
                if existing_vin:
                    return ServiceResponse.error_response(
                        message="A vehicle with this VIN already exists."
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
                    "mileage": int(mileage) if mileage is not None else None,
                    "notes": notes,
                    "is_active": 1,
                    "created_by": actor_id,
                    "updated_by": actor_id,
                }
            )

            logger.info(
                "Vehicle created successfully: id=%s, customer_id=%s, plate=%s",
                vehicle_id,
                customer_id,
                plate_number,
            )

            return ServiceResponse.success_response(
                message="Vehicle created successfully.",
                data={"vehicle_id": vehicle_id},
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
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
        """
        Update an existing vehicle.
        """
        try:
            SessionService.require_authentication()

            existing = self.vehicle_repo.get_by_id(vehicle_id)
            if not existing or not existing.get("is_active"):
                return ServiceResponse.error_response(
                    message="Vehicle not found."
                )

            update_data = {}

            if make is not None:
                make = make.strip()
                Validators.require(make, "Make")
                update_data["make"] = make

            if model is not None:
                model = model.strip()
                Validators.require(model, "Model")
                update_data["model"] = model

            if vehicle_year is not None:
                Validators.validate_vehicle_year(vehicle_year)
                update_data["vehicle_year"] = vehicle_year

            if vin is not None:
                vin = vin.strip().upper()
                Validators.validate_vin(vin or None)

                if vin:
                    found = self.vehicle_repo.get_by_vin(vin)
                    if found and found["id"] != vehicle_id:
                        return ServiceResponse.error_response(
                            message="Another vehicle already uses this VIN."
                        )

                update_data["vin"] = vin or None

            if plate_number is not None:
                plate_number = plate_number.strip().upper()
                Validators.validate_plate_number(plate_number)

                found = self.vehicle_repo.get_by_plate_number(plate_number)
                if found and found["id"] != vehicle_id:
                    return ServiceResponse.error_response(
                        message="Another vehicle already uses this plate number."
                    )

                update_data["plate_number"] = plate_number

            if color is not None:
                update_data["color"] = color.strip() or None

            if mileage is not None:
                Validators.validate_positive_number(mileage, "Mileage")
                update_data["mileage"] = int(mileage)

            if notes is not None:
                update_data["notes"] = notes.strip() or None

            current_user = SessionService.get_current_user()
            actor_id = current_user.get("id") if current_user else None
            update_data["updated_by"] = actor_id

            if len(update_data) == 1 and "updated_by" in update_data:
                return ServiceResponse.error_response(
                    message="No fields to update."
                )

            self.vehicle_repo.update_vehicle(vehicle_id, update_data)

            logger.info("Vehicle updated successfully: id=%s", vehicle_id)

            return ServiceResponse.success_response(
                message="Vehicle updated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to update vehicle: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def search_by_plate(self, plate_fragment: str) -> ServiceResponse:
        """
        Search vehicles by plate number / vehicle number.

        Professor requirement:
        add search using vehicle number / license plate.
        """
        try:
            SessionService.require_authentication()

            plate_fragment = (plate_fragment or "").strip()
            if not plate_fragment:
                return ServiceResponse.error_response(
                    message="Enter vehicle number or plate to search."
                )

            vehicles = self.vehicle_repo.search_by_plate(plate_fragment.upper())

            return ServiceResponse.success_response(
                message="Vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to search vehicles by plate: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_vehicle(self, vehicle_id: int) -> ServiceResponse:
        """
        Get a single vehicle by ID.
        """
        try:
            SessionService.require_authentication()

            vehicle = self.vehicle_repo.get_by_id(vehicle_id)
            if not vehicle or not vehicle.get("is_active"):
                return ServiceResponse.error_response(
                    message="Vehicle not found."
                )

            return ServiceResponse.success_response(
                message="Vehicle retrieved successfully.",
                data=vehicle,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve vehicle: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_by_customer_id(self, customer_id: int) -> ServiceResponse:
        """
        Get all vehicles for a customer.
        """
        try:
            SessionService.require_authentication()

            customer = self.customer_repo.get_by_id(customer_id)
            if not customer or not customer.get("is_active"):
                return ServiceResponse.error_response(
                    message="Customer not found."
                )

            vehicles = self.vehicle_repo.get_by_customer_id(customer_id)

            return ServiceResponse.success_response(
                message="Customer vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve customer vehicles: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_all_vehicles(self) -> ServiceResponse:
        """
        Get all active vehicles.
        """
        try:
            SessionService.require_authentication()

            vehicles = self.vehicle_repo.get_all_vehicles()

            return ServiceResponse.success_response(
                message="Vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve vehicles: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def get_prioritized_vehicle_list(self) -> ServiceResponse:
        """
        Get vehicles ordered with in-progress/latest relevant vehicles first.

        Professor requirement:
        emphasize latest or in-progress relevant vehicles.
        """
        try:
            SessionService.require_authentication()

            vehicles = self.vehicle_repo.get_prioritized_vehicle_list()

            return ServiceResponse.success_response(
                message="Prioritized vehicles retrieved successfully.",
                data=vehicles,
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to retrieve prioritized vehicles: %s", exc)
            return ServiceResponse.error_response(message=str(exc))

    def deactivate_vehicle(self, vehicle_id: int) -> ServiceResponse:
        """
        Deactivate a vehicle.
        """
        try:
            SessionService.require_authentication()

            existing = self.vehicle_repo.get_by_id(vehicle_id)
            if not existing or not existing.get("is_active"):
                return ServiceResponse.error_response(
                    message="Vehicle not found."
                )

            self.vehicle_repo.deactivate_vehicle(vehicle_id)

            logger.info("Vehicle deactivated successfully: id=%s", vehicle_id)

            return ServiceResponse.success_response(
                message="Vehicle deactivated successfully."
            )

        except (AuthenticationError, AuthorizationError) as exc:
            logger.warning("Authentication/authorization failed: %s", exc)
            return ServiceResponse.error_response(message=str(exc))
        except Exception as exc:
            logger.exception("Failed to deactivate vehicle: %s", exc)
            return ServiceResponse.error_response(message=str(exc))