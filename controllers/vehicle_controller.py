"""
controllers/vehicle_controller.py

Vehicle controller for GaragePulse.
Bridges UI with VehicleService for vehicle CRUD, search,
and prioritized listing (professor requirement).
"""

from __future__ import annotations

import logging
from typing import Optional

from services.vehicle_service import VehicleService
from utils.response import ServiceResponse


logger = logging.getLogger(__name__)


class VehicleController:
    """
    Controller for vehicle-related UI actions.
    """

    def __init__(self) -> None:
        self.vehicle_service = VehicleService()

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
        logger.info(
            "Creating vehicle for customer_id=%s plate=%s",
            customer_id,
            plate_number,
        )

        return self.vehicle_service.create_vehicle(
            customer_id=customer_id,
            make=make,
            model=model,
            vehicle_year=vehicle_year,
            vin=vin,
            plate_number=plate_number,
            color=color,
            mileage=mileage,
            notes=notes,
        )

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
        logger.info("Updating vehicle id=%s", vehicle_id)

        return self.vehicle_service.update_vehicle(
            vehicle_id=vehicle_id,
            make=make,
            model=model,
            vehicle_year=vehicle_year,
            vin=vin,
            plate_number=plate_number,
            color=color,
            mileage=mileage,
            notes=notes,
        )

    def search_by_plate(self, plate_fragment: str) -> ServiceResponse:
        """
        Search vehicles by vehicle number / license plate.

        Professor requirement:
        search using vehicle number.
        """
        logger.debug("Searching vehicles by plate=%s", plate_fragment)

        return self.vehicle_service.search_by_plate(plate_fragment)

    def get_vehicle(self, vehicle_id: int) -> ServiceResponse:
        """
        Get a specific vehicle.
        """
        logger.debug("Fetching vehicle id=%s", vehicle_id)

        return self.vehicle_service.get_vehicle(vehicle_id)

    def get_by_customer_id(self, customer_id: int) -> ServiceResponse:
        """
        Get all vehicles for a customer.
        """
        logger.debug("Fetching vehicles for customer_id=%s", customer_id)

        return self.vehicle_service.get_by_customer_id(customer_id)

    def get_all_vehicles(self) -> ServiceResponse:
        """
        Get all vehicles.
        """
        logger.debug("Fetching all vehicles")

        return self.vehicle_service.get_all_vehicles()

    def get_prioritized_vehicle_list(self) -> ServiceResponse:
        """
        Get prioritized vehicle list (in-progress + latest first).

        Professor requirement:
        emphasize latest / in-progress vehicles.
        """
        logger.debug("Fetching prioritized vehicle list")

        return self.vehicle_service.get_prioritized_vehicle_list()

    def deactivate_vehicle(self, vehicle_id: int) -> ServiceResponse:
        """
        Deactivate a vehicle.
        """
        logger.info("Deactivating vehicle id=%s", vehicle_id)

        return self.vehicle_service.deactivate_vehicle(vehicle_id)