import os
import ssl
import smtplib
from flask import Blueprint, request, jsonify, current_app

notify_bp = Blueprint("notify", __name__)

def send_email(subject: str, body: str, to_addr: str = None):
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", "465"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    from_addr = os.getenv("EMAIL_FROM", user)
    to_addr = to_addr or os.getenv("EMAIL_TO")

    if not (host and port and user and password and to_addr):
        current_app.logger.error("Email not sent — missing email configuration")
        return False

    msg = f"From: {from_addr}\r\nTo: {to_addr}\r\nSubject: {subject}\r\n\r\n{body}"

    try:
        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(user, password)
                server.sendmail(from_addr, [to_addr], msg)
        else:
            with smtplib.SMTP(host, port) as server:
                server.starttls(context=context)
                server.login(user, password)
                server.sendmail(from_addr, [to_addr], msg)
        current_app.logger.info("Email sent to %s (subject=%s)", to_addr, subject)
        return True
    except Exception as e:
        current_app.logger.exception("Failed to send email: %s", e)
        return False

def _extract_secret_from_header():
    """
    Returns the token from either X-Notify-Secret or Authorization header.
    Accepts 'Bearer <token>' and tolerates extra whitespace.
    """
    raw = request.headers.get("X-Notify-Secret") or request.headers.get("Authorization") or ""
    raw = raw.strip()
    if not raw:
        return ""
    # If Authorization: Bearer <token>
    parts = raw.split(None, 1)  # split on whitespace, max 2 parts
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return raw


@notify_bp.route("/notify-checkout", methods=["POST"])
def notify_checkout():
    data = request.get_json() or {}
    name = data.get("name", "Customer")
    cart_items = data.get("cart", [])
    action = data.get("action", "Checkout")

    # Build item list
    items_list = "\n".join([f"- {item['name']} x{item['quantity']}" for item in cart_items]) or "No items"

    # Email body
    body = f"User {name} clicked '{action}' and has ordered the following items:\n{items_list}"

    # Send to host
    host_email = os.getenv("EMAIL_TO")
    send_email(subject=f"Order Notification: {action}", body=body, to_addr=host_email)

    return jsonify({"ok": True})