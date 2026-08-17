"""Tests for the Discount hierarchy."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from ecommerce.discounts import (
    BuyOneGetOneDiscount,
    Discount,
    FixedAmountDiscount,
    PercentageDiscount,
    SeasonalDiscount,
)
from ecommerce.enums import DiscountType
from ecommerce.exceptions import DiscountError


# ---------------------------------------------------------------------------
# PercentageDiscount
# ---------------------------------------------------------------------------


class TestPercentageDiscount:
    """Tests for PercentageDiscount."""

    def test_creation(self) -> None:
        d = PercentageDiscount("Summer Sale", "SUMMER20", 20)
        assert d.name == "Summer Sale"
        assert d.code == "SUMMER20"
        assert d.percentage == 20
        assert d.discount_type() == DiscountType.PERCENTAGE

    def test_apply_discount(self) -> None:
        d = PercentageDiscount("10% Off", "TEN", 10)
        assert d.apply_discount(200.0) == 20.0

    def test_apply_discount_fractional(self) -> None:
        d = PercentageDiscount("15% Off", "FIFTEEN", 15)
        assert d.apply_discount(100.0) == 15.0

    def test_apply_discount_100_percent(self) -> None:
        d = PercentageDiscount("Free!", "FREE", 100)
        assert d.apply_discount(50.0) == 50.0

    def test_percentage_property(self) -> None:
        d = PercentageDiscount("Test", "T", 33)
        assert d.percentage == 33

    def test_name_and_code_properties(self) -> None:
        d = PercentageDiscount("My Disc", "MYCODE", 10)
        assert d.name == "My Disc"
        assert d.code == "MYCODE"

    def test_invalid_percentage_zero(self) -> None:
        with pytest.raises(DiscountError):
            PercentageDiscount("Bad", "B", 0)

    def test_invalid_percentage_negative(self) -> None:
        with pytest.raises(DiscountError):
            PercentageDiscount("Bad", "B", -5)

    def test_invalid_percentage_over_100(self) -> None:
        with pytest.raises(DiscountError):
            PercentageDiscount("Bad", "B", 101)


# ---------------------------------------------------------------------------
# FixedAmountDiscount
# ---------------------------------------------------------------------------


class TestFixedAmountDiscount:
    """Tests for FixedAmountDiscount."""

    def test_creation(self) -> None:
        d = FixedAmountDiscount("$10 Off", "SAVE10", 10)
        assert d.name == "$10 Off"
        assert d.code == "SAVE10"
        assert d.amount == 10
        assert d.discount_type() == DiscountType.FIXED_AMOUNT

    def test_apply_discount(self) -> None:
        d = FixedAmountDiscount("$25 Off", "SAVE25", 25)
        assert d.apply_discount(100.0) == 25.0

    def test_discount_clamped_to_subtotal(self) -> None:
        d = FixedAmountDiscount("$50 Off", "BIG", 50)
        assert d.apply_discount(30.0) == 30.0

    def test_invalid_amount_zero(self) -> None:
        with pytest.raises(DiscountError):
            FixedAmountDiscount("Bad", "B", 0)

    def test_invalid_amount_negative(self) -> None:
        with pytest.raises(DiscountError):
            FixedAmountDiscount("Bad", "B", -10)


# ---------------------------------------------------------------------------
# BuyOneGetOneDiscount
# ---------------------------------------------------------------------------


class TestBuyOneGetOneDiscount:
    """Tests for BuyOneGetOneDiscount."""

    def test_creation(self) -> None:
        d = BuyOneGetOneDiscount("BOGO", "BOGO")
        assert d.discount_type() == DiscountType.BUY_ONE_GET_ONE

    def test_apply_discount_quantity_4(self) -> None:
        d = BuyOneGetOneDiscount("BOGO", "BOGO")
        # subtotal=40, quantity=4 → unit_price=10, free_items=2 → 20
        assert d.apply_discount(40.0, quantity=4) == 20.0

    def test_apply_discount_quantity_1(self) -> None:
        d = BuyOneGetOneDiscount("BOGO", "BOGO")
        assert d.apply_discount(10.0, quantity=1) == 0.0

    def test_apply_discount_quantity_3(self) -> None:
        d = BuyOneGetOneDiscount("BOGO", "BOGO")
        # subtotal=30, quantity=3 → unit_price=10, free_items=1 → 10
        assert d.apply_discount(30.0, quantity=3) == 10.0

    def test_apply_discount_quantity_2(self) -> None:
        d = BuyOneGetOneDiscount("BOGO", "BOGO")
        # subtotal=20, quantity=2 → unit_price=10, free_items=1 → 10
        assert d.apply_discount(20.0, quantity=2) == 10.0

    def test_apply_discount_quantity_0_raises(self) -> None:
        d = BuyOneGetOneDiscount("BOGO", "BOGO")
        with pytest.raises(DiscountError):
            d.apply_discount(10.0, quantity=0)


# ---------------------------------------------------------------------------
# SeasonalDiscount
# ---------------------------------------------------------------------------


class TestSeasonalDiscount:
    """Tests for SeasonalDiscount."""

    def test_creation(self) -> None:
        start = datetime(2026, 6, 1)
        end = datetime(2026, 8, 31)
        d = SeasonalDiscount("Summer", "S26", 25, start, end)
        assert d.name == "Summer"
        assert d.code == "S26"
        assert d.percentage == 25
        assert d.start_date == start
        assert d.end_date == end
        assert d.discount_type() == DiscountType.SEASONAL

    def test_apply_discount_within_valid_period(self) -> None:
        start = datetime(2026, 1, 1)
        end = datetime(2026, 12, 31)
        d = SeasonalDiscount("Annual", "ANN", 10, start, end)
        with patch("ecommerce.discounts.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 15)
            assert d.apply_discount(200.0) == 20.0

    def test_apply_discount_outside_valid_period(self) -> None:
        start = datetime(2026, 1, 1)
        end = datetime(2026, 3, 31)
        d = SeasonalDiscount("Q1", "Q1", 10, start, end)
        with patch("ecommerce.discounts.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 7, 1)
            assert d.apply_discount(200.0) == 0.0

    def test_is_valid_now_true(self) -> None:
        now = datetime.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)
        d = SeasonalDiscount("Active", "ACT", 10, start, end)
        assert d.is_valid_now() is True

    def test_is_valid_now_false_past(self) -> None:
        start = datetime(2020, 1, 1)
        end = datetime(2020, 12, 31)
        d = SeasonalDiscount("Old", "OLD", 10, start, end)
        assert d.is_valid_now() is False

    def test_is_valid_now_false_future(self) -> None:
        start = datetime(2099, 1, 1)
        end = datetime(2099, 12, 31)
        d = SeasonalDiscount("Future", "FUT", 10, start, end)
        assert d.is_valid_now() is False

    def test_invalid_percentage(self) -> None:
        start = datetime(2026, 1, 1)
        end = datetime(2026, 12, 31)
        with pytest.raises(DiscountError):
            SeasonalDiscount("Bad", "B", 0, start, end)

    def test_start_gte_end_raises(self) -> None:
        start = datetime(2026, 12, 31)
        end = datetime(2026, 1, 1)
        with pytest.raises(DiscountError):
            SeasonalDiscount("Bad", "B", 10, start, end)

    def test_start_equals_end_raises(self) -> None:
        date = datetime(2026, 6, 15)
        with pytest.raises(DiscountError):
            SeasonalDiscount("Bad", "B", 10, date, date)


# ---------------------------------------------------------------------------
# Base Discount
# ---------------------------------------------------------------------------


class TestBaseDiscount:
    """Tests for the abstract Discount base class."""

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            PercentageDiscount("", "CODE", 10)

    def test_empty_code_rejected(self) -> None:
        with pytest.raises(ValueError, match="code cannot be empty"):
            PercentageDiscount("Name", "", 10)

    def test_whitespace_name_rejected(self) -> None:
        with pytest.raises(ValueError):
            PercentageDiscount("   ", "CODE", 10)

    def test_activate_deactivate(self) -> None:
        d = PercentageDiscount("Test", "T", 10)
        assert d.is_active is True
        d.deactivate()
        assert d.is_active is False
        d.activate()
        assert d.is_active is True

    def test_clamp_discount_never_negative(self) -> None:
        d = PercentageDiscount("Test", "T", 10)
        with pytest.raises(DiscountError, match="cannot be negative"):
            d._clamp_discount(-5.0, 100.0)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            Discount("Test", "T")  # type: ignore[abstract]

    def test_discount_id_is_generated(self) -> None:
        d = PercentageDiscount("Test", "T", 10)
        assert isinstance(d.discount_id, str)
        assert len(d.discount_id) == 8


# ---------------------------------------------------------------------------
# Polymorphism
# ---------------------------------------------------------------------------


class TestPolymorphism:
    """Tests that discounts work polymorphically."""

    def test_polymorphic_apply_discount(self) -> None:
        discounts: list[Discount] = [
            PercentageDiscount("P10", "P10", 10),
            FixedAmountDiscount("$20", "F20", 20),
            BuyOneGetOneDiscount("BOGO", "BOGO"),
        ]
        results = [d.apply_discount(100.0) for d in discounts]
        assert results == [10.0, 20.0, 0.0]

    def test_polymorphic_discount_type(self) -> None:
        discounts: list[Discount] = [
            PercentageDiscount("P", "P", 10),
            FixedAmountDiscount("F", "F", 10),
            BuyOneGetOneDiscount("B", "B"),
        ]
        types = [d.discount_type() for d in discounts]
        assert types == [
            DiscountType.PERCENTAGE,
            DiscountType.FIXED_AMOUNT,
            DiscountType.BUY_ONE_GET_ONE,
        ]

    def test_polymorphic_with_seasonal(self) -> None:
        now = datetime.now()
        discounts: list[Discount] = [
            PercentageDiscount("P25", "P25", 25),
            SeasonalDiscount("S", "S", 50, now - timedelta(days=1), now + timedelta(days=1)),
        ]
        results = [d.apply_discount(200.0) for d in discounts]
        assert results == [50.0, 100.0]
