"""Store — aggregation root for products and categories."""

from __future__ import annotations

from typing import Dict, List, Optional

from ecommerce.categories import Category
from ecommerce.exceptions import ProductNotFoundError
from ecommerce.products import Product


class Store:
    """Manages products and categories via aggregation.

    Demonstrates: Aggregation (products exist independently of store)
    """

    def __init__(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Store name cannot be empty")
        self._name: str = name.strip()
        self._products: Dict[str, Product] = {}
        self._categories: Dict[str, Category] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def products(self) -> List[Product]:
        return list(self._products.values())

    @property
    def categories(self) -> List[Category]:
        return list(self._categories.values())

    @property
    def product_count(self) -> int:
        return len(self._products)

    def add_product(self, product: Product) -> None:
        if product.product_id in self._products:
            return
        self._products[product.product_id] = product

    def remove_product(self, product_id: str) -> Product:
        if product_id not in self._products:
            raise ProductNotFoundError(product_id)
        return self._products.pop(product_id)

    def get_product(self, product_id: str) -> Product:
        if product_id not in self._products:
            raise ProductNotFoundError(product_id)
        return self._products[product_id]

    def search_products(self, query: str) -> List[Product]:
        q = query.lower().strip()
        return [
            p
            for p in self._products.values()
            if q in p.name.lower() or q in p.description.lower()
        ]

    def get_active_products(self) -> List[Product]:
        return [p for p in self._products.values() if p.is_active]

    def get_in_stock_products(self) -> List[Product]:
        return [
            p
            for p in self._products.values()
            if p.is_active and (not p.requires_shipping() or p.stock > 0)
        ]

    def add_category(self, category: Category) -> None:
        if category.name not in self._categories:
            self._categories[category.name] = category

    def remove_category(self, name: str) -> Category:
        if name not in self._categories:
            raise KeyError(f"Category '{name}' not found")
        return self._categories.pop(name)

    def get_category(self, name: str) -> Optional[Category]:
        return self._categories.get(name)

    def get_products_by_category(self, category_name: str) -> List[Product]:
        cat = self._categories.get(category_name)
        if cat is None:
            return []
        return cat.products

    def __repr__(self) -> str:
        return (
            f"Store(name='{self._name}', "
            f"products={self.product_count})"
        )
