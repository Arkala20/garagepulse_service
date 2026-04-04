"""
utils/id_generator.py

ID generation helpers for GaragePulse.
Creates human-friendly business IDs such as Work Order ID and Invoice Number.
"""

from __future__ import annotations

from config.constants import IDPrefixes


class IDGenerator:
    """
    Generates formatted business identifiers.
    """

    @staticmethod
    def generate_work_order_id(sequence_number: int) -> str:
        """
        Generate a formatted Work Order ID.

        Example:
            WO-000001
        """
        return f"{IDPrefixes.WORK_ORDER}-{sequence_number:06d}"

    @staticmethod
    def generate_invoice_number(sequence_number: int) -> str:
        """
        Generate a formatted Invoice Number.

        Example:
            INV-000001
        """
        return f"{IDPrefixes.INVOICE}-{sequence_number:06d}"

    @staticmethod
    def generate_customer_code(sequence_number: int) -> str:
        """
        Optional helper for future customer code generation.

        Example:
            CUS-000001
        """
        return f"{IDPrefixes.CUSTOMER}-{sequence_number:06d}"

    @staticmethod
    def generate_vehicle_code(sequence_number: int) -> str:
        """
        Optional helper for future vehicle code generation.

        Example:
            VEH-000001
        """
        return f"{IDPrefixes.VEHICLE}-{sequence_number:06d}"