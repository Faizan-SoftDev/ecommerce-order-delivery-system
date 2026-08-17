"""Product hierarchy with polymorphic pricing and stock management."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from ecommerce.categories import Category
from ecommerce.enums import ProductType
from ecommerce.exceptions import (
    InsufficientStockError,
    InvalidPriceError,
    InvalidQuantityError,
)


class Product(ABC):
    """Abstract base product.

    Demonstrates: Abstraction, Encapsulation
    """

    def __init__(
        self,
        name: str,
        price: float,
        description: str = "",
        stock: int = 0,
        category: Optional[Category] = None,
    ) -> None:
        if not name or not name.strip():
            raise ValueError("Product name cannot be empty")
        if price < 0:
            raise InvalidPriceError(price)
        if stock < 0:
            raise ValueError("Stock cannot be negative")

        self._product_id: str = str(uuid.uuid4())[:8]
        self._name: str = name.strip()
        self._price: float = round(price, 2)
        self._description: str = description
        self._stock: int = stock
        self._category: Optional[Category] = category
        self._active: bool = True

        if category is not None:
            category.add_product(self)

    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise InvalidPriceError(value)
        self._price = round(value, 2)

    @property
    def description(self) -> str:
        return self._description

    @property
    def stock(self) -> int:
        return self._stock

    @property
    def category(self) -> Optional[Category]:
        return self._category

    @property
    def is_active(self) -> bool:
        return self._active

    @abstractmethod
    def product_type(self) -> ProductType:
        """Return the concrete product type. Demonstrates Polymorphism."""

    @abstractmethod
    def requires_shipping(self) -> bool:
        """Whether this product needs physical shipping. Demonstrates Polymorphism."""

    def calculate_price(self, quantity: int = 1) -> float:
        """Calculate total price for a given quantity. Demonstrates Polymorphism."""
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        return round(self._price * quantity, 2)

    def increase_stock(self, amount: int) -> None:
        if amount <= 0:
            raise InvalidQuantityError(amount)
        self._stock += amount

    def decrease_stock(self, amount: int) -> None:
        if amount <= 0:
            raise InvalidQuantityError(amount)
        if self._stock < amount:
            raise InsufficientStockError(self._name, self._stock, amount)
        self._stock -= amount

    def deactivate(self) -> None:
        self._active = False

    def activate(self) -> None:
        self._active = True

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self._name}', price={self._price}, stock={self._stock})"
        )


class PhysicalProduct(Product):
    """Product that requires physical shipping and manages inventory stock.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(
        self,
        name: str,
        price: float,
        weight_kg: float,
        description: str = "",
        stock: int = 0,
        category: Optional[Category] = None,
    ) -> None:
        super().__init__(name, price, description, stock, category)
        if weight_kg <= 0:
            raise ValueError("Weight must be positive")
        self._weight_kg: float = weight_kg

    @property
    def weight_kg(self) -> float:
        return self._weight_kg

    def product_type(self) -> ProductType:
        return ProductType.PHYSICAL

    def requires_shipping(self) -> bool:
        return True

    def calculate_price(self, quantity: int = 1) -> float:
        base = super().calculate_price(quantity)
        return round(base, 2)


class DigitalProduct(Product):
    """Digital product that requires no physical shipping or stock.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(
        self,
        name: str,
        price: float,
        file_url: str,
        file_size_mb: float,
        description: str = "",
        category: Optional[Category] = None,
    ) -> None:
        super().__init__(name, price, description, stock=0, category=category)
        self._file_url: str = file_url
        self._file_size_mb: float = file_size_mb

    @property
    def file_url(self) -> str:
        return self._file_url

    @property
    def file_size_mb(self) -> float:
        return self._file_size_mb

    def product_type(self) -> ProductType:
        return ProductType.DIGITAL

    def requires_shipping(self) -> bool:
        return False

    def increase_stock(self, amount: int) -> None:
        pass

    def decrease_stock(self, amount: int) -> None:
        pass


class SubscriptionProduct(Product):
    """Subscription product with duration-based pricing.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(
        self,
        name: str,
        monthly_price: float,
        duration_months: int,
        description: str = "",
        category: Optional[Category] = None,
    ) -> None:
        super().__init__(name, monthly_price, description, stock=0, category=category)
        if duration_months <= 0:
            raise ValueError("Duration must be at least 1 month")
        self._duration_months: int = duration_months

    @property
    def duration_months(self) -> int:
        return self._duration_months

    def product_type(self) -> ProductType:
        return ProductType.SUBSCRIPTION

    def requires_shipping(self) -> bool:
        return False

    def calculate_price(self, quantity: int = 1) -> float:
        """Total price = monthly_price * duration * quantity."""
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        return round(self._price * self._duration_months * quantity, 2)

    def get_end_date(self, start_date: Optional[datetime] = None) -> datetime:
        start = start_date or datetime.now()
        return start + timedelta(days=self._duration_months * 30)

    def increase_stock(self, amount: int) -> None:
        pass

    def decrease_stock(self, amount: int) -> None:
        pass
