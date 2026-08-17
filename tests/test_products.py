"""Tests for the Product hierarchy and Category."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from ecommerce.products import (
    Product,
    PhysicalProduct,
    DigitalProduct,
    SubscriptionProduct,
)
from ecommerce.categories import Category
from ecommerce.enums import ProductType
from ecommerce.exceptions import (
    InsufficientStockError,
    InvalidPriceError,
    InvalidQuantityError,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_category(name: str = "Electronics") -> Category:
    return Category(name)


# ===========================================================================
# 1. PhysicalProduct
# ===========================================================================

class TestPhysicalProduct:

    def test_creation(self):
        p = PhysicalProduct("Widget", 9.99, weight_kg=0.5, stock=10)
        assert p.name == "Widget"
        assert p.price == 9.99
        assert p.weight_kg == 0.5
        assert p.stock == 10
        assert p.is_active is True

    def test_requires_shipping(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        assert p.requires_shipping() is True

    def test_product_type(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        assert p.product_type() == ProductType.PHYSICAL

    def test_calculate_price_single(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        assert p.calculate_price(1) == 10.0

    def test_calculate_price_multiple(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        assert p.calculate_price(5) == 50.0

    def test_calculate_price_rounding(self):
        p = PhysicalProduct("Widget", 9.99, weight_kg=1.0)
        assert p.calculate_price(3) == 29.97

    def test_increase_stock(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=5)
        p.increase_stock(3)
        assert p.stock == 8

    def test_decrease_stock(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=10)
        p.decrease_stock(4)
        assert p.stock == 6

    def test_insufficient_stock_error(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=2)
        with pytest.raises(InsufficientStockError) as exc_info:
            p.decrease_stock(5)
        assert exc_info.value.product_name == "Widget"
        assert exc_info.value.available == 2
        assert exc_info.value.requested == 5

    def test_invalid_quantity_increase(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=5)
        with pytest.raises(InvalidQuantityError):
            p.increase_stock(0)

    def test_invalid_quantity_decrease(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=5)
        with pytest.raises(InvalidQuantityError):
            p.decrease_stock(-1)

    def test_invalid_quantity_calculate_price(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        with pytest.raises(InvalidQuantityError):
            p.calculate_price(0)

    def test_negative_price_rejected(self):
        with pytest.raises(InvalidPriceError):
            PhysicalProduct("Widget", -5.0, weight_kg=1.0)

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError, match="Weight must be positive"):
            PhysicalProduct("Widget", 10.0, weight_kg=-1.0)

    def test_zero_weight_rejected(self):
        with pytest.raises(ValueError, match="Weight must be positive"):
            PhysicalProduct("Widget", 10.0, weight_kg=0)

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            PhysicalProduct("", 10.0, weight_kg=1.0)

    def test_whitespace_name_rejected(self):
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            PhysicalProduct("   ", 10.0, weight_kg=1.0)

    def test_negative_stock_rejected(self):
        with pytest.raises(ValueError, match="Stock cannot be negative"):
            PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=-1)

    def test_price_setter(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        p.price = 20.0
        assert p.price == 20.0

    def test_price_setter_negative(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        with pytest.raises(InvalidPriceError):
            p.price = -5.0

    def test_activate_deactivate(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        assert p.is_active is True
        p.deactivate()
        assert p.is_active is False
        p.activate()
        assert p.is_active is True

    def test_category_assignment(self):
        cat = _make_category()
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, category=cat)
        assert p.category is cat
        assert p in cat.products

    def test_repr(self):
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0, stock=5)
        r = repr(p)
        assert "PhysicalProduct" in r
        assert "Widget" in r
        assert "10.0" in r
        assert "5" in r


# ===========================================================================
# 2. DigitalProduct
# ===========================================================================

class TestDigitalProduct:

    def test_creation(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        assert dp.name == "EBook"
        assert dp.price == 4.99

    def test_requires_shipping(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        assert dp.requires_shipping() is False

    def test_product_type(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        assert dp.product_type() == ProductType.DIGITAL

    def test_stock_always_zero(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        assert dp.stock == 0

    def test_increase_stock_noop(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        dp.increase_stock(10)
        assert dp.stock == 0

    def test_decrease_stock_noop(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        dp.decrease_stock(5)
        assert dp.stock == 0

    def test_calculate_price(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        assert dp.calculate_price(3) == 14.97

    def test_file_url_property(self):
        url = "https://example.com/ebook.pdf"
        dp = DigitalProduct("EBook", 4.99, url, 2.5)
        assert dp.file_url == url

    def test_file_size_property(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        assert dp.file_size_mb == 2.5

    def test_repr(self):
        dp = DigitalProduct("EBook", 4.99, "https://example.com/ebook.pdf", 2.5)
        r = repr(dp)
        assert "DigitalProduct" in r
        assert "EBook" in r


# ===========================================================================
# 3. SubscriptionProduct
# ===========================================================================

class TestSubscriptionProduct:

    def test_creation(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=12)
        assert sp.name == "Netflix"
        assert sp.price == 15.99
        assert sp.duration_months == 12

    def test_requires_shipping(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=12)
        assert sp.requires_shipping() is False

    def test_product_type(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=12)
        assert sp.product_type() == ProductType.SUBSCRIPTION

    def test_calculate_price(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=6)
        # monthly_price * duration * quantity
        assert sp.calculate_price(1) == 15.99 * 6
        assert sp.calculate_price(2) == 15.99 * 6 * 2

    def test_calculate_price_rounding(self):
        sp = SubscriptionProduct("Spotify", 9.99, duration_months=3)
        assert sp.calculate_price(1) == round(9.99 * 3, 2)

    def test_invalid_quantity(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=12)
        with pytest.raises(InvalidQuantityError):
            sp.calculate_price(0)
        with pytest.raises(InvalidQuantityError):
            sp.calculate_price(-1)

    def test_invalid_duration_zero(self):
        with pytest.raises(ValueError, match="Duration must be at least 1 month"):
            SubscriptionProduct("Netflix", 15.99, duration_months=0)

    def test_invalid_duration_negative(self):
        with pytest.raises(ValueError, match="Duration must be at least 1 month"):
            SubscriptionProduct("Netflix", 15.99, duration_months=-3)

    def test_get_end_date_explicit(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=6)
        start = datetime(2025, 1, 1)
        end = sp.get_end_date(start)
        assert end == start + timedelta(days=6 * 30)

    def test_get_end_date_default(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=1)
        end = sp.get_end_date()
        expected = datetime.now() + timedelta(days=30)
        assert abs((end - expected).total_seconds()) < 1

    def test_stock_noops(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=12)
        assert sp.stock == 0
        sp.increase_stock(10)
        assert sp.stock == 0
        sp.decrease_stock(5)
        assert sp.stock == 0

    def test_repr(self):
        sp = SubscriptionProduct("Netflix", 15.99, duration_months=12)
        r = repr(sp)
        assert "SubscriptionProduct" in r
        assert "Netflix" in r


# ===========================================================================
# 4. Category
# ===========================================================================

class TestCategory:

    def test_creation(self):
        cat = Category("Electronics", "Gadgets and devices")
        assert cat.name == "Electronics"
        assert cat.description == "Gadgets and devices"
        assert cat.products == []

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            Category("")

    def test_whitespace_name_rejected(self):
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            Category("   ")

    def test_add_product(self):
        cat = _make_category()
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        cat.add_product(p)
        assert p in cat.products

    def test_add_product_no_duplicates(self):
        cat = _make_category()
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        cat.add_product(p)
        cat.add_product(p)
        assert len(cat.products) == 1

    def test_remove_product(self):
        cat = _make_category()
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        cat.add_product(p)
        cat.remove_product(p)
        assert p not in cat.products

    def test_remove_nonexistent_product_noop(self):
        cat = _make_category()
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        cat.remove_product(p)
        assert cat.products == []

    def test_products_returns_list_copy(self):
        cat = _make_category()
        p = PhysicalProduct("Widget", 10.0, weight_kg=1.0)
        cat.add_product(p)
        prods = cat.products
        prods.clear()
        assert len(cat.products) == 1

    def test_repr(self):
        cat = _make_category("Books")
        p = PhysicalProduct("Book", 10.0, weight_kg=1.0, category=cat)
        r = repr(cat)
        assert "Category" in r
        assert "Books" in r
        assert "1" in r


# ===========================================================================
# 5. Abstract Product cannot be instantiated
# ===========================================================================

class TestAbstractProduct:

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            Product("Widget", 10.0)

    def test_cannot_instantiate_with_abstract_methods_missing(self):
        class IncompleteProduct(Product):
            pass

        with pytest.raises(TypeError):
            IncompleteProduct("Widget", 10.0)
