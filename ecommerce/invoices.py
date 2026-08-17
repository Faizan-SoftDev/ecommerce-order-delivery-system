"""Invoice and Refund models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from ecommerce.enums import RefundStatus
from ecommerce.exceptions import RefundError

if TYPE_CHECKING:
    from ecommerce.orders import Order


class Invoice:
    """A read-only financial snapshot of an order.

    Demonstrates: Association (references Order)
    """

    def __init__(self, order: Order) -> None:
        if not order.items:
            raise ValueError("Cannot create invoice for empty order")
        self._invoice_id: str = str(uuid.uuid4())[:8]
        self._order_id: str = order.order_id
        self._customer_name: str = order.customer.name
        self._created_at: datetime = datetime.now()
        self._line_items: List[dict] = [
            {
                "product": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in order.items
        ]
        self._subtotal: float = order.subtotal
        self._shipping_cost: float = order.shipping_cost
        self._tax: float = order.tax
        self._customer_discount: float = order.customer_discount
        self._promo_discount: float = order.promo_discount_amount
        self._additional_charges: float = order.additional_charges
        self._total: float = order.total

    @property
    def invoice_id(self) -> str:
        return self._invoice_id

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer_name(self) -> str:
        return self._customer_name

    @property
    def total(self) -> float:
        return self._total

    @property
    def line_items(self) -> List[dict]:
        return list(self._line_items)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def get_summary(self) -> str:
        lines = [
            f"Invoice #{self._invoice_id} (Order #{self._order_id})",
            f"Customer: {self._customer_name}",
            f"Date: {self._created_at.strftime('%Y-%m-%d %H:%M')}",
            "-" * 40,
        ]
        for item in self._line_items:
            lines.append(
                f"  {item['product']} x{item['quantity']} "
                f"@ ${item['unit_price']:.2f} = ${item['subtotal']:.2f}"
            )
        lines.append("-" * 40)
        lines.append(f"  Subtotal:        ${self._subtotal:.2f}")
        lines.append(f"  Shipping:        ${self._shipping_cost:.2f}")
        lines.append(f"  Tax:             ${self._tax:.2f}")
        if self._customer_discount > 0:
            lines.append(f"  Cust. Discount: -${self._customer_discount:.2f}")
        if self._promo_discount > 0:
            lines.append(f"  Promo Discount: -${self._promo_discount:.2f}")
        if self._additional_charges > 0:
            lines.append(f"  Additional:     +${self._additional_charges:.2f}")
        lines.append(f"  TOTAL:           ${self._total:.2f}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"Invoice(id='{self._invoice_id}', "
            f"order='{self._order_id}', total={self._total})"
        )


class Refund:
    """Manages a refund for a delivered order.

    Demonstrates: Association (references Order, PaymentMethod)
    """

    def __init__(self, order: Order, amount: float, reason: str = "") -> None:
        from ecommerce.enums import OrderStatus

        if order.status != OrderStatus.DELIVERED:
            raise RefundError(
                f"Order must be DELIVERED to refund, current: {order.status.value}"
            )
        if amount <= 0:
            raise RefundError("Refund amount must be positive")
        if amount > order.total:
            raise RefundError(
                f"Refund ${amount:.2f} exceeds order total ${order.total:.2f}"
            )

        self._refund_id: str = str(uuid.uuid4())[:8]
        self._order_id: str = order.order_id
        self._amount: float = round(amount, 2)
        self._reason: str = reason
        self._status: RefundStatus = RefundStatus.PENDING
        self._created_at: datetime = datetime.now()
        self._processed_at: datetime | None = None

    @property
    def refund_id(self) -> str:
        return self._refund_id

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def status(self) -> RefundStatus:
        return self._status

    @property
    def processed_at(self) -> datetime | None:
        return self._processed_at

    def approve(self) -> None:
        if self._status != RefundStatus.PENDING:
            raise RefundError(f"Cannot approve refund in {self._status.value} status")
        self._status = RefundStatus.APPROVED

    def process(self) -> None:
        if self._status != RefundStatus.APPROVED:
            raise RefundError(f"Cannot process refund in {self._status.value} status")
        self._status = RefundStatus.PROCESSED
        self._processed_at = datetime.now()

    def reject(self) -> None:
        if self._status != RefundStatus.PENDING:
            raise RefundError(f"Cannot reject refund in {self._status.value} status")
        self._status = RefundStatus.REJECTED

    def __repr__(self) -> str:
        return (
            f"Refund(id='{self._refund_id}', amount={self._amount}, "
            f"status={self._status.value})"
        )
