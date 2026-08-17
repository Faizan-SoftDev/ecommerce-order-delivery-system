"""Payment method hierarchy with polymorphic processing."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ecommerce.enums import PaymentStatus, PaymentMethodType
from ecommerce.exceptions import PaymentError


class PaymentMethod(ABC):
    """Abstract base payment method.

    Demonstrates: Abstraction, Encapsulation
    """

    def __init__(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Payment method name cannot be empty")
        self._payment_id: str = str(uuid.uuid4())[:8]
        self._name: str = name.strip()
        self._status: PaymentStatus = PaymentStatus.PENDING
        self._amount: float = 0.0
        self._transaction_id: Optional[str] = None
        self._created_at: datetime = datetime.now()

    @property
    def payment_id(self) -> str:
        return self._payment_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> PaymentStatus:
        return self._status

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def transaction_id(self) -> Optional[str]:
        return self._transaction_id

    @abstractmethod
    def payment_method_type(self) -> PaymentMethodType:
        """Return the concrete payment type. Demonstrates Polymorphism."""

    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        """Process a payment. Returns True on success. Demonstrates Polymorphism."""

    @abstractmethod
    def refund_payment(self, amount: float) -> bool:
        """Refund a payment. Returns True on success. Demonstrates Polymorphism."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name='{self._name}', "
            f"status={self._status.value})"
        )


class CreditCard(PaymentMethod):
    """Credit card payment with card validation.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(self, card_number: str, cardholder_name: str, expiry: str) -> None:
        super().__init__(name=f"Credit Card ending {card_number[-4:]}")
        self._card_number: str = card_number.replace(" ", "").replace("-", "")
        self._cardholder_name: str = cardholder_name
        self._expiry: str = expiry
        self._validate_card()

    def _validate_card(self) -> None:
        digits = self._card_number
        if not digits.isdigit() or len(digits) < 13 or len(digits) > 19:
            raise PaymentError(f"Invalid card number: must be 13-19 digits")
        parts = self._expiry.split("/")
        if len(parts) != 2:
            raise PaymentError("Invalid expiry format, expected MM/YY")

    @property
    def cardholder_name(self) -> str:
        return self._cardholder_name

    @property
    def masked_number(self) -> str:
        return f"****-****-****-{self._card_number[-4:]}"

    def payment_method_type(self) -> PaymentMethodType:
        return PaymentMethodType.CREDIT_CARD

    def process_payment(self, amount: float) -> bool:
        if amount <= 0:
            raise PaymentError("Payment amount must be positive")
        if self._status == PaymentStatus.COMPLETED:
            raise PaymentError("Payment already processed")
        self._amount = round(amount, 2)
        self._transaction_id = f"CC-{uuid.uuid4().hex[:8].upper()}"
        self._status = PaymentStatus.COMPLETED
        return True

    def refund_payment(self, amount: float) -> bool:
        if self._status != PaymentStatus.COMPLETED:
            raise PaymentError("Can only refund completed payments")
        if amount <= 0:
            raise PaymentError("Refund amount must be positive")
        if amount > self._amount:
            raise PaymentError(
                f"Refund ${amount:.2f} exceeds paid amount ${self._amount:.2f}"
            )
        self._status = PaymentStatus.REFUNDED
        return True


class BankTransfer(PaymentMethod):
    """Bank transfer payment with account validation.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(self, account_number: str, bank_name: str, routing_number: str = "") -> None:
        super().__init__(name=f"Bank Transfer ({bank_name})")
        self._account_number: str = account_number
        self._bank_name: str = bank_name
        self._routing_number: str = routing_number
        self._validate_account()

    def _validate_account(self) -> None:
        if not self._account_number or len(self._account_number) < 8:
            raise PaymentError("Account number must be at least 8 characters")

    @property
    def bank_name(self) -> str:
        return self._bank_name

    def payment_method_type(self) -> PaymentMethodType:
        return PaymentMethodType.BANK_TRANSFER

    def process_payment(self, amount: float) -> bool:
        if amount <= 0:
            raise PaymentError("Payment amount must be positive")
        if self._status == PaymentStatus.COMPLETED:
            raise PaymentError("Payment already processed")
        self._amount = round(amount, 2)
        self._transaction_id = f"BT-{uuid.uuid4().hex[:8].upper()}"
        self._status = PaymentStatus.COMPLETED
        return True

    def refund_payment(self, amount: float) -> bool:
        if self._status != PaymentStatus.COMPLETED:
            raise PaymentError("Can only refund completed payments")
        if amount <= 0:
            raise PaymentError("Refund amount must be positive")
        if amount > self._amount:
            raise PaymentError(
                f"Refund ${amount:.2f} exceeds paid amount ${self._amount:.2f}"
            )
        self._status = PaymentStatus.REFUNDED
        return True


class DigitalWallet(PaymentMethod):
    """Digital wallet payment with balance-based deduction.

    Demonstrates: Inheritance, Polymorphism
    """

    def __init__(self, wallet_id: str, owner_name: str, initial_balance: float = 0.0) -> None:
        super().__init__(name=f"Digital Wallet ({wallet_id})")
        self._wallet_id: str = wallet_id
        self._owner_name: str = owner_name
        self._wallet_balance: float = round(max(initial_balance, 0.0), 2)

    @property
    def wallet_balance(self) -> float:
        return self._wallet_balance

    @property
    def owner_name(self) -> str:
        return self._owner_name

    def top_up(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Top-up amount must be positive")
        self._wallet_balance = round(self._wallet_balance + amount, 2)

    def payment_method_type(self) -> PaymentMethodType:
        return PaymentMethodType.DIGITAL_WALLET

    def process_payment(self, amount: float) -> bool:
        if amount <= 0:
            raise PaymentError("Payment amount must be positive")
        if self._status == PaymentStatus.COMPLETED:
            raise PaymentError("Payment already processed")
        if self._wallet_balance < amount:
            raise PaymentError(
                f"Insufficient wallet balance: have ${self._wallet_balance:.2f}, "
                f"need ${amount:.2f}"
            )
        self._wallet_balance = round(self._wallet_balance - amount, 2)
        self._amount = round(amount, 2)
        self._transaction_id = f"DW-{uuid.uuid4().hex[:8].upper()}"
        self._status = PaymentStatus.COMPLETED
        return True

    def refund_payment(self, amount: float) -> bool:
        if self._status != PaymentStatus.COMPLETED:
            raise PaymentError("Can only refund completed payments")
        if amount <= 0:
            raise PaymentError("Refund amount must be positive")
        if amount > self._amount:
            raise PaymentError(
                f"Refund ${amount:.2f} exceeds paid amount ${self._amount:.2f}"
            )
        self._wallet_balance = round(self._wallet_balance + amount, 2)
        self._status = PaymentStatus.REFUNDED
        return True
