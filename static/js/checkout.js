document.addEventListener("DOMContentLoaded", async () => {
  const cartContainer = document.getElementById("cartItemsSummary");
  let cart = JSON.parse(localStorage.getItem("cart") || "[]");

  // --- Cart summary ---
  if (cart.length) {
    let subtotal = 0;
    const rows = cart.map(i => {
      const line = i.price * i.quantity;
      subtotal += line;
      return `
        <li style="display:flex; align-items:center; justify-content:space-between; padding:8px 0; border-bottom:1px solid #eee;">
          <div style="display:flex; align-items:center; gap:10px;">
            <img src="${i.image}" alt="${i.name}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;">
            <span>${i.name} x${i.quantity}</span>
          </div>
          <span>$${line.toFixed(2)}</span>
        </li>`;
    }).join('');

    const shipping = 2.99;
    const total = subtotal + shipping;

    cartContainer.innerHTML = `
      <ul style="list-style:none;padding:0;margin:0;">${rows}</ul>
      <p style="text-align:right;margin-top:8px;"><strong>Subtotal: $${subtotal.toFixed(2)}</strong></p>
      <p style="text-align:right;margin:4px 0;"><strong>Shipping: $${shipping.toFixed(2)}</strong></p>
      <p style="text-align:right;font-weight:bold;font-size:1.1em;margin-top:6px;">Total: $${total.toFixed(2)}</p>`;
  } else {
    cartContainer.innerHTML = "<p style='text-align:center;color:#888;'>Your cart is empty</p>";
  }

  // --- Notify dropdown checkout ---
  async function notifyCartClick(buttonName) {
    try {
      await fetch("/notify-checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Cart User", email: "N/A", cart, action: buttonName })
      });
    } catch (err) {
      console.error(err);
      notify("Error", "Failed to send cart notification.");
    }
  }

  const cartCheckoutBtn = document.getElementById("cartCheckoutBtn");
  cartCheckoutBtn.addEventListener("click", async () => {
    await notifyCartClick("Checkout Dropdown Button");
    window.location.href = "/checkout";
  });

  // --- Stripe Setup ---
  if (typeof Stripe === "undefined") {
    console.error("Stripe.js not loaded");
    notify("Error", "Stripe.js is not loaded.");
    return;
  }

  const stripe = Stripe(stripePublicKey);
  const elements = stripe.elements();

  const addressElement = elements.create("address", { mode: "shipping", allowedCountries: ["US"] });
  addressElement.mount("#address-element");

  const cardElement = elements.create("card");
  cardElement.mount("#card-element");

  const form = document.getElementById("payment-form");
  let shippingData = null;

  // --- Listen for shipping changes ---
  addressElement.on("change", event => {
    if (event.complete) shippingData = event.value;
  });

  // --- Handle Payment ---
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const name = email || "Customer";

    if (!shippingData) {
      notify("Shipping Required", "Please complete your shipping address.", "error");
      return;
    }

    // Notify backend
    try {
      await fetch("/notify-checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, cart, shipping: shippingData, action: "Pay Now Button" })
      });
    } catch (err) {
      console.error(err);
      notify("Error", "Failed to notify backend.");
    }

    // Create PaymentIntent on server with shipping
    let data;
    try {
      const res = await fetch("/create-payment-intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cart, shipping: shippingData, email })
      });
      data = await res.json();
      if (data.error) {
        notify("Payment Error", data.error, "error");
        return;
      }
    } catch (err) {
      console.error(err);
      notify("Error", "Failed to create payment intent.", "error");
      return;
    }

    // Confirm payment (shipping is already saved in PaymentIntent)
    try {
      const { error, paymentIntent } = await stripe.confirmCardPayment(data.client_secret, {
        payment_method: {
          card: cardElement,
          billing_details: { name, email }
        }
      });

      if (error) {
        notify("Payment Failed", error.message, "error");
        return;
      }

      if (paymentIntent.status === "succeeded") {
        notify("Payment Successful", "Your payment was processed successfully.", "success");
        localStorage.removeItem("cart");
        setTimeout(() => window.location.href = "/", 1500);
      }
    } catch (err) {
      console.error(err);
      notify("Error", "Payment processing failed.", "error");
    }
  });
});