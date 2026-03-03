document.addEventListener("DOMContentLoaded", async () => {
  // --- Load cart from localStorage ---
  let cart = JSON.parse(localStorage.getItem("cart") || "[]");

  // --- Render checkout summary ---
  const cartContainer = document.getElementById("cartItemsSummary");

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
    }[c]));
  }

  function renderCart() {
    if (!cart.length) {
      cartContainer.innerHTML = "<p>Your cart is empty</p>";
      return;
    }

    let total = 0;
    const rows = cart.map(item => {
      const line = item.price * item.quantity;
      total += line;
      return `
        <li class="checkout-item">
          <img src="${item.image}" class="cart-item-img" alt="${escapeHtml(item.name)}">
          <div class="checkout-item-details">
            <span class="checkout-item-name">${escapeHtml(item.name)}</span>
            <span class="checkout-item-qty">Qty: ${item.quantity}</span>
          </div>
          <span class="checkout-item-line">$${line.toFixed(2)}</span>
        </li>
      `;
    }).join("");

    cartContainer.innerHTML = `
      <ul class="checkout-items">${rows}</ul>
      <p class="checkout-total">Total: $${total.toFixed(2)}</p>
    `;
  }

  renderCart();

  // --- Notify function ---
  async function notifyHost(actionName) {
    try {
      await fetch("/notify-checkout", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ name: "Cart User", email: "N/A", cart, action: actionName })
      });
    } catch (err) { console.error("Notification failed:", err); }
  }

  // --- Cart Checkout Button ---
  const cartCheckoutBtn = document.getElementById("cartCheckoutBtn");
  cartCheckoutBtn.addEventListener("click", async () => {
    await notifyHost("Cart Checkout Button");
    window.location.href = "/checkout";
  });

  // --- Stripe setup ---
  if (typeof Stripe === "undefined") { console.error("Stripe.js not loaded"); return; }

  const stripe = Stripe(stripePublicKey);
  const elements = stripe.elements();

  const addressElement = elements.create("address", { mode: "shipping", allowedCountries: ["US"] });
  addressElement.mount("#address-element");

  const cardElement = elements.create("card");
  cardElement.mount("#card-element");

  const form = document.getElementById("payment-form");
  const message = document.getElementById("payment-message");

  form.addEventListener("submit", async e => {
    e.preventDefault();
    message.textContent = "Processing payment...";

    const email = document.getElementById("email").value;
    const name = email || "Customer";

    // Notify host when Pay Now clicked
    await fetch("/notify-checkout", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ name, cart, action: "Pay Now Button" })
    });

    // Create PaymentIntent
    const res = await fetch("/create-payment-intent", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({ cart })
    });
    const data = await res.json();
    if (data.error) { message.textContent = data.error; return; }

    const { error, paymentIntent } = await stripe.confirmCardPayment(data.client_secret, {
      payment_method: { card: cardElement, billing_details: { name, email } },
      shipping: addressElement.value
    });

    if (error) { message.textContent = error.message; return; }

    if (paymentIntent.status === "succeeded") {
      message.textContent = "Payment successful!";
      localStorage.removeItem("cart");
      setTimeout(() => window.location.href = "/checkout", 1500);
    }
  });
});