document.addEventListener("DOMContentLoaded", async () => {
  const cart = JSON.parse(localStorage.getItem("cart")) || [];
  const paymentForm = document.getElementById("payment-form");
  const paymentMessage = document.getElementById("payment-message");

  const stripe = Stripe("pk_test_51T6xjBLsMXS9E6aFTuZMBsCrwxlOctoyuGOeEYtHrMACpO9xx9w8s2yuCV5GdDB0juEsIGmtvHWG1M5cdw3jZQ5G00EBhhHfdw");
  const elements = stripe.elements();
  const cardElement = elements.create("card");
  cardElement.mount("#card-element");

  paymentForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // 1️⃣ Create PaymentIntent
    const res = await fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart })
    });
    const data = await res.json();
    if (data.error) {
      paymentMessage.textContent = data.error;
      paymentMessage.style.color = "red";
      return;
    }

    // 2️⃣ Confirm payment
    const { error, paymentIntent } = await stripe.confirmCardPayment(data.client_secret, {
      payment_method: {
        card: cardElement,
        billing_details: {
          name: paymentForm.name.value,
          email: paymentForm.email.value
        }
      }
    });

    if (error) {
      paymentMessage.textContent = error.message;
      paymentMessage.style.color = "red";
      return;
    }

    if (paymentIntent && paymentIntent.status === "succeeded") {
      paymentMessage.textContent = "Payment successful!";
      paymentMessage.style.color = "green";

      // 3️⃣ Send email notification
      await fetch("/notify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Notify-Secret": "a-strong-secret"  // match your .env
        },
        body: JSON.stringify({
          subject: "New Paid Order",
          message: `New order by ${paymentForm.name.value} (${paymentForm.email.value})\n\nItems:\n${cart.map(i => `${i.name} x${i.quantity} - $${i.price}`).join("\n")}\n\nTotal: $${cart.reduce((a,b)=>a+b.price*b.quantity,0).toFixed(2)}`
        })
      });

      // 4️⃣ Clear cart if you want
      localStorage.removeItem("cart");
    }
  });
});
document.addEventListener("DOMContentLoaded", async () => {
  const cart = JSON.parse(localStorage.getItem("cart")) || [];
  const cartItemsDiv = document.getElementById("cartItemsSummary");
  let totalAmount = 0;

  if (cartItemsDiv) {
    cartItemsDiv.innerHTML = cart.map(item => {
      totalAmount += item.price * item.quantity;
      return `
        <p>
          <strong>${item.name}</strong> x ${item.quantity} - $${(item.price * item.quantity).toFixed(2)}
        </p>
      `;
    }).join("");

    cartItemsDiv.innerHTML += `<p><strong>Total: $${totalAmount.toFixed(2)}</strong></p>`;
  }

  // --- Stripe integration ---
  const stripe = Stripe("pk_test_51T6xjBLsMXS9E6aFTuZMBsCrwxlOctoyuGOeEYtHrMACpO9xx9w8s2yuCV5GdDB0juEsIGmtvHWG1M5cdw3jZQ5G00EBhhHfdw");
  const elements = stripe.elements();
  const cardElement = elements.create("card");
  cardElement.mount("#card-element");

  const paymentForm = document.getElementById("payment-form");
  const paymentMessage = document.getElementById("payment-message");

  paymentForm.addEventListener("submit", async e => {
    e.preventDefault();

    if (cart.length === 0) {
      paymentMessage.textContent = "Your cart is empty!";
      return;
    }

    const res = await fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart })
    });

    const data = await res.json();
    if (data.error) {
      paymentMessage.textContent = data.error;
      return;
    }

    const { error } = await stripe.confirmCardPayment(data.client_secret, {
      payment_method: {
        card: cardElement,
        billing_details: {
          name: paymentForm.name.value,
          email: paymentForm.email.value
        }
      }
    });

    if (error) {
      paymentMessage.textContent = error.message;
    } else {
      paymentMessage.textContent = "Payment successful!";

      // Send notification email
      fetch("/notify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Notify-Secret": "a-strong-secret"
        },
        body: JSON.stringify({
          subject: "New Checkout",
          message: `Order by ${paymentForm.name.value} (${paymentForm.email.value})\n\nItems:\n${cart.map(i => `${i.name} x ${i.quantity}`).join("\n")}`
        })
      });

      // Clear cart after payment
      localStorage.removeItem("cart");
      cartItemsDiv.innerHTML = "<p>Your cart is now empty.</p>";
      document.getElementById("cartCount").textContent = "0";
    }
  });
});