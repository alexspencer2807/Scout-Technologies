// cart.js
document.addEventListener("DOMContentLoaded", () => {
  const cartIcon = document.getElementById("cartIcon");
  const cartDropdown = document.getElementById("cartDropdown");
  const cartItemsEl = document.getElementById("cartItems");
  const cartCount = document.getElementById("cartCount");
  const cartTotal = document.getElementById("cartTotal");
  const cartCheckoutBtn = document.getElementById("cartCheckoutBtn");

  let cart = JSON.parse(localStorage.getItem("cart") || "[]");

  const saveCart = () => localStorage.setItem("cart", JSON.stringify(cart));

  function renderCartDropdown() {
    cartItemsEl.innerHTML = "";
    let total = 0, count = 0;

    cart.forEach((item, index) => {
      total += item.price * item.quantity;
      count += item.quantity;
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="cart-item">
          <img src="${item.image}" class="cart-item-img" style="width:40px;height:40px;border-radius:4px;margin-right:8px;">
          <div class="cart-item-details">
            <strong>${item.name}</strong>
            <span>Qty: ${item.quantity}</span>
            <span>$${(item.price * item.quantity).toFixed(2)}</span>
          </div>
          <button class="removeBtn" data-index="${index}">&times;</button>
        </div>`;
      cartItemsEl.appendChild(li);
    });

    cartCount.textContent = count;
    cartTotal.textContent = total.toFixed(2);
  }

  cartItemsEl.addEventListener("click", e => {
    if (e.target.classList.contains("removeBtn")) {
      cart.splice(parseInt(e.target.dataset.index), 1);
      saveCart();
      renderCartDropdown();
    }
  });

  // Add-to-cart buttons
  document.querySelectorAll(".product-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.name;
      const price = parseFloat(btn.dataset.price);
      const image = btn.dataset.image;
      if (!name || isNaN(price) || !image) return;

      const existing = cart.find(i => i.name === name);
      if (existing) existing.quantity++;
      else cart.push({ name, price, image, quantity: 1 });

      saveCart();
      renderCartDropdown();
    });
  });

  // Dropdown toggle
  cartIcon.addEventListener("click", e => {
    e.stopPropagation();
    cartDropdown.classList.toggle("show");
  });
  document.addEventListener("click", e => {
    if (!cartDropdown.contains(e.target) && !cartIcon.contains(e.target)) 
      cartDropdown.classList.remove("show");
  });

  // Checkout button
  cartCheckoutBtn?.addEventListener("click", async () => {
    try {
      await fetch("/notify-checkout", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ name:"Cart User", cart, action:"Cart Checkout Button" })
      });
      window.location.href = "/checkout";
    } catch {
      window.location.href = "/checkout";
    }
  });

  renderCartDropdown();
});