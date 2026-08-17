"""Discount hierarchy with polymorphic discount calculation."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from ecommerce.enums import DiscountType
from ecommerce.exceptions import DiscountError


class Discount(ABC):
    """Abstract base discount.

    Demonstrates: Abstraction, Encapsulation
    """

    def __init__(self, name: str, code: str) -> None:
        if not name or not name.strip():
            raise ValueError("Discount name cannot be empty")
        if not code or not code.strip():
            raise ValueError("Discount code cannot be empty")
        self._discount_id: str = str(uuid.uuid4())[:8]
        self._name: str = name.strip()
        self._code: str = code.strip().upper()
        self._active: bool = True

    @property
    def discount_id(self) -> str:
        return self._discount_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def code(self) -> str:
        return self._code

    @property
    def is_active(self) -> bool:
        return self._active

    def deactivate(self) -> None:
        self._active = False

    def activate(self) -> None:
        self._active = True

    @abstractmethod
    def discount_type(self) -> DiscountType:
        """Return the concrete discount type. Demonstrates Polymorphism."""

    @abstractmethod
    def apply_discount(self, subtotal: float, quantity: int = 1) -> float:
        """Calculate the discount amount. Demonstrates Polymorphism.

        Returns the amount to subtract from subtotal.
        Never returns a negative value or more than subtotal.
        """

    def _clamp_discount(self, discount_amount: float, subtotal: float) -> float:
        """Ensure discount never makes total negative."""
        if discount_amount < 0:
            raise DiscountError("Discount amount cannot be negative")
        return round(min(discount_amount, subtotal), 2)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}', code='{self._code}')"


class PercentageDiscount(Discount):
    """Discount by percentage of subtotal.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(self, name: str, code: str, percentage: float) -> None:
        super().__init__(name, code)
        if not 0 < percentage <= 100:
            raise DiscountError(f"Percentage must be between 0 and 100, got {percentage}")
        self._percentage: float = percentage

    @property
    def percentage(self) -> float:
        return self._percentage

    def discount_type(self) -> DiscountType:
        return DiscountType.PERCENTAGE

    def apply_discount(self, subtotal: float, quantity: int = 1) -> float:
        amount = round(subtotal * (self._percentage / 100), 2)
        return self._clamp_discount(amount, subtotal)


class FixedAmountDiscount(Discount):
    """Discount by fixed dollar amount.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(self, name: str, code: str, amount: float) -> None:
        super().__init__(name, code)
        if amount <= 0:
            raise DiscountError(f"Fixed amount must be positive, got {amount}")
        self._amount: float = round(amount, 2)

    @property
    def amount(self) -> float:
        return self._amount

    def discount_type(self) -> DiscountType:
        return DiscountType.FIXED_AMOUNT

    def apply_discount(self, subtotal: float, quantity: int = 1) -> float:
        return self._clamp_discount(self._amount, subtotal)


class BuyOneGetOneDiscount(Discount):
    """BOGO: for every 2 items, 1 is free.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(self, name: str, code: str) -> None:
        super().__init__(name, code)

    def discount_type(self) -> DiscountType:
        return DiscountType.BUY_ONE_GET_ONE

    def apply_discount(self, subtotal: float, quantity: int = 1) -> float:
        if quantity <= 0:
            raise DiscountError("Quantity must be positive for BOGO")
        free_items = quantity // 2
        if free_items == 0:
            return 0.0
        unit_price = subtotal / quantity
        discount_amount = round(unit_price * free_items, 2)
        return self._clamp_discount(discount_amount, subtotal)


class SeasonalDiscount(Discount):
    """Seasonal discount: valid only within a date range.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(
        self,
        name: str,
        code: str,
        percentage: float,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        super().__init__(name, code)
        if not 0 < percentage <= 100:
            raise DiscountError(f"Percentage must be between 0 and 100, got {percentage}")
        if start_date >= end_date:
            raise DiscountError("Start date must be before end date")
        self._percentage: float = percentage
        self._start_date: datetime = start_date
        self._end_date: datetime = end_date

    @property
    def percentage(self) -> float:
        return self._percentage

    @property
    def start_date(self) -> datetime:
        return self._start_date

    @property
    def end_date(self) -> datetime:
        return self._end_date

    def is_valid_now(self) -> bool:
        now = datetime.now()
        return self._start_date <= now <= self._end_date

    def discount_type(self) -> DiscountType:
        return DiscountType.SEASONAL

    def apply_discount(self, subtotal: float, quantity: int = 1) -> float:
        if not self.is_valid_now():
            return 0.0
        amount = round(subtotal * (self._percentage / 100), 2)
        return self._clamp_discount(amount, subtotal)
