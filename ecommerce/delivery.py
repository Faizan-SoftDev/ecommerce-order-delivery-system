"""Delivery method hierarchy with polymorphic cost calculation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from ecommerce.enums import DeliverySpeed


class DeliveryMethod(ABC):
    """Abstract base delivery method.

    Demonstrates: Abstraction, Encapsulation
    """

    def __init__(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Delivery method name cannot be empty")
        self._name: str = name.strip()
        self._estimated_days_min: int = 0
        self._estimated_days_max: int = 0

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def delivery_speed(self) -> DeliverySpeed:
        """Return the concrete delivery speed type. Demonstrates Polymorphism."""

    @abstractmethod
    def calculate_cost(self, weight_kg: float, subtotal: float = 0.0) -> float:
        """Calculate shipping cost. Demonstrates Polymorphism."""

    @abstractmethod
    def estimate_delivery_date(self) -> datetime:
        """Estimate delivery date. Demonstrates Polymorphism."""

    def estimate_days(self) -> tuple[int, int]:
        return (self._estimated_days_min, self._estimated_days_max)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}')"


class StandardDelivery(DeliveryMethod):
    """Standard delivery: 5-7 business days, base + weight rate.

    Demonstrates: Inheritance, Polymorphism
    """

    BASE_COST: float = 5.99
    COST_PER_KG: float = 1.50

    def __init__(self) -> None:
        super().__init__(name="Standard Delivery")
        self._estimated_days_min = 5
        self._estimated_days_max = 7

    def delivery_speed(self) -> DeliverySpeed:
        return DeliverySpeed.STANDARD

    def calculate_cost(self, weight_kg: float, subtotal: float = 0.0) -> float:
        if weight_kg < 0:
            raise ValueError("Weight cannot be negative")
        cost = self.BASE_COST + (weight_kg * self.COST_PER_KG)
        return round(cost, 2)

    def estimate_delivery_date(self) -> datetime:
        return datetime.now() + timedelta(days=self._estimated_days_max)


class ExpressDelivery(DeliveryMethod):
    """Express delivery: 2-3 business days, higher rate.

    Demonstrates: Inheritance, Polymorphism
    """

    BASE_COST: float = 12.99
    COST_PER_KG: float = 3.00

    def __init__(self) -> None:
        super().__init__(name="Express Delivery")
        self._estimated_days_min = 2
        self._estimated_days_max = 3

    def delivery_speed(self) -> DeliverySpeed:
        return DeliverySpeed.EXPRESS

    def calculate_cost(self, weight_kg: float, subtotal: float = 0.0) -> float:
        if weight_kg < 0:
            raise ValueError("Weight cannot be negative")
        cost = self.BASE_COST + (weight_kg * self.COST_PER_KG)
        return round(cost, 2)

    def estimate_delivery_date(self) -> datetime:
        return datetime.now() + timedelta(days=self._estimated_days_max)


class SameDayDelivery(DeliveryMethod):
    """Same-day delivery: delivers today, premium rate.

    Demonstrates: Inheritance, Polymorphism
    """

    BASE_COST: float = 24.99
    COST_PER_KG: float = 5.00

    def __init__(self) -> None:
        super().__init__(name="Same-Day Delivery")
        self._estimated_days_min = 0
        self._estimated_days_max = 0

    def delivery_speed(self) -> DeliverySpeed:
        return DeliverySpeed.SAME_DAY

    def calculate_cost(self, weight_kg: float, subtotal: float = 0.0) -> float:
        if weight_kg < 0:
            raise ValueError("Weight cannot be negative")
        cost = self.BASE_COST + (weight_kg * self.COST_PER_KG)
        return round(cost, 2)

    def estimate_delivery_date(self) -> datetime:
        return datetime.now()
