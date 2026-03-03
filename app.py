import os, stripe, json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from notify import notify_bp, send_email

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

@app.route("/checkout")
def checkout():
    return render_template(
        "checkout.html",
        stripe_public_key=os.getenv("STRIPE_PUBLIC_KEY")
    )
@app.route("/notify-checkout", methods=["POST"])
def notify_checkout():
    data = request.get_json()
    name = data.get("name", "Unknown")
    email = data.get("email", "Unknown")
    cart_items = data.get("cart", [])

    items_list = "\n".join([f"- {i['name']} x{i['quantity']}" for i in cart_items])
    body = f"{name} ({email}) clicked Checkout.\nItems:\n{items_list}"

    send_email(subject="Cart Checkout Clicked", body=body)
    return jsonify({"ok": True})

# --- Stripe PaymentIntent ---
@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.get_json()
    cart_items = data.get("cart", [])
    total_cents = int(sum(item["price"] * item["quantity"] for item in cart_items) * 100)

    intent = stripe.PaymentIntent.create(
        amount=total_cents,
        currency="usd",
        automatic_payment_methods={"enabled": True},
        metadata={
            "cart": json.dumps(cart_items)
        }
    )

    return jsonify({"client_secret": intent.client_secret})

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
        items = intent.metadata

        # Email to host
        host_body = f"""
New Payment Received!
Customer: {customer_name} ({customer_email})
Amount: ${amount:.2f}
Items:
{json.dumps(items, indent=2)}
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