"""Order and OrderItem — the core orchestration of purchases."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from ecommerce.enums import OrderStatus
from ecommerce.exceptions import (
    EmptyOrderError,
    InsufficientStockError,
    InvalidOrderStateError,
    InvalidQuantityError,
)
from ecommerce.products import Product

if TYPE_CHECKING:
    from ecommerce.delivery import DeliveryMethod
    from ecommerce.discounts import Discount
    from ecommerce.payments import PaymentMethod
    from ecommerce.users import Customer


class OrderItem:
    """A line item within an order.

    Demonstrates: Composition (owned by Order), Association (references Product)
    Price is locked at time of purchase — product price can change later.
    """

    def __init__(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        self._product: Product = product
        self._quantity: int = quantity
        self._unit_price: float = product.price
        self._subtotal: float = product.calculate_price(quantity)
        self._item_id: str = str(uuid.uuid4())[:8]

    @property
    def item_id(self) -> str:
        return self._item_id

    @property
    def product(self) -> Product:
        return self._product

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def unit_price(self) -> float:
        return self._unit_price

    @property
    def subtotal(self) -> float:
        return self._subtotal

    def __repr__(self) -> str:
        return (
            f"OrderItem(product='{self._product.name}', "
            f"qty={self._quantity}, subtotal={self._subtotal})"
        )


class Order:
    """An order with full lifecycle management.

    Demonstrates: Composition (owns OrderItems), Association (Customer,
    PaymentMethod, DeliveryMethod, Discount), Polymorphism (delegates to
    each component for calculations).

    Lifecycle: CREATED → CONFIRMED → PAID → PROCESSING → SHIPPED → DELIVERED
    Also: CANCELLED, REFUNDED
    """

    VALID_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
        OrderStatus.CREATED: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
        OrderStatus.CONFIRMED: [OrderStatus.PAID, OrderStatus.CANCELLED],
        OrderStatus.PAID: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
        OrderStatus.PROCESSING: [
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
        OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
        OrderStatus.CANCELLED: [],
        OrderStatus.REFUNDED: [],
    }

    TAX_RATE: float = 0.08

    def __init__(
        self,
        customer: Customer,
        delivery_method: DeliveryMethod,
        payment_method: Optional[PaymentMethod] = None,
        promotional_discount: Optional[Discount] = None,
    ) -> None:
        self._order_id: str = str(uuid.uuid4())[:8]
        self._customer: Customer = customer
        self._delivery_method: DeliveryMethod = delivery_method
        self._payment_method: Optional[PaymentMethod] = payment_method
        self._promotional_discount: Optional[Discount] = promotional_discount
        self._items: List[OrderItem] = []
        self._status: OrderStatus = OrderStatus.CREATED
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = datetime.now()
        self._subtotal: float = 0.0
        self._shipping_cost: float = 0.0
        self._tax: float = 0.0
        self._customer_discount: float = 0.0
        self._promo_discount_amount: float = 0.0
        self._additional_charges: float = 0.0
        self._total: float = 0.0
        self._additional_charges_description: str = ""

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def total(self) -> float:
        return self._total

    @property
    def subtotal(self) -> float:
        return self._subtotal

    @property
    def shipping_cost(self) -> float:
        return self._shipping_cost

    @property
    def tax(self) -> float:
        return self._tax

    @property
    def customer_discount(self) -> float:
        return self._customer_discount

    @property
    def promo_discount_amount(self) -> float:
        return self._promo_discount_amount

    @property
    def additional_charges(self) -> float:
        return self._additional_charges

    @property
    def items(self) -> List[OrderItem]:
        return list(self._items)

    @property
    def delivery_method(self) -> DeliveryMethod:
        return self._delivery_method

    @property
    def payment_method(self) -> Optional[PaymentMethod]:
        return self._payment_method

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def has_physical_items(self) -> bool:
        return any(item.product.requires_shipping() for item in self._items)

    def _validate_transition(self, new_status: OrderStatus) -> None:
        allowed = self.VALID_TRANSITIONS.get(self._status, [])
        if new_status not in allowed:
            raise InvalidOrderStateError(self._status.value, new_status.value)

    def _transition_to(self, new_status: OrderStatus) -> None:
        self._validate_transition(new_status)
        self._status = new_status
        self._updated_at = datetime.now()

    def add_item(self, product: Product, quantity: int = 1) -> None:
        if self._status != OrderStatus.CREATED:
            raise InvalidOrderStateError(
                self._status.value, "ADD_ITEM"
            )
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        if not product.is_active:
            raise ValueError(f"Product '{product.name}' is not active")
        if product.requires_shipping() and product.stock < quantity:
            raise InsufficientStockError(product.name, product.stock, quantity)

        for item in self._items:
            if item.product.product_id == product.product_id:
                new_qty = item.quantity + quantity
                if product.requires_shipping() and product.stock < new_qty:
                    raise InsufficientStockError(product.name, product.stock, new_qty)
                self._items.remove(item)
                self._items.append(OrderItem(product, new_qty))
                return

        self._items.append(OrderItem(product, quantity))
        self._recalculate()

    def remove_item(self, product_id: str) -> None:
        if self._status != OrderStatus.CREATED:
            raise InvalidOrderStateError(self._status.value, "REMOVE_ITEM")
        for item in self._items:
            if item.product.product_id == product_id:
                self._items.remove(item)
                self._recalculate()
                return
        raise KeyError(f"Product '{product_id}' not in order")

    def _recalculate(self) -> None:
        if not self._items:
            self._subtotal = 0.0
            self._total = 0.0
            return

        self._subtotal = round(
            sum(item.subtotal for item in self._items), 2
        )

        if self.has_physical_items:
            total_weight = sum(
                item.quantity * getattr(item.product, "weight_kg", 1.0)
                for item in self._items
                if item.product.requires_shipping()
            )
            raw_shipping = self._delivery_method.calculate_cost(
                total_weight, self._subtotal
            )
            self._shipping_cost = self._customer.get_shipping_surcharge(raw_shipping)
        else:
            self._shipping_cost = 0.0

        self._tax = round(self._subtotal * self.TAX_RATE, 2)
        self._customer_discount = self._customer.calculate_discount(self._subtotal)

        if self._promotional_discount is not None and self._promotional_discount.is_active:
            total_qty = sum(item.quantity for item in self._items)
            self._promo_discount_amount = self._promotional_discount.apply_discount(
                self._subtotal, total_qty
            )
        else:
            self._promo_discount_amount = 0.0

        self._total = round(
            self._subtotal
            + self._shipping_cost
            + self._tax
            - self._customer_discount
            - self._promo_discount_amount
            + self._additional_charges,
            2,
        )
        if self._total < 0:
            self._total = 0.0

    def set_promotional_discount(self, discount: Discount) -> None:
        if self._status != OrderStatus.CREATED:
            raise InvalidOrderStateError(self._status.value, "SET_DISCOUNT")
        self._promotional_discount = discount
        self._recalculate()

    def add_additional_charge(self, amount: float, description: str = "") -> None:
        if self._status not in (OrderStatus.CREATED, OrderStatus.CONFIRMED):
            raise InvalidOrderStateError(self._status.value, "ADD_CHARGE")
        if amount < 0:
            raise ValueError("Additional charge cannot be negative")
        self._additional_charges = round(self._additional_charges + amount, 2)
        self._additional_charges_description = description
        self._recalculate()

    def calculate_total(self) -> float:
        self._recalculate()
        return self._total

    def confirm(self) -> None:
        if not self._items:
            raise EmptyOrderError("Cannot confirm an empty order")
        if self.has_physical_items:
            for item in self._items:
                if item.product.requires_shipping():
                    item.product.decrease_stock(item.quantity)
        self._transition_to(OrderStatus.CONFIRMED)
        self._recalculate()

    def set_payment(self, payment_method: PaymentMethod) -> None:
        if self._status != OrderStatus.CONFIRMED:
            raise InvalidOrderStateError(self._status.value, "SET_PAYMENT")
        self._payment_method = payment_method

    def pay(self) -> None:
        if self._status != OrderStatus.CONFIRMED:
            raise InvalidOrderStateError(self._status.value, "PAY")
        if self._payment_method is None:
            raise ValueError("No payment method set")
        self._recalculate()
        success = self._payment_method.process_payment(self._total)
        if not success:
            raise ValueError("Payment processing failed")
        self._transition_to(OrderStatus.PAID)

    def process(self) -> None:
        self._transition_to(OrderStatus.PROCESSING)

    def ship(self) -> None:
        if self._status != OrderStatus.PROCESSING:
            raise InvalidOrderStateError(self._status.value, "SHIP")
        if self.has_physical_items:
            self._transition_to(OrderStatus.SHIPPED)
        else:
            self._transition_to(OrderStatus.DELIVERED)

    def deliver(self) -> None:
        self._transition_to(OrderStatus.DELIVERED)

    def cancel(self) -> None:
        if self._status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise InvalidOrderStateError(self._status.value, "CANCEL")
        if self._status in (OrderStatus.CONFIRMED, OrderStatus.PAID, OrderStatus.PROCESSING):
            for item in self._items:
                if item.product.requires_shipping():
                    item.product.increase_stock(item.quantity)
        self._transition_to(OrderStatus.CANCELLED)

    def refund(self) -> None:
        if self._status != OrderStatus.DELIVERED:
            raise InvalidOrderStateError(self._status.value, "REFUND")
        if self._payment_method is not None:
            self._payment_method.refund_payment(self._total)
        self._transition_to(OrderStatus.REFUNDED)

    def __repr__(self) -> str:
        return (
            f"Order(id='{self._order_id}', status={self._status.value}, "
            f"total={self._total}, items={len(self._items)})"
        )
