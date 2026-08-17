"""Flask web application for the E-Commerce system."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, redirect, url_for, flash, session

from ecommerce.categories import Category
from ecommerce.delivery import ExpressDelivery, SameDayDelivery, StandardDelivery
from ecommerce.discounts import (
    BuyOneGetOneDiscount,
    FixedAmountDiscount,
    PercentageDiscount,
)
from ecommerce.enums import OrderStatus
from ecommerce.exceptions import (
    ECommerceError,
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
    Customer,
    PremiumCustomer,
    RegularCustomer,
)

app = Flask(__name__)
app.secret_key = "ecommerce-oop-assignment-secret-key"


# ---------------------------------------------------------------------------
# In-memory data store — initialized once on startup
# ---------------------------------------------------------------------------

def create_store() -> Store:
    store = Store("TechMart")

    electronics = Category("Electronics", "Gadgets and devices")
    software = Category("Software", "Digital products")
    subs = Category("Subscriptions", "Recurring services")

    laptop = PhysicalProduct(
        "Laptop Pro 15", 1299.99, 2.1,
        "15-inch high-performance laptop with 16GB RAM",
        stock=10, category=electronics,
    )
    mouse = PhysicalProduct(
        "Wireless Mouse", 29.99, 0.15,
        "Ergonomic wireless mouse with adjustable DPI",
        stock=50, category=electronics,
    )
    headphones = PhysicalProduct(
        "Noise-Cancelling Headphones", 199.99, 0.3,
        "Premium over-ear headphones with ANC",
        stock=25, category=electronics,
    )
    phone_case = PhysicalProduct(
        "Phone Case", 14.99, 0.05,
        "Shockproof silicone phone case",
        stock=100, category=electronics,
    )
    antivirus = DigitalProduct(
        "Antivirus Plus", 49.99,
        "https://download.techmart.com/antivirus", 120.5,
        "Full protection against malware and viruses",
        category=software,
    )
    ebook = DigitalProduct(
        "Python Mastery E-Book", 29.99,
        "https://download.techmart.com/python-ebook", 45.0,
        "Complete guide to Python programming",
        category=software,
    )
    cloud = SubscriptionProduct(
        "Cloud Storage", 9.99, 12,
        "1TB cloud storage with sync across devices",
        category=subs,
    )
    vpn = SubscriptionProduct(
        "VPN Service", 4.99, 6,
        "Unlimited VPN with 50+ server locations",
        category=subs,
    )

    for p in [laptop, mouse, headphones, phone_case, antivirus, ebook, cloud, vpn]:
        store.add_product(p)

    return store


def create_discounts() -> dict:
    return {
        "SUMMER20": PercentageDiscount("Summer Sale 20%", "SUMMER20", 20),
        "FLAT10": FixedAmountDiscount("$10 Off", "FLAT10", 10),
        "BOGO": BuyOneGetOneDiscount("Buy One Get One", "BOGO"),
        "SAVE15": PercentageDiscount("15% Off", "SAVE15", 15),
    }


store = create_store()
discounts = create_discounts()
customers: dict[str, Customer] = {}
orders: dict[str, Order] = {}


def get_customer() -> Customer:
    cid = session.get("customer_id")
    if cid and cid in customers:
        return customers[cid]
    return None


def ensure_customer() -> Customer:
    c = get_customer()
    if c is None:
        c = RegularCustomer("Guest User", "guest@example.com")
        customers[c.user_id] = c
        session["customer_id"] = c.user_id
    return c


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    products = store.get_active_products()
    categories = store.categories
    customer = get_customer()
    cart_count = session.get("cart_count", 0)
    return render_template(
        "index.html",
        products=products,
        categories=categories,
        customer=customer,
        cart_count=cart_count,
    )


@app.route("/products")
def products_list():
    query = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    if query:
        products = store.search_products(query)
    elif cat:
        products = store.get_products_by_category(cat)
    else:
        products = store.get_active_products()
    customer = get_customer()
    cart_count = session.get("cart_count", 0)
    return render_template(
        "products.html",
        products=products,
        query=query,
        selected_category=cat,
        categories=store.categories,
        customer=customer,
        cart_count=cart_count,
    )


@app.route("/product/<product_id>")
def product_detail(product_id):
    try:
        product = store.get_product(product_id)
    except Exception:
        flash("Product not found.", "error")
        return redirect(url_for("products_list"))
    customer = get_customer()
    cart_count = session.get("cart_count", 0)
    return render_template(
        "product_detail.html",
        product=product,
        customer=customer,
        cart_count=cart_count,
    )


@app.route("/cart")
def cart_view():
    cart_items = session.get("cart", {})
    items = []
    subtotal = 0.0
    for pid, qty in cart_items.items():
        try:
            p = store.get_product(pid)
            line_total = p.calculate_price(qty)
            items.append({
                "product": p,
                "quantity": qty,
                "line_total": line_total,
            })
            subtotal += line_total
        except Exception:
            pass
    subtotal = round(subtotal, 2)
    customer = get_customer()
    customer_discount = customer.calculate_discount(subtotal) if customer else 0
    cart_count = sum(cart_items.values())
    session["cart_count"] = cart_count
    return render_template(
        "cart.html",
        items=items,
        subtotal=subtotal,
        customer_discount=customer_discount,
        total=max(round(subtotal - customer_discount, 2), 0),
        customer=customer,
        cart_count=cart_count,
    )


@app.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = request.form.get("product_id", "")
    qty = int(request.form.get("quantity", 1))
    if qty < 1:
        qty = 1
    cart = session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + qty
    session["cart"] = cart
    session["cart_count"] = sum(cart.values())
    flash(f"Added {qty} item(s) to cart.", "success")
    return redirect(request.referrer or url_for("cart_view"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    product_id = request.form.get("product_id", "")
    qty = int(request.form.get("quantity", 1))
    cart = session.get("cart", {})
    if qty <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = qty
    session["cart"] = cart
    session["cart_count"] = sum(cart.values())
    flash("Cart updated.", "success")
    return redirect(url_for("cart_view"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    product_id = request.form.get("product_id", "")
    cart = session.get("cart", {})
    cart.pop(product_id, None)
    session["cart"] = cart
    session["cart_count"] = sum(cart.values())
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart_view"))


@app.route("/customer/select", methods=["POST"])
def customer_select():
    ctype = request.form.get("customer_type", "regular")
    name = request.form.get("name", "").strip() or "Guest User"
    email = request.form.get("email", "").strip() or "guest@example.com"
    if ctype == "premium":
        c = PremiumCustomer(name, email)
    elif ctype == "business":
        c = BusinessCustomer(name, email, company=request.form.get("company", ""))
    else:
        c = RegularCustomer(name, email)
    customers[c.user_id] = c
    session["customer_id"] = c.user_id
    flash(f"Switched to {ctype.title()} Customer: {name}", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    customer = ensure_customer()
    cart_items = session.get("cart", {})
    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart_view"))

    if request.method == "POST":
        delivery_type = request.form.get("delivery", "standard")
        promo_code = request.form.get("promo_code", "").strip().upper()
        payment_type = request.form.get("payment", "credit_card")

        if delivery_type == "express":
            delivery = ExpressDelivery()
        elif delivery_type == "same_day":
            delivery = SameDayDelivery()
        else:
            delivery = StandardDelivery()

        promo = discounts.get(promo_code)

        order = Order(customer, delivery, promotional_discount=promo)

        for pid, qty in cart_items.items():
            try:
                p = store.get_product(pid)
                order.add_item(p, qty)
            except Exception as e:
                flash(f"Error adding {pid}: {e}", "error")
                return redirect(url_for("cart_view"))

        try:
            order.confirm()
        except EmptyOrderError:
            flash("Cannot confirm empty order.", "error")
            return redirect(url_for("cart_view"))
        except InsufficientStockError as e:
            flash(str(e), "error")
            return redirect(url_for("cart_view"))

        if payment_type == "credit_card":
            card_num = request.form.get("card_number", "4111111111111111")
            card_name = request.form.get("card_name", customer.name)
            card_exp = request.form.get("card_expiry", "12/27")
            try:
                payment = CreditCard(card_num, card_name, card_exp)
            except Exception:
                payment = CreditCard("4111111111111111", customer.name, "12/27")
        elif payment_type == "bank_transfer":
            acc = request.form.get("bank_account", "12345678")
            bank = request.form.get("bank_name", "Default Bank")
            payment = BankTransfer(acc, bank)
        else:
            payment = DigitalWallet(
                "W001", customer.name, 5000.0
            )

        order.set_payment(payment)
        try:
            order.pay()
        except Exception as e:
            flash(f"Payment failed: {e}", "error")
            orders[order.order_id] = order
            return redirect(url_for("order_detail", order_id=order.order_id))

        orders[order.order_id] = order
        customer.add_order(order)
        session["cart"] = {}
        session["cart_count"] = 0
        flash(f"Order #{order.order_id} placed successfully! Total: ${order.total:.2f}", "success")
        return redirect(url_for("order_detail", order_id=order.order_id))

    items = []
    subtotal = 0.0
    for pid, qty in cart_items.items():
        try:
            p = store.get_product(pid)
            items.append({"product": p, "quantity": qty, "line_total": p.calculate_price(qty)})
            subtotal += p.calculate_price(qty)
        except Exception:
            pass
    subtotal = round(subtotal, 2)
    cust_disc = customer.calculate_discount(subtotal)

    return render_template(
        "checkout.html",
        items=items,
        subtotal=subtotal,
        customer_discount=cust_disc,
        total=max(round(subtotal - cust_disc, 2), 0),
        customer=customer,
        cart_count=sum(cart_items.values()),
    )


@app.route("/orders")
def orders_list():
    customer = get_customer()
    all_orders = list(orders.values())
    all_orders.sort(key=lambda o: o.created_at, reverse=True)
    cart_count = session.get("cart_count", 0)
    return render_template(
        "orders.html",
        orders=all_orders,
        customer=customer,
        cart_count=cart_count,
    )


@app.route("/order/<order_id>")
def order_detail(order_id):
    order = orders.get(order_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders_list"))
    customer = get_customer()
    cart_count = session.get("cart_count", 0)
    invoice = None
    try:
        if order.items:
            invoice = Invoice(order)
    except Exception:
        pass
    return render_template(
        "order_detail.html",
        order=order,
        invoice=invoice,
        customer=customer,
        cart_count=cart_count,
    )


@app.route("/order/<order_id>/action", methods=["POST"])
def order_action(order_id):
    order = orders.get(order_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders_list"))

    action = request.form.get("action", "")

    try:
        if action == "process":
            order.process()
            flash("Order is now being processed.", "success")
        elif action == "ship":
            order.ship()
            flash("Order shipped!" if order.status == OrderStatus.SHIPPED else "Order delivered (digital)!", "success")
        elif action == "deliver":
            order.deliver()
            flash("Order delivered!", "success")
        elif action == "cancel":
            order.cancel()
            flash("Order cancelled.", "success")
        elif action == "refund":
            order.refund()
            flash("Order refunded.", "success")
    except (InvalidOrderStateError, EmptyOrderError, ECommerceError) as e:
        flash(f"Action failed: {e}", "error")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/admin")
def admin_dashboard():
    customer = get_customer()
    all_orders = list(orders.values())
    total_revenue = sum(o.total for o in all_orders if o.status in (
        OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED
    ))
    cart_count = session.get("cart_count", 0)
    return render_template(
        "admin.html",
        store=store,
        orders=all_orders,
        customers=list(customers.values()),
        total_revenue=round(total_revenue, 2),
        customer=customer,
        cart_count=cart_count,
    )


@app.template_filter("status_color")
def status_color(status):
    colors = {
        "CREATED": "#6c757d",
        "CONFIRMED": "#0d6efd",
        "PAID": "#0dcaf0",
        "PROCESSING": "#fd7e14",
        "SHIPPED": "#6f42c1",
        "DELIVERED": "#198754",
        "CANCELLED": "#dc3545",
        "REFUNDED": "#ffc107",
    }
    return colors.get(str(status), "#6c757d")


@app.template_filter("product_type_icon")
def product_type_icon(product):
    ptype = product.product_type().value
    icons = {"PHYSICAL": "📦", "DIGITAL": "💻", "SUBSCRIPTION": "🔄"}
    return icons.get(ptype, "📦")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
