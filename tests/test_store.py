import pytest
from ecommerce.store import Store
from ecommerce.products import PhysicalProduct, DigitalProduct, SubscriptionProduct
from ecommerce.categories import Category
from ecommerce.exceptions import ProductNotFoundError


def make_store(name="Test Store"):
    return Store(name=name)


def make_physical_product(name="Widget", price=10.0, stock=100, description="A widget", category=None):
    return PhysicalProduct(
        name=name, price=price, description=description,
        stock=stock, weight_kg=1.0, category=category,
    )


def make_digital_product(name="Ebook", price=5.0, description="Digital ebook"):
    return DigitalProduct(
        name=name, price=price, description=description,
        file_url="https://example.com/file", file_size_mb=10,
    )


def make_subscription_product(name="Premium", price=9.99, description="Premium plan", months=12):
    return SubscriptionProduct(
        name=name, monthly_price=price, description=description,
        duration_months=months,
    )


# ── Store Creation ─────────────────────────────────────────────


class TestStoreCreation:
    def test_create_store(self):
        store = make_store("My Store")
        assert store.name == "My Store"

    def test_strips_whitespace_from_name(self):
        store = make_store("  Padded  ")
        assert store.name == "Padded"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            Store(name="")

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValueError):
            Store(name="   ")


class TestStoreNameProperty:
    def test_name_property(self):
        store = make_store("Acme")
        assert store.name == "Acme"


# ── Add Product ────────────────────────────────────────────────


class TestAddProduct:
    def test_add_product(self):
        store = make_store()
        product = make_physical_product()
        store.add_product(product)
        assert store.product_count == 1

    def test_products_property_returns_list(self):
        store = make_store()
        product = make_physical_product()
        store.add_product(product)
        products = store.products
        assert isinstance(products, list)
        assert len(products) == 1

    def test_products_property_returns_copy(self):
        store = make_store()
        store.add_product(make_physical_product())
        products = store.products
        products.clear()
        assert store.product_count == 1

    def test_product_count(self):
        store = make_store()
        assert store.product_count == 0
        store.add_product(make_physical_product(name="A"))
        assert store.product_count == 1
        store.add_product(make_digital_product(name="B"))
        assert store.product_count == 2


class TestAddDuplicateProduct:
    def test_add_duplicate_is_idempotent(self):
        store = make_store()
        product = make_physical_product()
        store.add_product(product)
        store.add_product(product)
        assert store.product_count == 1

    def test_add_duplicate_does_not_raise(self):
        store = make_store()
        product = make_physical_product()
        store.add_product(product)
        store.add_product(product)
        assert store.product_count == 1


# ── Get Product ────────────────────────────────────────────────


class TestGetProduct:
    def test_get_product_by_id(self):
        store = make_store()
        product = make_physical_product()
        store.add_product(product)
        result = store.get_product(product.product_id)
        assert result is product

    def test_get_non_existent_product_raises(self):
        store = make_store()
        with pytest.raises(ProductNotFoundError):
            store.get_product("nonexistent-id")


# ── Remove Product ─────────────────────────────────────────────


class TestRemoveProduct:
    def test_remove_product(self):
        store = make_store()
        product = make_physical_product()
        store.add_product(product)
        removed = store.remove_product(product.product_id)
        assert removed is product
        assert store.product_count == 0

    def test_remove_non_existent_product_raises(self):
        store = make_store()
        with pytest.raises(ProductNotFoundError):
            store.remove_product("nonexistent-id")


# ── Search Products ────────────────────────────────────────────


class TestSearchProducts:
    def test_search_by_name(self):
        store = make_store()
        p1 = make_physical_product(name="Red Widget", description="A red widget")
        p2 = make_physical_product(name="Blue Gadget", description="A blue gadget")
        store.add_product(p1)
        store.add_product(p2)
        results = store.search_products("Widget")
        assert len(results) == 1
        assert results[0] is p1

    def test_search_case_insensitive(self):
        store = make_store()
        product = make_physical_product(name="WIDGET")
        store.add_product(product)
        results = store.search_products("widget")
        assert len(results) == 1
        assert results[0] is product

    def test_search_by_description(self):
        store = make_store()
        product = make_physical_product(name="Item", description="A rare collectible")
        store.add_product(product)
        results = store.search_products("collectible")
        assert len(results) == 1
        assert results[0] is product

    def test_search_no_results(self):
        store = make_store()
        store.add_product(make_physical_product(name="Widget"))
        results = store.search_products("Nonexistent")
        assert results == []


# ── Active / In-Stock Products ─────────────────────────────────


class TestGetActiveProducts:
    def test_get_active_products(self):
        store = make_store()
        p1 = make_physical_product(name="Active")
        p2 = make_physical_product(name="Inactive")
        store.add_product(p1)
        store.add_product(p2)
        p2.deactivate()
        active = store.get_active_products()
        assert len(active) == 1
        assert active[0] is p1

    def test_all_active(self):
        store = make_store()
        p1 = make_physical_product(name="A")
        p2 = make_digital_product(name="B")
        store.add_product(p1)
        store.add_product(p2)
        assert len(store.get_active_products()) == 2


class TestGetInStockProducts:
    def test_physical_in_stock(self):
        store = make_store()
        product = make_physical_product(name="Widget", stock=5)
        store.add_product(product)
        results = store.get_in_stock_products()
        assert len(results) == 1

    def test_physical_out_of_stock_excluded(self):
        store = make_store()
        product = make_physical_product(name="Widget", stock=0)
        store.add_product(product)
        results = store.get_in_stock_products()
        assert results == []

    def test_digital_always_in_stock(self):
        store = make_store()
        product = make_digital_product(name="Ebook")
        store.add_product(product)
        results = store.get_in_stock_products()
        assert len(results) == 1

    def test_subscription_always_in_stock(self):
        store = make_store()
        product = make_subscription_product(name="Premium")
        store.add_product(product)
        results = store.get_in_stock_products()
        assert len(results) == 1

    def test_inactive_excluded(self):
        store = make_store()
        product = make_digital_product(name="Ebook")
        store.add_product(product)
        product.deactivate()
        results = store.get_in_stock_products()
        assert results == []


# ── Categories ─────────────────────────────────────────────────


class TestAddCategory:
    def test_add_category(self):
        store = make_store()
        cat = Category(name="Electronics")
        store.add_category(cat)
        assert len(store.categories) == 1

    def test_add_duplicate_category_is_idempotent(self):
        store = make_store()
        cat = Category(name="Electronics")
        store.add_category(cat)
        store.add_category(cat)
        assert len(store.categories) == 1

    def test_categories_property_returns_list(self):
        store = make_store()
        cat = Category(name="Books")
        store.add_category(cat)
        result = store.categories
        assert isinstance(result, list)
        assert len(result) == 1


class TestGetCategory:
    def test_get_category_by_name(self):
        store = make_store()
        cat = Category(name="Clothing")
        store.add_category(cat)
        result = store.get_category("Clothing")
        assert result is cat

    def test_get_non_existent_category_returns_none(self):
        store = make_store()
        result = store.get_category("Nonexistent")
        assert result is None


class TestRemoveCategory:
    def test_remove_category(self):
        store = make_store()
        cat = Category(name="Toys")
        store.add_category(cat)
        removed = store.remove_category("Toys")
        assert removed is cat
        assert len(store.categories) == 0

    def test_remove_non_existent_category_raises(self):
        store = make_store()
        with pytest.raises(KeyError):
            store.remove_category("Nonexistent")


# ── Products by Category ───────────────────────────────────────


class TestGetProductsByCategory:
    def test_get_products_by_category(self):
        store = make_store()
        cat = Category(name="Electronics")
        store.add_category(cat)
        p1 = make_physical_product(name="Phone", category=cat)
        p2 = make_physical_product(name="Tablet", category=cat)
        store.add_product(p1)
        store.add_product(p2)
        results = store.get_products_by_category("Electronics")
        assert len(results) == 2

    def test_non_existent_category_returns_empty(self):
        store = make_store()
        results = store.get_products_by_category("Nonexistent")
        assert results == []


# ── Repr ───────────────────────────────────────────────────────


class TestStoreRepr:
    def test_repr(self):
        store = make_store("MyStore")
        store.add_product(make_physical_product())
        store.add_product(make_digital_product())
        result = repr(store)
        assert "MyStore" in result
        assert "2" in result
