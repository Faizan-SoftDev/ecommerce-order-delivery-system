"""User hierarchy: User -> Customer -> {Regular, Premium, Business}, Admin."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

from ecommerce.enums import CustomerType

if TYPE_CHECKING:
    from ecommerce.orders import Order


class User(ABC):
    """Abstract base user.

    Demonstrates: Abstraction, Encapsulation
    """

    def __init__(self, name: str, email: str) -> None:
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        if not email or "@" not in email:
            raise ValueError(f"Invalid email: {email}")
        self._user_id: str = str(uuid.uuid4())[:8]
        self._name: str = name.strip()
        self._email: str = email.strip().lower()

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}')"


class Customer(User):
    """Customer base with balance, orders, and polymorphic discounts.

    Demonstrates: Inheritance, Polymorphism, Association
    """

    def __init__(self, name: str, email: str, address: str = "") -> None:
        super().__init__(name, email)
        self._address: str = address
        self._balance: float = 0.0
        self._orders: List[Order] = []
        self._customer_type: CustomerType = CustomerType.REGULAR

    @property
    def address(self) -> str:
        return self._address

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def orders(self) -> List[Order]:
        return list(self._orders)

    @property
    def customer_type(self) -> CustomerType:
        return self._customer_type

    def add_balance(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance = round(self._balance + amount, 2)

    def deduct_balance(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deduction amount must be positive")
        if self._balance < amount:
            raise ValueError(
                f"Insufficient balance: have ${self._balance:.2f}, need ${amount:.2f}"
            )
        self._balance = round(self._balance - amount, 2)

    def add_order(self, order: Order) -> None:
        if order not in self._orders:
            self._orders.append(order)

    def remove_order(self, order: Order) -> None:
        if order in self._orders:
            self._orders.remove(order)

    @abstractmethod
    def calculate_discount(self, subtotal: float) -> float:
        """Calculate customer-specific discount. Polymorphic method."""

    @abstractmethod
    def get_shipping_surcharge(self, base_cost: float) -> float:
        """Calculate shipping surcharge/discount. Polymorphic method."""


class RegularCustomer(Customer):
    """Regular customer with basic 5% discount.

    Demonstrates: Polymorphism
    """

    def __init__(self, name: str, email: str, address: str = "") -> None:
        super().__init__(name, email, address)
        self._customer_type = CustomerType.REGULAR

    def calculate_discount(self, subtotal: float) -> float:
        return round(subtotal * 0.05, 2)

    def get_shipping_surcharge(self, base_cost: float) -> float:
        return round(base_cost, 2)


class PremiumCustomer(Customer):
    """Premium customer with 10% discount and free shipping over $50.

    Demonstrates: Polymorphism
    """

    def __init__(self, name: str, email: str, address: str = "") -> None:
        super().__init__(name, email, address)
        self._customer_type = CustomerType.PREMIUM

    def calculate_discount(self, subtotal: float) -> float:
        return round(subtotal * 0.10, 2)

    def get_shipping_surcharge(self, base_cost: float) -> float:
        return 0.0


class BusinessCustomer(Customer):
    """Business customer with 15% discount and no shipping surcharge.

    Demonstrates: Polymorphism
    """

    def __init__(
        self, name: str, email: str, address: str = "", company: str = ""
    ) -> None:
        super().__init__(name, email, address)
        self._company: str = company
        self._customer_type = CustomerType.BUSINESS

    @property
    def company(self) -> str:
        return self._company

    def calculate_discount(self, subtotal: float) -> float:
        return round(subtotal * 0.15, 2)

    def get_shipping_surcharge(self, base_cost: float) -> float:
        return 0.0


class Admin(User):
    """Admin user for store management.

    Demonstrates: Inheritance
    """

    def __init__(self, name: str, email: str, role: str = "admin") -> None:
        super().__init__(name, email)
        self._role: str = role

    @property
    def role(self) -> str:
        return self._role
