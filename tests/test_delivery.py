"""Tests for the DeliveryMethod hierarchy."""

import pytest
from datetime import datetime, timedelta

from ecommerce.enums import DeliverySpeed
from ecommerce.delivery import (
    DeliveryMethod,
    StandardDelivery,
    ExpressDelivery,
    SameDayDelivery,
)


# ---------------------------------------------------------------------------
# StandardDelivery
# ---------------------------------------------------------------------------

class TestStandardDelivery:
    def test_creation(self):
        d = StandardDelivery()
        assert d.name == "Standard Delivery"

    def test_delivery_speed(self):
        d = StandardDelivery()
        assert d.delivery_speed() == DeliverySpeed.STANDARD

    def test_calculate_cost(self):
        d = StandardDelivery()
        assert d.calculate_cost(0) == 5.99
        assert d.calculate_cost(10) == round(5.99 + 10 * 1.50, 2)
        assert d.calculate_cost(2.5) == round(5.99 + 2.5 * 1.50, 2)

    def test_estimate_days(self):
        d = StandardDelivery()
        assert d.estimate_days() == (5, 7)

    def test_estimate_delivery_date(self):
        d = StandardDelivery()
        expected = datetime.now() + timedelta(days=7)
        result = d.estimate_delivery_date()
        assert result.date() == expected.date()


# ---------------------------------------------------------------------------
# ExpressDelivery
# ---------------------------------------------------------------------------

class TestExpressDelivery:
    def test_creation(self):
        d = ExpressDelivery()
        assert d.name == "Express Delivery"

    def test_delivery_speed(self):
        d = ExpressDelivery()
        assert d.delivery_speed() == DeliverySpeed.EXPRESS

    def test_calculate_cost(self):
        d = ExpressDelivery()
        assert d.calculate_cost(0) == 12.99
        assert d.calculate_cost(10) == round(12.99 + 10 * 3.00, 2)
        assert d.calculate_cost(2.5) == round(12.99 + 2.5 * 3.00, 2)

    def test_estimate_days(self):
        d = ExpressDelivery()
        assert d.estimate_days() == (2, 3)

    def test_estimate_delivery_date(self):
        d = ExpressDelivery()
        expected = datetime.now() + timedelta(days=3)
        result = d.estimate_delivery_date()
        assert result.date() == expected.date()


# ---------------------------------------------------------------------------
# SameDayDelivery
# ---------------------------------------------------------------------------

class TestSameDayDelivery:
    def test_creation(self):
        d = SameDayDelivery()
        assert d.name == "Same-Day Delivery"

    def test_delivery_speed(self):
        d = SameDayDelivery()
        assert d.delivery_speed() == DeliverySpeed.SAME_DAY

    def test_calculate_cost(self):
        d = SameDayDelivery()
        assert d.calculate_cost(0) == 24.99
        assert d.calculate_cost(10) == round(24.99 + 10 * 5.00, 2)
        assert d.calculate_cost(2.5) == round(24.99 + 2.5 * 5.00, 2)

    def test_estimate_days(self):
        d = SameDayDelivery()
        assert d.estimate_days() == (0, 0)

    def test_estimate_delivery_date(self):
        d = SameDayDelivery()
        result = d.estimate_delivery_date()
        assert result.date() == datetime.now().date()


# ---------------------------------------------------------------------------
# Negative weight
# ---------------------------------------------------------------------------

class TestNegativeWeight:
    def test_standard_negative_weight(self):
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            StandardDelivery().calculate_cost(-1)

    def test_express_negative_weight(self):
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            ExpressDelivery().calculate_cost(-1)

    def test_sameday_negative_weight(self):
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            SameDayDelivery().calculate_cost(-1)


# ---------------------------------------------------------------------------
# Empty name validation
# ---------------------------------------------------------------------------

class _MinimalDelivery(DeliveryMethod):
    """Concrete helper to test base-class validation."""

    def delivery_speed(self):
        return DeliverySpeed.STANDARD

    def calculate_cost(self, weight_kg, subtotal=0.0):
        return 0.0

    def estimate_delivery_date(self):
        return datetime.now()


class TestEmptyName:
    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Delivery method name cannot be empty"):
            _MinimalDelivery("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Delivery method name cannot be empty"):
            _MinimalDelivery("   ")

    def test_none_like_empty_raises(self):
        with pytest.raises(ValueError, match="Delivery method name cannot be empty"):
            _MinimalDelivery("")


# ---------------------------------------------------------------------------
# Polymorphism
# ---------------------------------------------------------------------------

class TestPolymorphism:
    def test_calculate_cost_varies_by_type(self):
        methods = [StandardDelivery(), ExpressDelivery(), SameDayDelivery()]
        costs = [m.calculate_cost(5) for m in methods]
        assert costs[0] < costs[1] < costs[2]

    def test_estimate_delivery_date_varies_by_type(self):
        methods = [StandardDelivery(), ExpressDelivery(), SameDayDelivery()]
        dates = [m.estimate_delivery_date() for m in methods]
        # All should be valid datetimes
        assert all(isinstance(d, datetime) for d in dates)
        # Same-day should be earliest, standard latest
        assert dates[2].date() <= dates[1].date() <= dates[0].date()

    def test_iterate_methods_polymorphically(self):
        methods = [StandardDelivery(), ExpressDelivery(), SameDayDelivery()]
        expected_costs = {
            round(5.99 + 5 * 1.50, 2),
            round(12.99 + 5 * 3.00, 2),
            round(24.99 + 5 * 5.00, 2),
        }
        seen_costs = set()
        seen_dates = set()
        seen_speeds = set()

        for m in methods:
            seen_costs.add(m.calculate_cost(5))
            seen_dates.add(m.estimate_delivery_date().date())
            seen_speeds.add(m.delivery_speed())

        assert seen_costs == expected_costs
        assert seen_speeds == {DeliverySpeed.STANDARD, DeliverySpeed.EXPRESS, DeliverySpeed.SAME_DAY}


# ---------------------------------------------------------------------------
# Base class cannot be instantiated
# ---------------------------------------------------------------------------

class TestBaseClass:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            DeliveryMethod("Test")
