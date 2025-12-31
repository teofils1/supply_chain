"""
Custom validators for supply chain models.

This module provides reusable validators for enforcing business rules and data integrity
across the supply chain tracking system.
"""

import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_expiry_after_manufacturing(manufacturing_date, expiry_date):
    """
    Validate that expiry date is after manufacturing date.

    Args:
        manufacturing_date: The manufacturing date
        expiry_date: The expiry date

    Raises:
        ValidationError: If expiry date is not after manufacturing date
    """
    if manufacturing_date and expiry_date:
        if expiry_date <= manufacturing_date:
            raise ValidationError(
                {
                    "expiry_date": "Expiry date must be after manufacturing date.",
                    "manufacturing_date": "Manufacturing date must be before expiry date.",
                }
            )


def validate_available_quantity_not_exceeds_produced(
    quantity_produced, available_quantity
):
    """
    Validate that available quantity does not exceed quantity produced.

    Args:
        quantity_produced: Total quantity produced
        available_quantity: Currently available quantity

    Raises:
        ValidationError: If available quantity exceeds produced quantity
    """
    if quantity_produced is not None and available_quantity is not None:
        if available_quantity > quantity_produced:
            raise ValidationError(
                {
                    "available_quantity": f"Available quantity ({available_quantity}) cannot exceed quantity produced ({quantity_produced})."
                }
            )


def validate_positive_quantity(value):
    """
    Validate that a quantity value is positive.

    Args:
        value: The quantity to validate

    Raises:
        ValidationError: If value is not positive
    """
    if value is not None and value < 0:
        raise ValidationError("Quantity must be a positive number.")


def validate_tracking_number_format(value):
    """
    Validate tracking number format.

    Tracking numbers should be alphanumeric and may contain hyphens or underscores.
    Length: 5-50 characters.

    Args:
        value: The tracking number to validate

    Raises:
        ValidationError: If tracking number format is invalid
    """
    if not value:
        return

    # Check length
    if len(value) < 5 or len(value) > 50:
        raise ValidationError(
            "Tracking number must be between 5 and 50 characters long."
        )

    # Check format: alphanumeric with hyphens and underscores allowed
    if not re.match(r"^[A-Za-z0-9_-]+$", value):
        raise ValidationError(
            "Tracking number must contain only letters, numbers, hyphens, and underscores."
        )


# Regex validator for tracking numbers (can be used in model field definition)
tracking_number_validator = RegexValidator(
    regex=r"^[A-Za-z0-9_-]{5,50}$",
    message="Tracking number must be 5-50 characters long and contain only letters, numbers, hyphens, and underscores.",
    code="invalid_tracking_number",
)


def validate_temperature_range(min_temp, max_temp):
    """
    Validate temperature range.

    Args:
        min_temp: Minimum temperature
        max_temp: Maximum temperature

    Raises:
        ValidationError: If temperature range is invalid
    """
    if min_temp is not None and max_temp is not None:
        if min_temp > max_temp:
            raise ValidationError(
                {
                    "min_temperature": "Minimum temperature cannot be greater than maximum temperature.",
                    "max_temperature": "Maximum temperature cannot be less than minimum temperature.",
                }
            )

        # Reasonable bounds for supply chain temperatures (-100°C to 100°C)
        if min_temp < -100 or min_temp > 100:
            raise ValidationError(
                {"min_temperature": "Minimum temperature must be between -100°C and 100°C."}
            )

        if max_temp < -100 or max_temp > 100:
            raise ValidationError(
                {"max_temperature": "Maximum temperature must be between -100°C and 100°C."}
            )


def validate_temperature_value(value):
    """
    Validate a single temperature value.

    Args:
        value: Temperature value in Celsius

    Raises:
        ValidationError: If temperature is outside reasonable bounds
    """
    if value is not None:
        if value < -100 or value > 100:
            raise ValidationError(
                "Temperature must be between -100°C and 100°C."
            )


def validate_gtin_format(value):
    """
    Validate GTIN (Global Trade Item Number) format.

    Supports GTIN-8, GTIN-12, GTIN-13, and GTIN-14.

    Args:
        value: The GTIN to validate

    Raises:
        ValidationError: If GTIN format is invalid
    """
    if not value:
        return

    # Remove any spaces or hyphens
    gtin = value.replace(" ", "").replace("-", "")

    # Check if numeric
    if not gtin.isdigit():
        raise ValidationError("GTIN must contain only digits.")

    # Check valid lengths
    valid_lengths = [8, 12, 13, 14]
    if len(gtin) not in valid_lengths:
        raise ValidationError(
            f"GTIN must be {', '.join(map(str, valid_lengths))} digits long."
        )

    # Validate check digit using GS1 algorithm
    if not _validate_gtin_check_digit(gtin):
        raise ValidationError("Invalid GTIN check digit.")


def _validate_gtin_check_digit(gtin):
    """
    Validate GTIN check digit using GS1 algorithm.

    Args:
        gtin: GTIN string (digits only)

    Returns:
        bool: True if check digit is valid
    """
    if not gtin:
        return False

    # Calculate check digit
    digits = [int(d) for d in gtin[:-1]]
    check_digit = int(gtin[-1])

    # GS1 algorithm: multiply odd positions by 3, even by 1, sum and mod 10
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:
            total += digit * 3
        else:
            total += digit

    calculated_check = (10 - (total % 10)) % 10

    return calculated_check == check_digit


def validate_lot_number_format(value):
    """
    Validate lot number format.

    Lot numbers should be alphanumeric and may contain hyphens or underscores.
    Length: 3-100 characters.

    Args:
        value: The lot number to validate

    Raises:
        ValidationError: If lot number format is invalid
    """
    if not value:
        return

    # Check length
    if len(value) < 3 or len(value) > 100:
        raise ValidationError("Lot number must be between 3 and 100 characters long.")

    # Check format: alphanumeric with hyphens and underscores allowed
    if not re.match(r"^[A-Za-z0-9_-]+$", value):
        raise ValidationError(
            "Lot number must contain only letters, numbers, hyphens, and underscores."
        )


def validate_serial_number_format(value):
    """
    Validate serial number format.

    Serial numbers should be alphanumeric and may contain hyphens or underscores.
    Length: 3-100 characters.

    Args:
        value: The serial number to validate

    Raises:
        ValidationError: If serial number format is invalid
    """
    if not value:
        return

    # Check length
    if len(value) < 3 or len(value) > 100:
        raise ValidationError(
            "Serial number must be between 3 and 100 characters long."
        )

    # Check format: alphanumeric with hyphens and underscores allowed
    if not re.match(r"^[A-Za-z0-9_-]+$", value):
        raise ValidationError(
            "Serial number must contain only letters, numbers, hyphens, and underscores."
        )
