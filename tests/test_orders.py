"""Tests for Order, OrderItem, and the full order lifecycle."""

import pytest

from ecommerce.orders import Order, OrderItem
from ecommerce.products import DigitalProduct, PhysicalProduct
from ecommerce.users import (
    BusinessCustomer,
    PremiumCustomer,
    RegularCustomer,
)
from ecommerce.delivery import ExpressDelivery, StandardDelivery
from ecommerce.payments import CreditCard, DigitalWallet
from ecommerce.discounts import PercentageDiscount
from ecommerce.enums import OrderStatus
from ecommerce.exceptions import (
    EmptyOrderError,
    InsufficientStockError,
    InvalidOrderStateError,
    InvalidQuantityError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def physical_product():
    return PhysicalProduct("Laptop", 100.0, 2.0, stock=10)


@pytest.fixture
def digital_product():
    return DigitalProduct("Ebook", 9.99, "http://example.com", 5.0)


@pytest.fixture
def regular_customer():
    return RegularCustomer("Alice", "alice@test.com")


@pytest.fixture
def premium_customer():
    return PremiumCustomer("Bob", "bob@test.com")


@pytest.fixture
def business_customer():
    return BusinessCustomer("Carol", "carol@test.com", company="Acme")


@pytest.fixture
def standard_delivery():
    return StandardDelivery()


@pytest.fixture
def express_delivery():
    return ExpressDelivery()


@pytest.fixture
def credit_card():
    return CreditCard("4111111111111111", "Test", "12/27")


@pytest.fixture
def wallet():
    return DigitalWallet("W1", "Test", 1000.0)


# ---------------------------------------------------------------------------
# 1. OrderItem
# ---------------------------------------------------------------------------

class TestOrderItem:
    def test_creation(self, physical_product):
        item = OrderItem(physical_product, 2)
        assert item.quantity == 2
        assert item.product is physical_product

    def test_product_property(self, physical_product):
        item = OrderItem(physical_product, 1)
        assert item.product.name == "Laptop"

    def test_quantity_property(self, physical_product):
        item = OrderItem(physical_product, 5)
        assert item.quantity == 5

    def test_unit_price_property(self, physical_product):
        item = OrderItem(physical_product, 3)
        assert item.unit_price == 100.0

    def test_subtotal_property(self, physical_product):
        item = OrderItem(physical_product, 4)
        assert item.subtotal == 400.0

    def test_invalid_quantity_raises(self, physical_product):
        with pytest.raises(InvalidQuantityError):
            OrderItem(physical_product, 0)
        with pytest.raises(InvalidQuantityError):
            OrderItem(physical_product, -1)


# ---------------------------------------------------------------------------
# 2. Order creation
# ---------------------------------------------------------------------------

class TestOrderCreation:
    def test_customer_property(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        assert order.customer is regular_customer

    def test_delivery_property(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        assert order.delivery_method is standard_delivery

    def test_status_is_created(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        assert order.status == OrderStatus.CREATED

    def test_total_is_zero(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        assert order.total == 0.0

    def test_items_starts_empty(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        assert order.items == []


# ---------------------------------------------------------------------------
# 3. add_item
# ---------------------------------------------------------------------------

class TestAddItem:
    def test_adds_item(self, regular_customer, standard_delivery, physical_product):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        assert len(order.items) == 1
        assert order.items[0].product is physical_product
        assert order.items[0].quantity == 1

    def test_add_same_product_increases_quantity(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 2)
        order.add_item(physical_product, 3)
        assert len(order.items) == 1
        assert order.items[0].quantity == 5

    def test_add_different_products(
        self, regular_customer, standard_delivery, physical_product, digital_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.add_item(digital_product, 1)
        assert len(order.items) == 2

    def test_add_inactive_product_raises(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        product = PhysicalProduct("Inactive", 10.0, 1.0, stock=5)
        product.deactivate()
        with pytest.raises(ValueError, match="not active"):
            order.add_item(product, 1)

    def test_add_physical_beyond_stock_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        with pytest.raises(InsufficientStockError):
            order.add_item(physical_product, 20)

    def test_add_item_when_not_created_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        with pytest.raises(InvalidOrderStateError):
            order.add_item(physical_product, 1)

    def test_invalid_quantity_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        with pytest.raises(InvalidQuantityError):
            order.add_item(physical_product, 0)


# ---------------------------------------------------------------------------
# 4. remove_item
# ---------------------------------------------------------------------------

class TestRemoveItem:
    def test_removes_item(self, regular_customer, standard_delivery, physical_product):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.remove_item(physical_product.product_id)
        assert len(order.items) == 0

    def test_not_found_raises(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        with pytest.raises(KeyError):
            order.remove_item("nonexistent")

    def test_remove_when_not_created_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        with pytest.raises(InvalidOrderStateError):
            order.remove_item(physical_product.product_id)


# ---------------------------------------------------------------------------
# 5. Full lifecycle — physical order
# ---------------------------------------------------------------------------

class TestPhysicalOrderLifecycle:
    def test_full_lifecycle(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 2)
        assert order.status == OrderStatus.CREATED

        initial_stock = physical_product.stock

        order.confirm()
        assert order.status == OrderStatus.CONFIRMED
        assert physical_product.stock == initial_stock - 2

        order.set_payment(credit_card)
        assert order.payment_method is credit_card

        order.pay()
        assert order.status == OrderStatus.PAID
        assert credit_card.status.value == "COMPLETED"

        order.process()
        assert order.status == OrderStatus.PROCESSING

        order.ship()
        assert order.status == OrderStatus.SHIPPED

        order.deliver()
        assert order.status == OrderStatus.DELIVERED


# ---------------------------------------------------------------------------
# 6. Full lifecycle — digital order
# ---------------------------------------------------------------------------

class TestDigitalOrderLifecycle:
    def test_digital_ship_auto_delivers(
        self, regular_customer, standard_delivery, digital_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(digital_product, 1)

        order.confirm()
        assert order.status == OrderStatus.CONFIRMED

        order.set_payment(credit_card)
        order.pay()
        assert order.status == OrderStatus.PAID

        order.process()
        assert order.status == OrderStatus.PROCESSING

        assert not order.has_physical_items
        assert order.shipping_cost == 0.0


# ---------------------------------------------------------------------------
# 7. Cancel lifecycle
# ---------------------------------------------------------------------------

class TestCancelLifecycle:
    def test_cancel_created(self, regular_customer, standard_delivery, physical_product):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_confirmed_restores_stock(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 3)
        order.confirm()
        assert physical_product.stock == 7

        order.cancel()
        assert order.status == OrderStatus.CANCELLED
        assert physical_product.stock == 10

    def test_cancel_paid_restores_stock(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 2)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        assert physical_product.stock == 8

        order.cancel()
        assert physical_product.stock == 10

    def test_cancel_processing_restores_stock(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 4)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        order.process()
        assert physical_product.stock == 6

        order.cancel()
        assert physical_product.stock == 10

    def test_cancel_shipped_raises(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        order.process()
        order.ship()
        with pytest.raises(InvalidOrderStateError):
            order.cancel()

    def test_cancel_delivered_raises(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        order.process()
        order.ship()
        order.deliver()
        with pytest.raises(InvalidOrderStateError):
            order.cancel()


# ---------------------------------------------------------------------------
# 8. Refund
# ---------------------------------------------------------------------------

class TestRefund:
    def test_refund_delivered(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        order.process()
        order.ship()
        order.deliver()

        order.refund()
        assert order.status == OrderStatus.REFUNDED
        assert credit_card.status.value == "REFUNDED"

    def test_refund_non_delivered_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        with pytest.raises(InvalidOrderStateError):
            order.refund()


# ---------------------------------------------------------------------------
# 9. calculate_total
# ---------------------------------------------------------------------------

class TestCalculateTotal:
    def test_total_formula(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 2)

        subtotal = 200.0
        raw_shipping = StandardDelivery.BASE_COST + (4.0 * StandardDelivery.COST_PER_KG)
        shipping = regular_customer.get_shipping_surcharge(raw_shipping)
        tax = round(subtotal * 0.08, 2)
        customer_discount = regular_customer.calculate_discount(subtotal)

        expected = round(subtotal + shipping + tax - customer_discount, 2)
        assert order.calculate_total() == expected


# ---------------------------------------------------------------------------
# 10. Empty order confirm
# ---------------------------------------------------------------------------

class TestEmptyOrderConfirm:
    def test_confirm_empty_raises(self, regular_customer, standard_delivery):
        order = Order(regular_customer, standard_delivery)
        with pytest.raises(EmptyOrderError):
            order.confirm()


# ---------------------------------------------------------------------------
# 11. Invalid transitions
# ---------------------------------------------------------------------------

class TestInvalidTransitions:
    def test_shipped_to_paid(self, regular_customer, standard_delivery, physical_product, credit_card):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        order.process()
        order.ship()
        with pytest.raises(InvalidOrderStateError):
            order.pay()

    def test_delivered_to_confirm(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        order.process()
        order.ship()
        order.deliver()
        with pytest.raises(InvalidOrderStateError):
            order.confirm()

    def test_cancelled_to_anything(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.cancel()
        with pytest.raises(InvalidOrderStateError):
            order.confirm()
        with pytest.raises(InvalidOrderStateError):
            order.set_payment(credit_card)
        with pytest.raises(InvalidOrderStateError):
            order.pay()
        with pytest.raises(InvalidOrderStateError):
            order.process()
        with pytest.raises(InvalidOrderStateError):
            order.ship()
        with pytest.raises(InvalidOrderStateError):
            order.deliver()


# ---------------------------------------------------------------------------
# 12. set_payment
# ---------------------------------------------------------------------------

class TestSetPayment:
    def test_set_payment_must_be_confirmed(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        with pytest.raises(InvalidOrderStateError):
            order.set_payment(credit_card)

    def test_set_payment_works_in_confirmed(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        assert order.payment_method is credit_card


# ---------------------------------------------------------------------------
# 13. pay
# ---------------------------------------------------------------------------

class TestPay:
    def test_pay_without_payment_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        with pytest.raises(ValueError, match="No payment method"):
            order.pay()

    def test_pay_not_confirmed_raises(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        with pytest.raises(InvalidOrderStateError):
            order.pay()


# ---------------------------------------------------------------------------
# 14. Digital products — shipping cost is 0
# ---------------------------------------------------------------------------

class TestDigitalShippingCost:
    def test_no_shipping_for_digital(
        self, regular_customer, standard_delivery, digital_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(digital_product, 1)
        assert order.shipping_cost == 0.0


# ---------------------------------------------------------------------------
# 15. Customer discount polymorphism
# ---------------------------------------------------------------------------

class TestCustomerDiscountPolymorphism:
    def test_regular_discount(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        assert order.customer_discount == round(100.0 * 0.05, 2)

    def test_premium_discount(
        self, premium_customer, standard_delivery, physical_product
    ):
        order = Order(premium_customer, standard_delivery)
        order.add_item(physical_product, 1)
        assert order.customer_discount == round(100.0 * 0.10, 2)

    def test_business_discount(
        self, business_customer, standard_delivery, physical_product
    ):
        order = Order(business_customer, standard_delivery)
        order.add_item(physical_product, 1)
        assert order.customer_discount == round(100.0 * 0.15, 2)

    def test_different_discounts_produce_different_totals(
        self, standard_delivery, physical_product
    ):
        customers = [
            RegularCustomer("A", "a@test.com"),
            PremiumCustomer("B", "b@test.com"),
            BusinessCustomer("C", "c@test.com"),
        ]
        totals = []
        for cust in customers:
            order = Order(cust, standard_delivery)
            order.add_item(physical_product, 1)
            totals.append(order.calculate_total())
        assert totals[0] != totals[1] != totals[2]
        assert totals[0] > totals[1] > totals[2]


# ---------------------------------------------------------------------------
# 16. Promotional discount
# ---------------------------------------------------------------------------

class TestPromotionalDiscount:
    def test_percentage_discount_applied(
        self, regular_customer, standard_delivery, physical_product
    ):
        promo = PercentageDiscount("Spring Sale", "SPRING20", 20)
        order = Order(regular_customer, standard_delivery, promotional_discount=promo)
        order.add_item(physical_product, 1)

        subtotal = 100.0
        promo_amount = round(subtotal * 0.20, 2)
        assert order.promo_discount_amount == promo_amount


# ---------------------------------------------------------------------------
# 17. Additional charges
# ---------------------------------------------------------------------------

class TestAdditionalCharges:
    def test_add_charge_in_created(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.add_additional_charge(15.0, "Gift wrapping")
        assert order.additional_charges == 15.0

    def test_add_charge_in_confirmed(
        self, regular_customer, standard_delivery, physical_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.add_additional_charge(10.0, "Insurance")
        assert order.additional_charges == 10.0

    def test_add_charge_in_paid_raises(
        self, regular_customer, standard_delivery, physical_product, credit_card
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.confirm()
        order.set_payment(credit_card)
        order.pay()
        with pytest.raises(InvalidOrderStateError):
            order.add_additional_charge(5.0)


# ---------------------------------------------------------------------------
# 18. has_physical_items
# ---------------------------------------------------------------------------

class TestHasPhysicalItems:
    def test_physical_order(self, regular_customer, standard_delivery, physical_product):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        assert order.has_physical_items is True

    def test_digital_order(self, regular_customer, standard_delivery, digital_product):
        order = Order(regular_customer, standard_delivery)
        order.add_item(digital_product, 1)
        assert order.has_physical_items is False

    def test_mixed_order(
        self, regular_customer, standard_delivery, physical_product, digital_product
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(digital_product, 1)
        assert order.has_physical_items is False
        order.add_item(physical_product, 1)
        assert order.has_physical_items is True


# ---------------------------------------------------------------------------
# 19. Mixed physical and digital products
# ---------------------------------------------------------------------------

class TestMixedOrder:
    def test_mixed_products_lifecycle(
        self,
        regular_customer,
        standard_delivery,
        physical_product,
        digital_product,
        credit_card,
    ):
        order = Order(regular_customer, standard_delivery)
        order.add_item(physical_product, 1)
        order.add_item(digital_product, 2)

        assert order.has_physical_items is True
        assert len(order.items) == 2
        subtotal = 100.0 + 9.99 * 2
        assert order.subtotal == round(subtotal, 2)

        initial_stock = physical_product.stock
        order.confirm()
        assert physical_product.stock == initial_stock - 1

        order.set_payment(credit_card)
        order.pay()
        order.process()

        order.ship()
        assert order.status == OrderStatus.SHIPPED

        order.deliver()
        assert order.status == OrderStatus.DELIVERED
