"""Enumerations for the e-commerce system."""

from enum import Enum, auto


class OrderStatus(Enum):
    """Lifecycle states of an order."""

    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(Enum):
    """Status of a payment transaction."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class RefundStatus(Enum):
    """Status of a refund request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"


class CustomerType(Enum):
    """Types of customers."""

    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    BUSINESS = "BUSINESS"


class ProductType(Enum):
    """Types of products."""

    PHYSICAL = "PHYSICAL"
    DIGITAL = "DIGITAL"
    SUBSCRIPTION = "SUBSCRIPTION"


class DeliverySpeed(Enum):
    """Speed tiers for delivery."""

    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    SAME_DAY = "SAME_DAY"


class DiscountType(Enum):
    """Types of discounts."""

    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    BUY_ONE_GET_ONE = "BUY_ONE_GET_ONE"
    SEASONAL = "SEASONAL"


class PaymentMethodType(Enum):
    """Types of payment methods."""

    CREDIT_CARD = "CREDIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    DIGITAL_WALLET = "DIGITAL_WALLET"
