import pytest
from datetime import datetime

from ecommerce.invoices import Invoice, Refund
from ecommerce.orders import Order
from ecommerce.products import PhysicalProduct
from ecommerce.users import RegularCustomer
from ecommerce.payments import CreditCard
from ecommerce.delivery import StandardDelivery
from ecommerce.enums import OrderStatus, RefundStatus
from ecommerce.exceptions import RefundError


def make_product(name="Widget", price=25.0, stock=50):
    return PhysicalProduct(
        name=name, price=price, weight_kg=1.0, stock=stock
    )


def make_customer(name="Alice", email="alice@example.com"):
    return RegularCustomer(name=name, email=email)


def make_payment():
    return CreditCard(
        card_number="4111111111111111",
        cardholder_name="Alice",
        expiry="12/28",
    )


def make_delivery():
    return StandardDelivery()


def make_delivered_order(
    customer=None,
    product1=None,
    product2=None,
    qty1=2,
    qty2=1,
):
    customer = customer or make_customer()
    product1 = product1 or make_product(name="Widget", price=25.0, stock=50)
    product2 = product2 or make_product(name="Gadget", price=50.0, stock=50)

    delivery = make_delivery()
    order = Order(customer=customer, delivery_method=delivery)
    order.add_item(product1, quantity=qty1)
    order.add_item(product2, quantity=qty2)
    order.confirm()

    payment = make_payment()
    order.set_payment(payment)
    order.pay()
    order.process()
    order.ship()
    order.deliver()

    return order


# ── Invoice Tests ────────────────────────────────────────────────


class TestInvoiceCreation:
    def test_create_invoice_from_order(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        assert invoice is not None

    def test_invoice_id_is_string(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        assert isinstance(invoice.invoice_id, str)
        assert len(invoice.invoice_id) == 8

    def test_order_id_matches_order(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        assert invoice.order_id == order.order_id

    def test_customer_name_matches_order(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        assert invoice.customer_name == order.customer.name


class TestInvoiceProperties:
    def test_total_matches_order(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        assert invoice.total == order.total

    def test_created_at_is_datetime(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        assert isinstance(invoice.created_at, datetime)

    def test_line_items_length(self):
        order = make_delivered_order(qty1=2, qty2=3)
        invoice = Invoice(order)
        assert len(invoice.line_items) == len(order.items)

    def test_line_items_contain_product_name(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        names = [item["product"] for item in invoice.line_items]
        assert "Widget" in names
        assert "Gadget" in names

    def test_line_items_contain_quantity(self):
        order = make_delivered_order(qty1=2, qty2=1)
        invoice = Invoice(order)
        quantities = {item["product"]: item["quantity"] for item in invoice.line_items}
        assert quantities["Widget"] == 2
        assert quantities["Gadget"] == 1

    def test_line_items_contain_unit_price(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        prices = {item["product"]: item["unit_price"] for item in invoice.line_items}
        assert prices["Widget"] == 25.0
        assert prices["Gadget"] == 50.0

    def test_line_items_contain_subtotal(self):
        order = make_delivered_order(qty1=2, qty2=1)
        invoice = Invoice(order)
        subtotals = {item["product"]: item["subtotal"] for item in invoice.line_items}
        assert subtotals["Widget"] == 50.0
        assert subtotals["Gadget"] == 50.0

    def test_line_items_returns_copy(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        items = invoice.line_items
        items.clear()
        assert len(invoice.line_items) == 2


class TestInvoiceGetSummary:
    def test_summary_contains_invoice_id(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert invoice.invoice_id in summary

    def test_summary_contains_order_id(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert order.order_id in summary

    def test_summary_contains_customer_name(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert "Alice" in summary

    def test_summary_contains_all_line_items(self):
        order = make_delivered_order(qty1=2, qty2=1)
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert "Widget" in summary
        assert "Gadget" in summary

    def test_summary_contains_total(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert f"${order.total:.2f}" in summary

    def test_summary_contains_subtotal(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert f"${order.subtotal:.2f}" in summary

    def test_summary_contains_shipping(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert "Shipping" in summary

    def test_summary_contains_tax(self):
        order = make_delivered_order()
        invoice = Invoice(order)
        summary = invoice.get_summary()
        assert "Tax" in summary


class TestInvoiceEmptyOrder:
    def test_empty_order_raises_value_error(self):
        customer = make_customer()
        delivery = make_delivery()
        order = Order(customer=customer, delivery_method=delivery)
        with pytest.raises(ValueError):
            Invoice(order)


# ── Refund Tests ─────────────────────────────────────────────────


class TestRefundCreation:
    def test_create_refund_from_delivered_order(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0, reason="Changed mind")
        assert refund is not None

    def test_refund_id_is_string(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        assert isinstance(refund.refund_id, str)
        assert len(refund.refund_id) == 8

    def test_order_id_matches_order(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        assert refund.order_id == order.order_id

    def test_amount_is_set(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        assert refund.amount == 25.0

    def test_amount_is_rounded(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.456)
        assert refund.amount == 25.46

    def test_reason_is_set(self):
        order = make_delivered_order()
        refund = Refund(order, amount=10.0, reason="Defective product")
        assert refund.reason == "Defective product"

    def test_reason_defaults_to_empty(self):
        order = make_delivered_order()
        refund = Refund(order, amount=10.0)
        assert refund.reason == ""

    def test_status_defaults_to_pending(self):
        order = make_delivered_order()
        refund = Refund(order, amount=10.0)
        assert refund.status == RefundStatus.PENDING

    def test_processed_at_defaults_to_none(self):
        order = make_delivered_order()
        refund = Refund(order, amount=10.0)
        assert refund.processed_at is None


class TestRefundAmountValidation:
    def test_refund_amount_exceeds_total_raises(self):
        order = make_delivered_order()
        with pytest.raises(RefundError):
            Refund(order, amount=order.total + 1.0)

    def test_refund_amount_zero_raises(self):
        order = make_delivered_order()
        with pytest.raises(RefundError):
            Refund(order, amount=0)

    def test_refund_amount_negative_raises(self):
        order = make_delivered_order()
        with pytest.raises(RefundError):
            Refund(order, amount=-10.0)

    def test_refund_amount_equals_total_accepted(self):
        order = make_delivered_order()
        refund = Refund(order, amount=order.total)
        assert refund.amount == order.total


class TestRefundOnNonDeliveredOrder:
    def test_refund_on_created_order_raises(self):
        customer = make_customer()
        delivery = make_delivery()
        order = Order(customer=customer, delivery_method=delivery)
        order.add_item(make_product(), quantity=1)
        with pytest.raises(RefundError):
            Refund(order, amount=25.0)

    def test_refund_on_confirmed_order_raises(self):
        customer = make_customer()
        delivery = make_delivery()
        order = Order(customer=customer, delivery_method=delivery)
        order.add_item(make_product(), quantity=1)
        order.confirm()
        with pytest.raises(RefundError):
            Refund(order, amount=25.0)

    def test_refund_on_paid_order_raises(self):
        order = make_delivered_order()
        # Instead, create a paid-only order
        customer = make_customer()
        delivery = make_delivery()
        order2 = Order(customer=customer, delivery_method=delivery)
        order2.add_item(make_product(), quantity=1)
        order2.confirm()
        order2.set_payment(make_payment())
        order2.pay()
        with pytest.raises(RefundError):
            Refund(order2, amount=25.0)

    def test_refund_on_processing_order_raises(self):
        customer = make_customer()
        delivery = make_delivery()
        order = Order(customer=customer, delivery_method=delivery)
        order.add_item(make_product(), quantity=1)
        order.confirm()
        order.set_payment(make_payment())
        order.pay()
        order.process()
        with pytest.raises(RefundError):
            Refund(order, amount=25.0)

    def test_refund_on_shipped_order_raises(self):
        customer = make_customer()
        delivery = make_delivery()
        order = Order(customer=customer, delivery_method=delivery)
        order.add_item(make_product(), quantity=1)
        order.confirm()
        order.set_payment(make_payment())
        order.pay()
        order.process()
        order.ship()
        with pytest.raises(RefundError):
            Refund(order, amount=25.0)


class TestRefundApprove:
    def test_approve_pending_to_approved(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        assert refund.status == RefundStatus.APPROVED

    def test_approve_non_pending_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        with pytest.raises(RefundError):
            refund.approve()

    def test_approve_rejected_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.reject()
        with pytest.raises(RefundError):
            refund.approve()

    def test_approve_processed_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        refund.process()
        with pytest.raises(RefundError):
            refund.approve()


class TestRefundProcess:
    def test_process_approved_to_processed(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        refund.process()
        assert refund.status == RefundStatus.PROCESSED

    def test_process_sets_processed_at(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        refund.process()
        assert isinstance(refund.processed_at, datetime)

    def test_process_non_approved_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        with pytest.raises(RefundError):
            refund.process()

    def test_process_pending_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        with pytest.raises(RefundError):
            refund.process()

    def test_process_rejected_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.reject()
        with pytest.raises(RefundError):
            refund.process()


class TestRefundReject:
    def test_reject_pending_to_rejected(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.reject()
        assert refund.status == RefundStatus.REJECTED

    def test_reject_non_pending_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        with pytest.raises(RefundError):
            refund.reject()

    def test_reject_approved_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        with pytest.raises(RefundError):
            refund.reject()

    def test_reject_processed_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.approve()
        refund.process()
        with pytest.raises(RefundError):
            refund.reject()

    def test_reject_already_rejected_raises(self):
        order = make_delivered_order()
        refund = Refund(order, amount=25.0)
        refund.reject()
        with pytest.raises(RefundError):
            refund.reject()
