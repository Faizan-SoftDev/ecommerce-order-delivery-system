"""Tests for the User hierarchy."""

import pytest

from ecommerce.enums import CustomerType
from ecommerce.users import (
    Admin,
    BusinessCustomer,
    Customer,
    PremiumCustomer,
    RegularCustomer,
    User,
)


# ---------------------------------------------------------------------------
# RegularCustomer
# ---------------------------------------------------------------------------

class TestRegularCustomer:
    def test_creation(self):
        c = RegularCustomer("Alice", "alice@example.com", "123 Main St")
        assert c.name == "Alice"
        assert c.email == "alice@example.com"
        assert c.address == "123 Main St"
        assert c.balance == 0.0

    def test_customer_type(self):
        c = RegularCustomer("Bob", "bob@example.com")
        assert c.customer_type == CustomerType.REGULAR

    def test_calculate_discount(self):
        c = RegularCustomer("Alice", "alice@example.com")
        assert c.calculate_discount(200) == 10.00
        assert c.calculate_discount(0) == 0.0
        assert c.calculate_discount(50.50) == 2.53

    def test_get_shipping_surcharge(self):
        c = RegularCustomer("Alice", "alice@example.com")
        assert c.get_shipping_surcharge(15.00) == 15.00
        assert c.get_shipping_surcharge(0.0) == 0.0


# ---------------------------------------------------------------------------
# PremiumCustomer
# ---------------------------------------------------------------------------

class TestPremiumCustomer:
    def test_creation(self):
        c = PremiumCustomer("Charlie", "charlie@example.com", "456 Oak Ave")
        assert c.name == "Charlie"
        assert c.email == "charlie@example.com"
        assert c.address == "456 Oak Ave"
        assert c.balance == 0.0

    def test_customer_type(self):
        c = PremiumCustomer("Charlie", "charlie@example.com")
        assert c.customer_type == CustomerType.PREMIUM

    def test_calculate_discount(self):
        c = PremiumCustomer("Charlie", "charlie@example.com")
        assert c.calculate_discount(200) == 20.00
        assert c.calculate_discount(0) == 0.0
        assert c.calculate_discount(99.99) == 10.00

    def test_get_shipping_surcharge(self):
        c = PremiumCustomer("Charlie", "charlie@example.com")
        assert c.get_shipping_surcharge(15.00) == 0.0
        assert c.get_shipping_surcharge(0.0) == 0.0


# ---------------------------------------------------------------------------
# BusinessCustomer
# ---------------------------------------------------------------------------

class TestBusinessCustomer:
    def test_creation(self):
        c = BusinessCustomer(
            "Diana", "diana@corp.com", "789 Pine Rd", company="Acme Corp"
        )
        assert c.name == "Diana"
        assert c.email == "diana@corp.com"
        assert c.address == "789 Pine Rd"
        assert c.company == "Acme Corp"
        assert c.balance == 0.0

    def test_customer_type(self):
        c = BusinessCustomer("Diana", "diana@corp.com")
        assert c.customer_type == CustomerType.BUSINESS

    def test_company_property(self):
        c = BusinessCustomer("Diana", "diana@corp.com", company="Globex")
        assert c.company == "Globex"

    def test_company_default_empty(self):
        c = BusinessCustomer("Diana", "diana@corp.com")
        assert c.company == ""

    def test_calculate_discount(self):
        c = BusinessCustomer("Diana", "diana@corp.com")
        assert c.calculate_discount(200) == 30.00
        assert c.calculate_discount(0) == 0.0
        assert c.calculate_discount(33.33) == 5.00

    def test_get_shipping_surcharge(self):
        c = BusinessCustomer("Diana", "diana@corp.com")
        assert c.get_shipping_surcharge(15.00) == 0.0
        assert c.get_shipping_surcharge(0.0) == 0.0


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

class TestAdmin:
    def test_creation(self):
        a = Admin("Eve", "eve@example.com")
        assert a.name == "Eve"
        assert a.email == "eve@example.com"
        assert a.role == "admin"

    def test_role_property(self):
        a = Admin("Eve", "eve@example.com", role="superadmin")
        assert a.role == "superadmin"


# ---------------------------------------------------------------------------
# User base validations
# ---------------------------------------------------------------------------

class TestUserValidations:
    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            Admin("", "x@y.com")

    def test_whitespace_only_name_rejected(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            Admin("   ", "x@y.com")

    def test_invalid_email_no_at_rejected(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Admin("Valid", "notanemail")

    def test_empty_email_rejected(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Admin("Valid", "")


# ---------------------------------------------------------------------------
# Customer balance operations
# ---------------------------------------------------------------------------

class TestCustomerBalance:
    @pytest.fixture()
    def customer(self):
        return RegularCustomer("Frank", "frank@example.com")

    def test_add_balance(self, customer):
        customer.add_balance(100.00)
        assert customer.balance == 100.00
        customer.add_balance(50.50)
        assert customer.balance == 150.50

    def test_deduct_balance(self, customer):
        customer.add_balance(100.00)
        customer.deduct_balance(30.00)
        assert customer.balance == 70.00

    def test_deduct_insufficient_raises(self, customer):
        customer.add_balance(10.00)
        with pytest.raises(ValueError, match="Insufficient balance"):
            customer.deduct_balance(20.00)

    def test_add_negative_raises(self, customer):
        with pytest.raises(ValueError, match="Deposit amount must be positive"):
            customer.add_balance(-10.00)

    def test_add_zero_raises(self, customer):
        with pytest.raises(ValueError, match="Deposit amount must be positive"):
            customer.add_balance(0)

    def test_deduct_negative_raises(self, customer):
        with pytest.raises(ValueError, match="Deduction amount must be positive"):
            customer.deduct_balance(-5.00)

    def test_deduct_zero_raises(self, customer):
        with pytest.raises(ValueError, match="Deduction amount must be positive"):
            customer.deduct_balance(0)


# ---------------------------------------------------------------------------
# Customer orders
# ---------------------------------------------------------------------------

class TestCustomerOrders:
    @pytest.fixture()
    def customer(self):
        return RegularCustomer("Grace", "grace@example.com")

    def test_add_order(self, customer):
        fake_order = object()
        customer.add_order(fake_order)
        assert len(customer.orders) == 1

    def test_add_order_no_duplicates(self, customer):
        fake_order = object()
        customer.add_order(fake_order)
        customer.add_order(fake_order)
        assert len(customer.orders) == 1

    def test_remove_order(self, customer):
        fake_order = object()
        customer.add_order(fake_order)
        customer.remove_order(fake_order)
        assert len(customer.orders) == 0

    def test_remove_nonexistent_order_no_error(self, customer):
        fake_order = object()
        customer.remove_order(fake_order)
        assert len(customer.orders) == 0

    def test_orders_returns_copy(self, customer):
        fake_order = object()
        customer.add_order(fake_order)
        orders_copy = customer.orders
        orders_copy.clear()
        assert len(customer.orders) == 1


# ---------------------------------------------------------------------------
# Polymorphism
# ---------------------------------------------------------------------------

class TestPolymorphism:
    def test_discount_varies_by_customer_type(self):
        customers = [
            RegularCustomer("R", "r@e.com"),
            PremiumCustomer("P", "p@e.com"),
            BusinessCustomer("B", "b@e.com"),
        ]
        subtotal = 1000.0
        discounts = [c.calculate_discount(subtotal) for c in customers]
        assert discounts == [50.0, 100.0, 150.0]

    def test_shipping_surcharge_varies_by_customer_type(self):
        customers = [
            RegularCustomer("R", "r@e.com"),
            PremiumCustomer("P", "p@e.com"),
            BusinessCustomer("B", "b@e.com"),
        ]
        base_cost = 25.0
        surcharges = [c.get_shipping_surcharge(base_cost) for c in customers]
        assert surcharges == [25.0, 0.0, 0.0]

    def test_iterate_and_call(self):
        customers = [
            RegularCustomer("R", "r@e.com"),
            PremiumCustomer("P", "p@e.com"),
            BusinessCustomer("B", "b@e.com"),
        ]
        expected_discounts = {50.0, 100.0, 150.0}
        expected_shipping = {25.0, 0.0}

        seen_discounts = set()
        seen_shipping = set()

        for c in customers:
            seen_discounts.add(c.calculate_discount(1000.0))
            seen_shipping.add(c.get_shipping_surcharge(25.0))

        assert seen_discounts == expected_discounts
        assert seen_shipping == expected_shipping
