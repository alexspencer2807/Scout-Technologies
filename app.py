import os
import json
import stripe
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from notify import notify_bp  # <-- contains both /notify-checkout & /webhook

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
app.register_blueprint(notify_bp)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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
    return render_template("checkout.html", stripe_public_key=os.getenv("STRIPE_PUBLIC_KEY"))

@app.route("/contact")
def contact():
    return render_template("contact.html")

# --- Create PaymentIntent ---
@app.route("/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.json
    cart = data.get("cart", [])
    shipping = data.get("shipping", {})
    customer_email = data.get("email")

    subtotal = sum(float(i["price"]) * int(i["quantity"]) for i in cart)
    total_items = sum(int(i["quantity"]) for i in cart)

    discount_amount = 0
    discount_label = ""

    if total_items >= 5:
        discount_amount = subtotal * 0.20
        discount_label = "5+ Item Bundle Discount (20% Off)"

    elif total_items >= 3:
        discount_amount = subtotal * (1 - (5000/6000))
        discount_label = "3 Item Bundle Discount (~16.7% Off)"

    discounted_total = subtotal - discount_amount
    shipping_cost = 0
    total_amount = discounted_total + shipping_cost
    amount_cents = int(total_amount * 100)
    items_summary = ", ".join([f"{i['name']} x{i['quantity']}" for i in cart])

    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="jmd",
        payment_method_types=["card"],
        shipping=shipping,
        metadata={
            "items": items_summary,
            "items_count": total_items,
            "discount_label": discount_label,
            "discount_amount": discount_amount,   # IMPORTANT
            "final_price": total_amount,
            "customer_email": customer_email,
            "cart_json": json.dumps(cart)
        }
    )
    return jsonify({"client_secret": intent.client_secret})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)