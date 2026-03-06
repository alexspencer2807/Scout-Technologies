import os, stripe, json
from flask import Flask, render_template, request, jsonify, url_for, redirect
from dotenv import load_dotenv
from notify import notify_bp, send_email
import smtplib
from email.mime.text import MIMEText

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.register_blueprint(notify_bp)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
HOST_EMAIL = os.getenv("EMAIL_TO")

print("Stripe Secret Key Loaded:", stripe.api_key)

# --- Pages ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/products")
def products():
    return render_template("products.html")

@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/shipping")
def shipping():
    return render_template("shipping.html")


@app.route("/checkout")
def checkout():
    return render_template(
        "checkout.html",
        stripe_public_key=os.getenv("STRIPE_PUBLIC_KEY")
    )

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/notify-checkout", methods=["POST"])
def notify_checkout():
    data = request.get_json()
    name = data.get("name", "Unknown")
    email = data.get("email", "Unknown")
    cart_items = data.get("cart", [])
    shipping = data.get("shipping", {})

    items_list = "\n".join([f"- {i['name']} x{i['quantity']}" for i in cart_items])

    # Format shipping nicely
    shipping_text = ""
    if shipping:
        addr = shipping.get("address", {})
        shipping_text = f"""
Shipping Info:
Name: {shipping.get('name')}
Phone: {shipping.get('phone', '')}
Address:
{addr.get('line1','')} {addr.get('line2','')}
{addr.get('city','')}, {addr.get('state','')} {addr.get('postal_code','')}
{addr.get('country','')}
"""

    body = f"{name} ({email}) clicked Checkout.\nItems:\n{items_list}\n{shipping_text}"

    send_email(subject="Cart Checkout Clicked", body=body)
    return jsonify({"ok": True})

# --- Stripe PaymentIntent ---
@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.json
    cart = data.get("cart", [])
    shipping = data.get("shipping")

    subtotal = 0
    total_items = 0

    for item in cart:
        price = float(item["price"])
        qty = int(item["quantity"])
        subtotal += price * qty
        total_items += qty

    # --- Bundle Discounts ---
    discount_label = "none"
    total = subtotal

    if total_items >= 5:
        total = subtotal * 0.8  # 20% off
        discount_label = "5_item_bundle"
    elif total_items >= 3:
        total = subtotal * (5000/6000)  # 16.67% off
        discount_label = "3_item_bundle"

    total = max(total, 0)  # Ensure total is non-negative
   
 # Convert to cents for Stripe
    amount = int(total * 100)

    # Create short item summary for Stripe metadata
    items_summary = ", ".join([f"{i['name']} x{i['quantity']}" for i in cart])

    payment_intent = stripe.PaymentIntent.create(
        amount=amount,
        currency="jmd",
        payment_method_types=["card"],
        shipping={
            "name": shipping.get("name"),
            "phone": shipping.get("phone", ""),
            "address": {
                "line1": shipping["address"].get("line1"),
                "line2": shipping["address"].get("line2", ""),
                "city": shipping["address"].get("city"),
                "state": shipping["address"].get("state"),
                "postal_code": shipping["address"].get("postal_code"),
                "country": shipping["address"].get("country")
            }
        },
        metadata={
            "items": items_summary,
            "items_count": total_items,
            "discount": discount_label,
            "final_price": total
        }
    )
    
    return jsonify({"client_secret": payment_intent.client_secret})

# --- Stripe Webhook for Payment Confirmation ---
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        charge = intent["charges"]["data"][0]
        customer_email = charge["billing_details"]["email"]
        customer_name = charge["billing_details"]["name"]
        amount = intent["amount_received"] / 100
        items = intent.metadata.get("items", "Unknown items")

        # Email to host
        host_body = f"""
        New Payment Received!

        Customer: {customer_name} ({customer_email})
        Amount: ${amount:.2f}

        Items:
        {items}

        Payment ID: {intent['id']}
        """
        send_email(subject="New Payment Received", body=host_body, to_addr=HOST_EMAIL)

        # Email to customer
        customer_body = f"""
Hi {customer_name},

Thank you for your order! Your payment of ${amount:.2f} was successful.

Order details:
{json.dumps(items, indent=2)}

Payment ID: {intent['id']}
"""
        send_email(subject="Order Confirmation", body=customer_body, to_addr=customer_email)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)