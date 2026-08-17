"""ShoppingCart and CartItem — composition and product price delegation."""

from __future__ import annotations

from typing import Dict, List, Optional

from ecommerce.enums import ProductType
from ecommerce.exceptions import (
    CartEmptyError,
    DuplicateItemError,
    InvalidQuantityError,
)
from ecommerce.products import Product


class CartItem:
    """A single item in the shopping cart.

    Demonstrates: Composition (owned by ShoppingCart), Association (references Product)
    """

    def __init__(self, product: Product, quantity: int = 1) -> None:
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        self._product: Product = product
        self._quantity: int = quantity

    @property
    def product(self) -> Product:
        return self._product

    @property
    def quantity(self) -> int:
        return self._quantity

    def set_quantity(self, quantity: int) -> None:
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        self._quantity = quantity

    def get_subtotal(self) -> float:
        """Delegate price calculation to the product (polymorphism)."""
        return self._product.calculate_price(self._quantity)

    def __repr__(self) -> str:
        return (
            f"CartItem(product='{self._product.name}', "
            f"quantity={self._quantity}, subtotal={self.get_subtotal()})"
        )


class ShoppingCart:
    """Manages a collection of CartItems.

    Demonstrates: Composition (owns CartItems)
    """

    def __init__(self) -> None:
        self._items: Dict[str, CartItem] = {}

    @property
    def items(self) -> List[CartItem]:
        return list(self._items.values())

    @property
    def is_empty(self) -> bool:
        return len(self._items) == 0

    @property
    def item_count(self) -> int:
        return len(self._items)

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self._items.values())

    def add_item(self, product: Product, quantity: int = 1) -> None:
        if product.product_id in self._items:
            existing = self._items[product.product_id]
            existing.set_quantity(existing.quantity + quantity)
        else:
            self._items[product.product_id] = CartItem(product, quantity)

    def remove_item(self, product_id: str) -> CartItem:
        if product_id not in self._items:
            raise KeyError(f"Product '{product_id}' not in cart")
        return self._items.pop(product_id)

    def update_quantity(self, product_id: str, quantity: int) -> None:
        if product_id not in self._items:
            raise KeyError(f"Product '{product_id}' not in cart")
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        self._items[product_id].set_quantity(quantity)

    def get_item(self, product_id: str) -> Optional[CartItem]:
        return self._items.get(product_id)

    def get_subtotal(self) -> float:
        """Sum of all item subtotals, each computed via product polymorphism."""
        return round(sum(item.get_subtotal() for item in self._items.values()), 2)

    def get_physical_items(self) -> List[CartItem]:
        """Return items that require shipping (polymorphic check)."""
        return [item for item in self._items.values() if item.product.requires_shipping()]

    def get_digital_items(self) -> List[CartItem]:
        """Return items that do not require shipping."""
        return [
            item for item in self._items.values() if not item.product.requires_shipping()
        ]

    def clear(self) -> None:
        self._items.clear()

    def __repr__(self) -> str:
        return (
            f"ShoppingCart(items={self.item_count}, "
            f"subtotal={self.get_subtotal()})"
        )
