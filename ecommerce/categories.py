"""Category model for grouping products."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ecommerce.products import Product


class Category:
    """A product category (aggregates products)."""

    def __init__(self, name: str, description: str = "") -> None:
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")
        self._name: str = name.strip()
        self._description: str = description
        self._products: List[Product] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def products(self) -> List[Product]:
        return list(self._products)

    def add_product(self, product: Product) -> None:
        if product not in self._products:
            self._products.append(product)

    def remove_product(self, product: Product) -> None:
        if product in self._products:
            self._products.remove(product)

    def __repr__(self) -> str:
        return f"Category(name='{self._name}', products={len(self._products)})"
