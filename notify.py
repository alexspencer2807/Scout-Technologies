import os
import ssl
import smtplib
import json
from flask import Blueprint, request, jsonify, current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from flask import Blueprint, request, jsonify
import os

notify_bp = Blueprint("notify", __name__)

# ---------------- EMAIL ----------------
def send_email(subject, body, to_addr, attachment_path=None):

    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", 465))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    from_addr = os.getenv("EMAIL_FROM", user)

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(attachment_path),
            )
            msg.attach(attach)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context) as server:
        server.login(user, password)
        server.send_message(msg)


# ---------------- PDF RECEIPT ----------------
def generate_pdf_receipt(customer, email, cart_items, shipping, discount=0, discount_label="", filename="receipt.pdf"):

    width, height = letter
    c = canvas.Canvas(filename, pagesize=letter)

    # Background
    c.setFillColor(colors.HexColor("#25262b"))
    c.rect(0, 0, width, height, fill=1)
    c.setFillColor(colors.HexColor("#f5f5f5"))

    # Logo
    logo_path = "static/media/Scout Videography Logo.jpg"
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            width / 2 - 90,
            height - 100,
            width=180,
            height=60,
            preserveAspectRatio=True,
        )

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 140, "Order Receipt")

    y = height - 190

    # ---------------- CUSTOMER ----------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Customer Information")
    y -= 25

    c.setFont("Helvetica", 12)

    addr = shipping.get("address") or {}

    ship_name = (shipping.get("name") or customer or "Customer").title()
    phone = shipping.get("phone") or ""

    line1 = (addr.get("line1") or "").title()
    line2 = (addr.get("line2") or "").title()
    city = (addr.get("city") or "").title()
    state = (addr.get("state") or "").upper()
    postal = addr.get("postal_code") or ""
    country = (addr.get("country") or "").title()

    c.drawString(70, y, f"{ship_name} - {phone}")
    y -= 18

    street = f"{line1} {line2}".strip()
    if street:
        c.drawString(70, y, street)
        y -= 18

    location = f"{city}, {state} {postal}".strip()
    if location:
        c.drawString(70, y, location)
        y -= 18

    if country:
        c.drawString(70, y, country)
        y -= 18

    c.drawString(70, y, f"Email: {email or 'N/A'}")

    y -= 40

    # ---------------- ITEMS ----------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Items Purchased")
    y -= 25

    # Column headers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y, "Item")
    c.drawRightString(400, y, "Qty")
    c.drawRightString(470, y, "Price")
    c.drawRightString(550, y, "Total")

    y -= 10

    # Divider line
    c.setStrokeColor(colors.grey)
    c.line(60, y, 560, y)
    y -= 20

    c.setFont("Helvetica", 12)

    subtotal = 0

    for item in cart_items:

        name = item.get("name", "Item")
        qty = int(item.get("quantity", 1))
        price = float(item.get("price", 0))

        line_total = price * qty
        subtotal += line_total

        c.drawString(70, y, name)
        c.drawRightString(400, y, str(qty))
        c.drawRightString(470, y, f"${price:.2f}")
        c.drawRightString(550, y, f"${line_total:.2f}")

        y -= 18
       
 # ---------------- TOTALS ----------------
    y -= 10

    c.setStrokeColor(colors.grey)
    c.line(350, y, 560, y)
    y -= 20

    c.setFont("Helvetica", 12)

    c.drawRightString(470, y, "Subtotal:")
    c.drawRightString(550, y, f"${subtotal:.2f}")
    y -= 18

    c.drawRightString(470, y, f"Discount ({discount_label}):")
    c.drawRightString(550, y, f"-${discount:.2f}")
    y -= 18

    total = subtotal - discount

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(470, y, "Total:")
    c.drawRightString(550, y, f"${total:.2f}")

    y -= 40

    # Footer
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Thank you for shopping with Scout Technologies!")

    c.showPage()
    c.save()

    return filename


# ---------------- CHECKOUT EMAIL ----------------
@notify_bp.route("/notify-checkout", methods=["POST"])
def notify_checkout():

    data = request.get_json() or {}

    cart_items = data.get("cart") or []
    shipping = data.get("shipping") or {}
   
    subtotal = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in cart_items)
    total_items = sum(int(i.get("quantity", 1)) for i in cart_items)

    discount = 0
    discount_label = ""

    if total_items >= 10:
        discount = subtotal * 0.20
        discount_label = "10+ Items Discount (20% Off)"
    elif total_items >= 7:
        discount = subtotal * 0.15
        discount_label = "7-9 Items Discount (15% Off)"
    elif total_items >= 5:
        discount = subtotal * 0.10
        discount_label = "5-6 Items Discount (10% Off)"
    elif total_items >= 3:
        discount = subtotal * 0.05
        discount_label = "3-4 Items Discount (5% Off)"

    name = (shipping.get("name") or "Customer").title()
    email = shipping.get("email") or data.get("email")

    pdf_path = generate_pdf_receipt(
        name,
        email,
        cart_items,
        shipping,
        discount,
        discount_label=discount_label,   # <-- pass it here
        filename=f"receipt_{name.replace(' ','_')}.pdf",
    )

    # Item list for email
    items_text = ""
    for item in cart_items:
        qty = item.get("quantity", 1)
        price = float(item.get("price", 0))
        items_text += f"{item.get('name','Item')} x{qty} - ${price * qty:.2f}\n"

    addr = shipping.get("address") or {}

    shipping_text = f"""
{name}
{addr.get("line1","")} {addr.get("line2","")}
{addr.get("city","")}, {addr.get("state","")} {addr.get("postal_code","")}
{addr.get("country","")}
Phone: {shipping.get("phone","")}
"""

    host_body = f"""
New Order Notification

Customer: {name}
Email: {email or "N/A"}

Items:
{items_text}

Shipping:
{shipping_text}
"""

    send_email(
        subject=f"New Order: {name}",
        body=host_body,
        to_addr=os.getenv("EMAIL_TO"),
        attachment_path=pdf_path,
    )

    if email:

        customer_body = f"""Hi {name},

Thank you for your order. Your receipt is attached.

Scout Technologies
"""

        send_email(
            subject="Your Order Confirmation",
            body=customer_body,
            to_addr=email,
            attachment_path=pdf_path,
        )

    return jsonify({"ok": True})


# ---------------- STRIPE WEBHOOK ----------------
@notify_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    import stripe

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        shipping = intent.get("shipping") or {}
        charge = intent["charges"]["data"][0]
        customer_name = charge["billing_details"].get("name") or shipping.get("name")
        customer_email = charge["billing_details"].get("email")

        # Get cart items from metadata
        cart_json = intent["metadata"].get("cart_json", "[]")
        cart_items = json.loads(cart_json)

        # Recalculate discount based on new tiers
        subtotal = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in cart_items)
        total_items = sum(int(i.get("quantity", 1)) for i in cart_items)

        discount_amount = 0
        discount_label = ""

        if total_items >= 10:
            discount_amount = subtotal * 0.20
            discount_label = "10+ Items Discount (20% Off)"
        elif total_items >= 7:
            discount_amount = subtotal * 0.15
            discount_label = "7-9 Items Discount (15% Off)"
        elif total_items >= 5:
            discount_amount = subtotal * 0.10
            discount_label = "5-6 Items Discount (10% Off)"
        elif total_items >= 3:
            discount_amount = subtotal * 0.05
            discount_label = "3-4 Items Discount (5% Off)"

        # Pass all relevant info to notify_checkout
        with current_app.test_request_context(
            "/notify-checkout",
            method="POST",
            json={
                "name": customer_name,
                "email": customer_email,
                "cart": cart_items,
                "shipping": shipping,
                "discount": discount_amount,
                "discount_label": discount_label
            },
        ):
            print("STRIPE METADATA:", intent["metadata"])
            notify_checkout()

    return jsonify({"status": "success"}), 200

# notify.py
@notify_bp.route("/notify-contact", methods=["POST"])
def notify_contact():
    data = request.get_json() or {}
    name = data.get("name", "N/A")
    email = data.get("email", "N/A")
    message = data.get("message", "")

    try:
        send_email(
            subject=f"New Contact Form Message from {name}",
            body=f"Name: {name}\nEmail: {email}\nMessage:\n{message}",
            to_addr=os.getenv("EMAIL_TO")
        )
        # Return JSON with ok=True so your toast knows it succeeded
        return jsonify({"ok": True}), 200
    except Exception as e:
        # Return error details in JSON so toast can show a message
        return jsonify({"ok": False, "error": str(e)}), 500