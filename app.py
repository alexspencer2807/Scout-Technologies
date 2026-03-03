import os, stripe, json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from notify import notify_bp, send_email

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.register_blueprint(notify_bp)

stripe.api_key = os.getenv("stripe_secret_key")
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
# --- Stripe PaymentIntent ---
@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.get_json()
    cart_items = data.get("cart", [])
    total_cents = int(sum(item["price"] * item["quantity"] for item in cart_items) * 100)
    try:
        intent = stripe.PaymentIntent.create(
            amount=total_cents,
            currency="usd",
            automatic_payment_methods={"enabled": True}
        )
        return jsonify({"client_secret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- Cart dropdown email trigger ---
@app.route("/notify-checkout", methods=["POST","GET"])
def notify_checkout():
    data = request.get_json()
    name = data.get("name", "Unknown")
    email = data.get("email", "Unknown")
    cart_items = data.get("cart", [])
    items_list = "\n".join([f"- {i['name']} x{i['quantity']}" for i in cart_items])
    body = f"{name} ({email}) clicked Checkout in the cart dropdown.\nItems:\n{items_list}"
    send_email(subject="Cart Checkout Clicked", body=body)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)