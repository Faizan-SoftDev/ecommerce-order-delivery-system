import pytest
from unittest.mock import patch

from ecommerce.enums import PaymentMethodType, PaymentStatus
from ecommerce.exceptions import PaymentError
from ecommerce.payments import (
    PaymentMethod,
    CreditCard,
    BankTransfer,
    DigitalWallet,
)


# ---------------------------------------------------------------------------
# CreditCard tests
# ---------------------------------------------------------------------------

class TestCreditCard:
    """Tests for CreditCard payment method."""

    def _make(self, number="4111111111111111", name="John Doe", expiry="12/28"):
        return CreditCard(card_number=number, cardholder_name=name, expiry=expiry)

    def test_creation_valid_card(self):
        cc = self._make()
        assert cc.cardholder_name == "John Doe"
        assert cc.status == PaymentStatus.PENDING
        assert cc.amount == 0.0
        assert cc.transaction_id is None

    def test_payment_method_type(self):
        assert self._make().payment_method_type() == PaymentMethodType.CREDIT_CARD

    def test_masked_number(self):
        cc = self._make(number="4111111111111111")
        assert cc.masked_number == "****-****-****-1111"

    def test_process_payment_success(self):
        cc = self._make()
        result = cc.process_payment(99.99)
        assert result is True
        assert cc.status == PaymentStatus.COMPLETED
        assert cc.amount == 99.99
        assert cc.transaction_id is not None
        assert cc.transaction_id.startswith("CC-")

    def test_process_payment_twice_raises(self):
        cc = self._make()
        cc.process_payment(50.0)
        with pytest.raises(PaymentError, match="already processed"):
            cc.process_payment(25.0)

    def test_process_payment_zero_amount_raises(self):
        with pytest.raises(PaymentError, match="positive"):
            self._make().process_payment(0)

    def test_process_payment_negative_amount_raises(self):
        with pytest.raises(PaymentError, match="positive"):
            self._make().process_payment(-10)

    def test_refund_payment_success(self):
        cc = self._make()
        cc.process_payment(100.0)
        assert cc.refund_payment(100.0) is True
        assert cc.status == PaymentStatus.REFUNDED

    def test_refund_non_completed_raises(self):
        with pytest.raises(PaymentError, match="Can only refund completed"):
            self._make().refund_payment(10)

    def test_refund_exceeds_paid_raises(self):
        cc = self._make()
        cc.process_payment(50.0)
        with pytest.raises(PaymentError, match="exceeds paid amount"):
            cc.refund_payment(60.0)

    def test_refund_zero_raises(self):
        cc = self._make()
        cc.process_payment(50.0)
        with pytest.raises(PaymentError, match="positive"):
            cc.refund_payment(0)

    def test_refund_negative_raises(self):
        cc = self._make()
        cc.process_payment(50.0)
        with pytest.raises(PaymentError, match="positive"):
            cc.refund_payment(-10)

    def test_invalid_card_too_short_raises(self):
        with pytest.raises(PaymentError, match="13-19 digits"):
            self._make(number="12345678901")

    def test_invalid_card_non_digits_raises(self):
        with pytest.raises(PaymentError, match="13-19 digits"):
            self._make(number="4111abcdefgh")

    def test_invalid_expiry_format_raises(self):
        with pytest.raises(PaymentError, match="Invalid expiry"):
            self._make(expiry="122028")


# ---------------------------------------------------------------------------
# BankTransfer tests
# ---------------------------------------------------------------------------

class TestBankTransfer:
    """Tests for BankTransfer payment method."""

    def _make(self, account="1234567890", bank="Chase", routing="021000021"):
        return BankTransfer(account_number=account, bank_name=bank, routing_number=routing)

    def test_creation(self):
        bt = self._make()
        assert bt.bank_name == "Chase"
        assert bt.status == PaymentStatus.PENDING

    def test_payment_method_type(self):
        assert self._make().payment_method_type() == PaymentMethodType.BANK_TRANSFER

    def test_process_payment_success(self):
        bt = self._make()
        assert bt.process_payment(200.0) is True
        assert bt.status == PaymentStatus.COMPLETED
        assert bt.amount == 200.0
        assert bt.transaction_id.startswith("BT-")

    def test_refund_payment_success(self):
        bt = self._make()
        bt.process_payment(200.0)
        assert bt.refund_payment(200.0) is True
        assert bt.status == PaymentStatus.REFUNDED

    def test_process_payment_already_completed_raises(self):
        bt = self._make()
        bt.process_payment(100.0)
        with pytest.raises(PaymentError, match="already processed"):
            bt.process_payment(50.0)

    def test_refund_exceeds_paid_raises(self):
        bt = self._make()
        bt.process_payment(100.0)
        with pytest.raises(PaymentError, match="exceeds paid amount"):
            bt.refund_payment(150.0)

    def test_short_account_number_raises(self):
        with pytest.raises(PaymentError, match="at least 8 characters"):
            BankTransfer(account_number="1234", bank_name="Tiny Bank")


# ---------------------------------------------------------------------------
# DigitalWallet tests
# ---------------------------------------------------------------------------

class TestDigitalWallet:
    """Tests for DigitalWallet payment method."""

    def _make(self, wallet_id="W-001", owner="Alice", balance=500.0):
        return DigitalWallet(wallet_id=wallet_id, owner_name=owner, initial_balance=balance)

    def test_creation_with_initial_balance(self):
        dw = self._make(balance=250.0)
        assert dw.wallet_balance == 250.0
        assert dw.owner_name == "Alice"

    def test_wallet_balance_property(self):
        dw = self._make(balance=100.0)
        assert dw.wallet_balance == 100.0

    def test_owner_name_property(self):
        dw = self._make(owner="Bob")
        assert dw.owner_name == "Bob"

    def test_payment_method_type(self):
        assert self._make().payment_method_type() == PaymentMethodType.DIGITAL_WALLET

    def test_top_up(self):
        dw = self._make(balance=100.0)
        dw.top_up(50.0)
        assert dw.wallet_balance == 150.0

    def test_top_up_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            self._make().top_up(-20)

    def test_process_payment_success(self):
        dw = self._make(balance=200.0)
        assert dw.process_payment(75.0) is True
        assert dw.status == PaymentStatus.COMPLETED
        assert dw.amount == 75.0
        assert dw.wallet_balance == 125.0
        assert dw.transaction_id.startswith("DW-")

    def test_process_payment_insufficient_balance_raises(self):
        dw = self._make(balance=50.0)
        with pytest.raises(PaymentError, match="Insufficient"):
            dw.process_payment(100.0)

    def test_refund_payment_success(self):
        dw = self._make(balance=200.0)
        dw.process_payment(80.0)
        assert dw.refund_payment(80.0) is True
        assert dw.status == PaymentStatus.REFUNDED
        assert dw.wallet_balance == 200.0

    def test_process_payment_already_completed_raises(self):
        dw = self._make(balance=300.0)
        dw.process_payment(100.0)
        with pytest.raises(PaymentError, match="already processed"):
            dw.process_payment(50.0)

    def test_refund_exceeds_paid_raises(self):
        dw = self._make(balance=100.0)
        dw.process_payment(50.0)
        with pytest.raises(PaymentError, match="exceeds paid amount"):
            dw.refund_payment(60.0)


# ---------------------------------------------------------------------------
# Polymorphism tests
# ---------------------------------------------------------------------------

class TestPolymorphism:
    """Verify that process_payment / refund_payment work polymorphically."""

    def test_polymorphic_process_and_refund(self):
        methods = [
            CreditCard(card_number="4111111111111111", cardholder_name="A", expiry="12/30"),
            BankTransfer(account_number="1234567890", bank_name="B"),
            DigitalWallet(wallet_id="W-1", owner_name="C", initial_balance=1000.0),
        ]

        for pm in methods:
            assert pm.process_payment(10.0) is True
            assert pm.status == PaymentStatus.COMPLETED
            assert pm.amount == 10.0
            assert pm.transaction_id is not None

        for pm in methods:
            assert pm.refund_payment(10.0) is True
            assert pm.status == PaymentStatus.REFUNDED


# ---------------------------------------------------------------------------
# Base class tests
# ---------------------------------------------------------------------------

class TestPaymentMethodBase:
    """Ensure PaymentMethod cannot be instantiated directly."""

    def test_cannot_instantiate_base(self):
        with pytest.raises(TypeError):
            PaymentMethod(name="Test")
