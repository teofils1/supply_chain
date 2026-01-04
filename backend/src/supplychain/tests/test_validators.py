"""
Tests for custom validators.

This module tests the custom validators to ensure they properly validate
data according to business rules.
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from supplychain.validators import (
    validate_available_quantity_not_exceeds_produced,
    validate_expiry_after_manufacturing,
    validate_gtin_format,
    validate_lot_number_format,
    validate_serial_number_format,
    validate_temperature_range,
    validate_temperature_value,
    validate_tracking_number_format,
)


class TestDateValidators(TestCase):
    """Test date validation functions."""

    def test_valid_expiry_after_manufacturing(self):
        """Test valid expiry date after manufacturing date."""
        manufacturing = date(2024, 1, 1)
        expiry = date(2024, 12, 31)
        # Should not raise
        validate_expiry_after_manufacturing(manufacturing, expiry)

    def test_invalid_expiry_before_manufacturing(self):
        """Test invalid expiry date before manufacturing date."""
        manufacturing = date(2024, 12, 31)
        expiry = date(2024, 1, 1)
        with self.assertRaises(ValidationError):
            validate_expiry_after_manufacturing(manufacturing, expiry)

    def test_invalid_expiry_equals_manufacturing(self):
        """Test invalid expiry date equal to manufacturing date."""
        manufacturing = date(2024, 1, 1)
        expiry = date(2024, 1, 1)
        with self.assertRaises(ValidationError):
            validate_expiry_after_manufacturing(manufacturing, expiry)


class TestQuantityValidators:
    """Test quantity validation functions."""

    def test_valid_available_quantity(self):
        """Test valid available quantity."""
        validate_available_quantity_not_exceeds_produced(100, 50)
        validate_available_quantity_not_exceeds_produced(100, 100)

    def test_invalid_available_exceeds_produced(self):
        """Test invalid available quantity exceeding produced."""
        with pytest.raises(ValidationError):
            validate_available_quantity_not_exceeds_produced(100, 150)


class TestFormatValidators:
    """Test format validation functions."""

    def test_valid_tracking_numbers(self):
        """Test valid tracking number formats."""
        valid_numbers = [
            "TRK-2024-001",
            "SHIP_12345",
            "FDX789012345",
            "12345",
            "ABC-123-XYZ",
        ]
        for number in valid_numbers:
            validate_tracking_number_format(number)

    def test_invalid_tracking_numbers(self):
        """Test invalid tracking number formats."""
        invalid_numbers = [
            "TRK",  # Too short
            "TRACKING NUMBER WITH SPACES",  # Has spaces
            "TRK@123",  # Special characters
            "AB",  # Too short
            "A" * 51,  # Too long
        ]
        for number in invalid_numbers:
            with pytest.raises(ValidationError):
                validate_tracking_number_format(number)

    def test_valid_lot_numbers(self):
        """Test valid lot number formats."""
        valid_numbers = [
            "LOT-2024-001",
            "BATCH_A123",
            "MFG-2024-01-15-001",
            "123",
        ]
        for number in valid_numbers:
            validate_lot_number_format(number)

    def test_invalid_lot_numbers(self):
        """Test invalid lot number formats."""
        invalid_numbers = [
            "AB",  # Too short
            "LOT 001",  # Has spaces
            "LOT#123",  # Special character
        ]
        for number in invalid_numbers:
            with pytest.raises(ValidationError):
                validate_lot_number_format(number)

    def test_valid_serial_numbers(self):
        """Test valid serial number formats."""
        valid_numbers = [
            "SN-2024-001",
            "PACK_A123",
            "12345678",
        ]
        for number in valid_numbers:
            validate_serial_number_format(number)

    def test_valid_gtin(self):
        """Test valid GTIN formats."""
        # GTIN-14 with valid check digit
        validate_gtin_format("00012345678905")

    def test_invalid_gtin_check_digit(self):
        """Test GTIN with invalid check digit."""
        with pytest.raises(ValidationError):
            validate_gtin_format("00012345678906")  # Wrong check digit

    def test_invalid_gtin_length(self):
        """Test GTIN with invalid length."""
        with pytest.raises(ValidationError):
            validate_gtin_format("12345")  # Wrong length

    def test_invalid_gtin_non_numeric(self):
        """Test GTIN with non-numeric characters."""
        with pytest.raises(ValidationError):
            validate_gtin_format("0001234567890A")


class TestTemperatureValidators:
    """Test temperature validation functions."""

    def test_valid_temperature_range(self):
        """Test valid temperature ranges."""
        validate_temperature_range(-20, 25)
        validate_temperature_range(2, 8)
        validate_temperature_range(-80, -70)

    def test_invalid_temperature_range_min_greater_than_max(self):
        """Test invalid temperature range where min > max."""
        with pytest.raises(ValidationError):
            validate_temperature_range(25, 8)

    def test_invalid_temperature_out_of_bounds(self):
        """Test invalid temperature values out of bounds."""
        with pytest.raises(ValidationError):
            validate_temperature_range(-150, 25)  # Min too low

        with pytest.raises(ValidationError):
            validate_temperature_range(-20, 150)  # Max too high

    def test_valid_temperature_value(self):
        """Test valid single temperature values."""
        validate_temperature_value(-80)
        validate_temperature_value(25)
        validate_temperature_value(0)

    def test_invalid_temperature_value(self):
        """Test invalid single temperature values."""
        with pytest.raises(ValidationError):
            validate_temperature_value(-150)

        with pytest.raises(ValidationError):
            validate_temperature_value(150)
