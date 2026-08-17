import pytest
from ecommerce.cart import ShoppingCart, CartItem
from ecommerce.products import PhysicalProduct, DigitalProduct
from ecommerce.categories import Category
from ecommerce.exceptions import InvalidQuantityError


def make_category(name="General"):
    return Category(name=name, description=f"{name} products")


def make_physical_product(name="Widget", price=10.0, stock=100):
    return PhysicalProduct(
        name=name,
        description=f"A {name}",
        price=price,
        category=make_category(),
        weight_kg=1.0,
        stock=stock,
    )


def make_digital_product(name="Ebook", price=5.0):
    return DigitalProduct(
        name=name,
        description=f"Digital {name}",
        price=price,
        category=make_category(),
        file_size_mb=10,
        file_url="https://example.com/download",
    )


class TestCartItemCreation:
    def test_create_cart_item(self):
        product = make_physical_product()
        item = CartItem(product=product, quantity=2)
        assert item.product is product
        assert item.quantity == 2

    def test_create_cart_item_default_quantity(self):
        product = make_physical_product()
        item = CartItem(product=product)
        assert item.quantity == 1


class TestCartItemProperties:
    def test_product_property(self):
        product = make_digital_product()
        item = CartItem(product=product, quantity=3)
        assert item.product is product

    def test_quantity_property(self):
        product = make_physical_product()
        item = CartItem(product=product, quantity=5)
        assert item.quantity == 5


class TestCartItemSetQuantity:
    def test_set_quantity_valid(self):
        product = make_physical_product()
        item = CartItem(product=product, quantity=1)
        item.set_quantity(10)
        assert item.quantity == 10

    def test_set_quantity_rejects_zero(self):
        product = make_physical_product()
        item = CartItem(product=product, quantity=1)
        with pytest.raises(InvalidQuantityError):
            item.set_quantity(0)

    def test_set_quantity_rejects_negative(self):
        product = make_physical_product()
        item = CartItem(product=product, quantity=1)
        with pytest.raises(InvalidQuantityError):
            item.set_quantity(-5)


class TestCartItemGetSubtotal:
    def test_get_subtotal_delegates_to_product(self):
        product = make_physical_product(price=25.0)
        item = CartItem(product=product, quantity=3)
        assert item.get_subtotal() == 75.0

    def test_get_subtotal_single_quantity(self):
        product = make_digital_product(price=9.99)
        item = CartItem(product=product, quantity=1)
        assert item.get_subtotal() == product.calculate_price(1)


class TestCartItemRepr:
    def test_repr(self):
        product = make_physical_product(name="Gadget", price=15.0)
        item = CartItem(product=product, quantity=4)
        result = repr(item)
        assert "Gadget" in result
        assert "4" in result


class TestShoppingCartCreation:
    def test_create_empty_cart(self):
        cart = ShoppingCart()
        assert cart.is_empty is True
        assert cart.item_count == 0
        assert cart.total_quantity == 0

    def test_is_empty_true(self):
        cart = ShoppingCart()
        assert cart.is_empty is True

    def test_is_empty_false_after_add(self):
        cart = ShoppingCart()
        cart.add_item(make_physical_product(), quantity=1)
        assert cart.is_empty is False

    def test_item_count(self):
        cart = ShoppingCart()
        cart.add_item(make_physical_product(name="A"), quantity=1)
        cart.add_item(make_digital_product(name="B"), quantity=1)
        assert cart.item_count == 2

    def test_total_quantity(self):
        cart = ShoppingCart()
        cart.add_item(make_physical_product(name="A"), quantity=3)
        cart.add_item(make_digital_product(name="B"), quantity=2)
        assert cart.total_quantity == 5


class TestShoppingCartAddItem:
    def test_add_single_item(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=2)
        assert cart.item_count == 1
        assert cart.total_quantity == 2

    def test_add_same_product_increases_quantity(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=2)
        cart.add_item(product, quantity=3)
        assert cart.item_count == 1
        assert cart.total_quantity == 5

    def test_add_different_products(self):
        cart = ShoppingCart()
        p1 = make_physical_product(name="A")
        p2 = make_digital_product(name="B")
        cart.add_item(p1, quantity=1)
        cart.add_item(p2, quantity=1)
        assert cart.item_count == 2
        assert cart.total_quantity == 2


class TestShoppingCartRemoveItem:
    def test_remove_item(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=2)
        cart.remove_item(product.product_id)
        assert cart.is_empty is True

    def test_remove_item_not_found_raises(self):
        cart = ShoppingCart()
        with pytest.raises(KeyError):
            cart.remove_item("nonexistent-id")


class TestShoppingCartUpdateQuantity:
    def test_update_quantity(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=1)
        cart.update_quantity(product.product_id, 5)
        assert cart.total_quantity == 5

    def test_update_quantity_not_found_raises(self):
        cart = ShoppingCart()
        with pytest.raises(KeyError):
            cart.update_quantity("nonexistent-id", 5)

    def test_update_quantity_invalid_raises(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=1)
        with pytest.raises(InvalidQuantityError):
            cart.update_quantity(product.product_id, 0)


class TestShoppingCartGetItem:
    def test_get_item(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=3)
        item = cart.get_item(product.product_id)
        assert item is not None
        assert item.quantity == 3
        assert item.product is product

    def test_get_item_not_found(self):
        cart = ShoppingCart()
        assert cart.get_item("nonexistent-id") is None


class TestShoppingCartSubtotal:
    def test_get_subtotal_empty_cart(self):
        cart = ShoppingCart()
        assert cart.get_subtotal() == 0

    def test_get_subtotal_single_item(self):
        cart = ShoppingCart()
        product = make_physical_product(price=20.0)
        cart.add_item(product, quantity=2)
        assert cart.get_subtotal() == 40.0

    def test_get_subtotal_multiple_items(self):
        cart = ShoppingCart()
        p1 = make_physical_product(name="A", price=10.0)
        p2 = make_digital_product(name="B", price=5.0)
        cart.add_item(p1, quantity=2)
        cart.add_item(p2, quantity=3)
        expected = p1.calculate_price(2) + p2.calculate_price(3)
        assert cart.get_subtotal() == expected


class TestShoppingCartFilterItems:
    def test_get_physical_items(self):
        cart = ShoppingCart()
        physical = make_physical_product(name="P")
        digital = make_digital_product(name="D")
        cart.add_item(physical, quantity=1)
        cart.add_item(digital, quantity=1)
        physical_items = cart.get_physical_items()
        assert len(physical_items) == 1
        assert physical_items[0].product is physical

    def test_get_digital_items(self):
        cart = ShoppingCart()
        physical = make_physical_product(name="P")
        digital = make_digital_product(name="D")
        cart.add_item(physical, quantity=1)
        cart.add_item(digital, quantity=1)
        digital_items = cart.get_digital_items()
        assert len(digital_items) == 1
        assert digital_items[0].product is digital

    def test_get_physical_items_empty(self):
        cart = ShoppingCart()
        assert cart.get_physical_items() == []

    def test_get_digital_items_empty(self):
        cart = ShoppingCart()
        assert cart.get_digital_items() == []


class TestShoppingCartClear:
    def test_clear(self):
        cart = ShoppingCart()
        cart.add_item(make_physical_product(name="A"), quantity=2)
        cart.add_item(make_digital_product(name="B"), quantity=3)
        cart.clear()
        assert cart.is_empty is True
        assert cart.item_count == 0
        assert cart.total_quantity == 0


class TestShoppingCartItemsProperty:
    def test_items_returns_list_copy(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=1)
        items = cart.items
        items.clear()
        assert cart.item_count == 1


class TestShoppingCartRepr:
    def test_repr(self):
        cart = ShoppingCart()
        result = repr(cart)
        assert "ShoppingCart" in result or "cart" in result.lower()


class TestCartPolymorphism:
    def test_mix_physical_and_digital_separated(self):
        cart = ShoppingCart()
        p1 = make_physical_product(name="Laptop", price=999.0)
        p2 = make_digital_product(name="Software", price=49.99)
        p3 = make_physical_product(name="Mouse", price=25.0)
        p4 = make_digital_product(name="Music", price=9.99)

        cart.add_item(p1, quantity=1)
        cart.add_item(p2, quantity=2)
        cart.add_item(p3, quantity=1)
        cart.add_item(p4, quantity=1)

        physical = cart.get_physical_items()
        digital = cart.get_digital_items()

        assert len(physical) == 2
        assert len(digital) == 2
        physical_names = {item.product.name for item in physical}
        digital_names = {item.product.name for item in digital}
        assert physical_names == {"Laptop", "Mouse"}
        assert digital_names == {"Software", "Music"}

    def test_total_quantity_with_mixed_items(self):
        cart = ShoppingCart()
        cart.add_item(make_physical_product(name="A"), quantity=2)
        cart.add_item(make_digital_product(name="B"), quantity=3)
        cart.add_item(make_physical_product(name="C"), quantity=1)
        assert cart.item_count == 3
        assert cart.total_quantity == 6

    def test_subtotal_with_mixed_items(self):
        cart = ShoppingCart()
        p_phys = make_physical_product(name="P", price=20.0)
        p_digi = make_digital_product(name="D", price=10.0)
        cart.add_item(p_phys, quantity=2)
        cart.add_item(p_digi, quantity=3)
        expected = p_phys.calculate_price(2) + p_digi.calculate_price(3)
        assert cart.get_subtotal() == expected


class TestCartEdgeCases:
    def test_add_then_remove_leaves_cart_empty(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=5)
        assert cart.is_empty is False
        cart.remove_item(product.product_id)
        assert cart.is_empty is True
        assert cart.item_count == 0
        assert cart.total_quantity == 0
        assert cart.get_subtotal() == 0

    def test_remove_one_of_many_products(self):
        cart = ShoppingCart()
        p1 = make_physical_product(name="A")
        p2 = make_digital_product(name="B")
        cart.add_item(p1, quantity=1)
        cart.add_item(p2, quantity=1)
        cart.remove_item(p1.product_id)
        assert cart.item_count == 1
        assert cart.get_item(p2.product_id) is not None

    def test_update_quantity_to_one(self):
        cart = ShoppingCart()
        product = make_physical_product()
        cart.add_item(product, quantity=10)
        cart.update_quantity(product.product_id, 1)
        assert cart.total_quantity == 1

    def test_get_subtotal_after_clear(self):
        cart = ShoppingCart()
        p = make_physical_product(price=100.0)
        cart.add_item(p, quantity=5)
        cart.clear()
        assert cart.get_subtotal() == 0
