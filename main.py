"""Main entry point — demonstrates the full e-commerce system."""

from datetime import datetime, timedelta

from ecommerce.cart import ShoppingCart
from ecommerce.categories import Category
from ecommerce.delivery import ExpressDelivery, SameDayDelivery, StandardDelivery
from ecommerce.discounts import (
    BuyOneGetOneDiscount,
    FixedAmountDiscount,
    PercentageDiscount,
    SeasonalDiscount,
)
from ecommerce.enums import OrderStatus
from ecommerce.exceptions import (
    EmptyOrderError,
    InsufficientStockError,
    InvalidOrderStateError,
)
from ecommerce.invoices import Invoice, Refund
from ecommerce.orders import Order
from ecommerce.payments import BankTransfer, CreditCard, DigitalWallet
from ecommerce.products import DigitalProduct, PhysicalProduct, SubscriptionProduct
from ecommerce.store import Store
from ecommerce.users import (
    BusinessCustomer,
    PremiumCustomer,
    RegularCustomer,
)


def demo() -> None:
    print("=" * 60)
    print("  E-Commerce Order & Delivery Management System")
    print("=" * 60)

    # --- Store Setup ---
    store = Store("TechMart")
    electronics = Category("Electronics", "Gadgets and devices")
    software = Category("Software", "Digital products")
    subscriptions = Category("Subscriptions", "Recurring services")

    laptop = PhysicalProduct("Laptop Pro 15", 1299.99, 2.1, "15-inch laptop", stock=10, category=electronics)
    mouse = PhysicalProduct("Wireless Mouse", 29.99, 0.15, "Ergonomic mouse", stock=50, category=electronics)
    antivirus = DigitalProduct("Antivirus Plus", 49.99, "https://download.techmart.com/av", 120.5, category=software)
    cloud_plan = SubscriptionProduct("Cloud Storage", 9.99, 12, category=subscriptions)

    for p in [laptop, mouse, antivirus, cloud_plan]:
        store.add_product(p)

    print(f"\nStore: {store.name} | Products: {store.product_count}")

    # --- Customers ---
    regular = RegularCustomer("Alice Smith", "alice@example.com", "123 Main St")
    premium = PremiumCustomer("Bob Jones", "bob@example.com", "456 Oak Ave")
    business = BusinessCustomer("Carol White", "carol@corp.com", "789 Corp Blvd", "Acme Inc")

    print(f"\nCustomers created:")
    print(f"  {regular.name} ({regular.customer_type.value})")
    print(f"  {premium.name} ({premium.customer_type.value})")
    print(f"  {business.name} ({business.customer_type.value}, company={business.company})")

    # --- Premium Customer Order ---
    print(f"\n{'─' * 60}")
    print(f"  Order #1: {premium.name} buys laptop + mouse")
    print(f"{'─' * 60}")

    cart = ShoppingCart()
    cart.add_item(laptop, 1)
    cart.add_item(mouse, 2)
    print(f"\nCart subtotal: ${cart.get_subtotal():.2f}")
    print(f"  Items: {cart.total_quantity}, Physical: {len(cart.get_physical_items())}")

    promo = PercentageDiscount("Summer Sale", "SUMMER20", 20)
    delivery = ExpressDelivery()
    order = Order(premium, delivery, promotional_discount=promo)

    for item in cart.items:
        order.add_item(item.product, item.quantity)

    print(f"\nOrder before confirmation:")
    print(f"  Subtotal: ${order.subtotal:.2f}")
    print(f"  Shipping: ${order.shipping_cost:.2f}")
    print(f"  Tax: ${order.tax:.2f}")
    print(f"  Customer discount: -${order.customer_discount:.2f}")
    print(f"  Promo discount: -${order.promo_discount_amount:.2f}")
    print(f"  Total: ${order.total:.2f}")

    order.confirm()
    print(f"\n  Status: {order.status.value}")

    payment = CreditCard("4111111111111111", "Bob Jones", "12/27")
    order.set_payment(payment)
    order.pay()
    print(f"  Payment: {payment.status.value} (${payment.amount:.2f})")

    order.process()
    print(f"  Processing...")

    order.ship()
    print(f"  Shipped! Estimated: {delivery.estimate_delivery_date().strftime('%Y-%m-%d')}")

    order.deliver()
    print(f"  Delivered! Status: {order.status.value}")

    # Invoice
    invoice = Invoice(order)
    print(f"\n{invoice.get_summary()}")

    # Refund
    refund = Refund(order, order.total, "Customer not satisfied")
    print(f"\nRefund created: {refund}")
    refund.approve()
    refund.process()
    print(f"Refund processed: {refund.status.value}")

    # --- Regular Customer: BOGO ---
    print(f"\n{'─' * 60}")
    print(f"  Order #2: {regular.name} buys mouse with BOGO")
    print(f"{'─' * 60}")

    bogo = BuyOneGetOneDiscount("BOGO Mice", "BOGO1")
    delivery2 = StandardDelivery()
    order2 = Order(regular, delivery2, promotional_discount=bogo)

    order2.add_item(mouse, 4)
    print(f"\n  Subtotal: ${order2.subtotal:.2f}")
    print(f"  Customer discount: -${order2.customer_discount:.2f}")
    print(f"  BOGO discount: -${order2.promo_discount_amount:.2f}")
    print(f"  Shipping: ${order2.shipping_cost:.2f}")
    print(f"  Tax: ${order2.tax:.2f}")
    print(f"  Total: ${order2.total:.2f}")

    # --- Business Customer: Digital Products ---
    print(f"\n{'─' * 60}")
    print(f"  Order #3: {business.name} buys digital products")
    print(f"{'─' * 60}")

    order3 = Order(business, StandardDelivery())
    order3.add_item(antivirus, 1)
    order3.add_item(cloud_plan, 1)
    print(f"\n  Subtotal: ${order3.subtotal:.2f}")
    print(f"  Shipping: ${order3.shipping_cost:.2f} (free for digital)")
    print(f"  Tax: ${order3.tax:.2f}")
    print(f"  Business discount: -${order3.customer_discount:.2f}")
    print(f"  Total: ${order3.total:.2f}")

    # --- Stock Demo ---
    print(f"\n{'─' * 60}")
    print(f"  Stock Management")
    print(f"{'─' * 60}")
    print(f"  Laptop stock before order: {laptop.stock}")
    print(f"  (Stock was reduced by 1 during order #1 confirmation)")
    print(f"  Laptop stock after: {laptop.stock}")

    laptop.increase_stock(5)
    print(f"  After restocking +5: {laptop.stock}")

    # --- Cancel Demo ---
    print(f"\n{'─' * 60}")
    print(f"  Cancel Demo")
    print(f"{'─' * 60}")

    cancel_order = Order(regular, StandardDelivery())
    cancel_order.add_item(mouse, 1)
    print(f"  Order status: {cancel_order.status.value}")
    cancel_order.cancel()
    print(f"  After cancel: {cancel_order.status.value}")

    try:
        cancel_order.cancel()
    except InvalidOrderStateError as e:
        print(f"  Double cancel rejected: {e}")

    # --- Empty Order Demo ---
    print(f"\n{'─' * 60}")
    print(f"  Empty Order Demo")
    print(f"{'─' * 60}")
    empty_order = Order(regular, StandardDelivery())
    try:
        empty_order.confirm()
    except EmptyOrderError as e:
        print(f"  Empty order rejected: {e}")

    # --- Wallet Payment ---
    print(f"\n{'─' * 60}")
    print(f"  Digital Wallet Payment")
    print(f"{'─' * 60}")
    wallet = DigitalWallet("W001", "Alice Smith", 500.00)
    print(f"  Wallet balance: ${wallet.wallet_balance:.2f}")

    order4 = Order(regular, SameDayDelivery())
    order4.add_item(mouse, 2)
    print(f"  Subtotal: ${order4.subtotal:.2f}")
    print(f"  Same-day shipping: ${order4.shipping_cost:.2f}")
    order4.confirm()
    order4.set_payment(wallet)
    order4.pay()
    print(f"  Order paid: ${order4.total:.2f}")
    print(f"  Wallet balance after: ${wallet.wallet_balance:.2f}")

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"  System Summary")
    print(f"{'=' * 60}")
    print(f"  Store: {store.name}")
    print(f"  Total products: {store.product_count}")
    print(f"  Categories: {[c.name for c in store.categories]}")
    print(f"  {premium.name} orders: {len(premium.orders)}")
    print(f"  {regular.name} orders: {len(regular.orders)}")
    print(f"\n  Laptop stock: {laptop.stock}")
    print(f"  Mouse stock: {mouse.stock}")
    print(f"  Digital products: no stock needed")
    print(f"  Subscription products: no stock needed")
    print(f"\n{'=' * 60}")
    print(f"  All demonstrations complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    demo()
