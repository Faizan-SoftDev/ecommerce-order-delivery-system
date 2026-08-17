"""Custom exceptions for the e-commerce system."""


class ECommerceError(Exception):
    """Base exception for all e-commerce errors."""


class InsufficientStockError(ECommerceError):
    """Raised when product stock is insufficient for the requested quantity."""

    def __init__(self, product_name: str, available: int, requested: int) -> None:
        self.product_name = product_name
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for '{product_name}': "
            f"available={available}, requested={requested}"
        )


class InvalidQuantityError(ECommerceError):
    """Raised when a quantity is not greater than zero."""

    def __init__(self, quantity: int) -> None:
        self.quantity = quantity
        super().__init__(f"Quantity must be greater than zero, got {quantity}")


class InvalidPriceError(ECommerceError):
    """Raised when a price is negative."""

    def __init__(self, price: float) -> None:
        self.price = price
        super().__init__(f"Price cannot be negative, got {price}")


class InvalidOrderStateError(ECommerceError):
    """Raised when an invalid order state transition is attempted."""

    def __init__(self, current: str, attempted: str) -> None:
        self.current = current
        self.attempted = attempted
        super().__init__(
            f"Cannot transition from '{current}' to '{attempted}'"
        )


class EmptyOrderError(ECommerceError):
    """Raised when an operation is performed on an empty order."""

    def __init__(self, message: str = "Order has no items") -> None:
        super().__init__(message)


class PaymentError(ECommerceError):
    """Raised when a payment operation fails."""

    def __init__(self, message: str = "Payment processing failed") -> None:
        super().__init__(message)


class RefundError(ECommerceError):
    """Raised when a refund operation fails."""

    def __init__(self, message: str = "Refund processing failed") -> None:
        super().__init__(message)


class DiscountError(ECommerceError):
    """Raised when a discount calculation fails or produces invalid result."""

    def __init__(self, message: str = "Discount calculation failed") -> None:
        super().__init__(message)


class ProductNotFoundError(ECommerceError):
    """Raised when a product is not found in the store."""

    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        super().__init__(f"Product '{product_id}' not found")


class UserNotFoundError(ECommerceError):
    """Raised when a user is not found."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User '{user_id}' not found")


class CartEmptyError(ECommerceError):
    """Raised when an operation requires a non-empty cart."""

    def __init__(self, message: str = "Shopping cart is empty") -> None:
        super().__init__(message)


class DuplicateItemError(ECommerceError):
    """Raised when trying to add a duplicate item to a cart."""

    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        super().__init__(f"Product '{product_id}' is already in the cart")
