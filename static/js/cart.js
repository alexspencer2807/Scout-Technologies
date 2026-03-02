document.addEventListener("DOMContentLoaded", function () {
  const cartIcon = document.getElementById("cartIcon");
  const cartDropdown = document.getElementById("cartDropdown");
  const cartItems = document.getElementById("cartItems");
  const cartCount = document.getElementById("cartCount");
  const cartTotal = document.getElementById("cartTotal");

  let cart = JSON.parse(localStorage.getItem("cart")) || [];

  function saveCart() {
    localStorage.setItem("cart", JSON.stringify(cart));
  }

  function renderCart() {
    if (!cartItems) return;

    // Save dropdown state
    const isOpen = cartDropdown.classList.contains("show");

    cartItems.innerHTML = "";
    let total = 0;
    let itemCount = 0;

    cart.forEach((item, index) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="cart-item">
          <img src="${item.image}" class="cart-item-img">
          <div class="cart-item-details">
            <strong>${item.name}</strong>
            <span>Qty: ${item.quantity}</span>
            <span>$${(item.price * item.quantity).toFixed(2)}</span>
          </div>
          <button class="removeBtn" data-index="${index}">&times;</button>
        </div>
      `;
      cartItems.appendChild(li);
      total += item.price * item.quantity;
      itemCount += item.quantity;
    });

    cartCount.textContent = itemCount;
    cartTotal.textContent = total.toFixed(2);

    // Reattach remove buttons
    document.querySelectorAll(".removeBtn").forEach(btn => {
      btn.addEventListener("click", () => {
        const index = parseInt(btn.getAttribute("data-index"));
        cart.splice(index, 1);
        saveCart();
        renderCart();

        // Force dropdown to stay open
        cartDropdown.classList.add("show");
      });
    });

    // Restore dropdown state after rendering
    if (isOpen || cart.length > 0) {
      cartDropdown.classList.add("show");
    } else {
      cartDropdown.classList.remove("show");
    }
  }

  // Toggle cart dropdown
  if (cartIcon) {
    cartIcon.addEventListener("click", e => {
      e.stopPropagation();
      cartDropdown.classList.toggle("show");
    });
  }

  // Close cart if clicking outside
  document.addEventListener("click", e => {
    if (!cartDropdown.contains(e.target) && !cartIcon.contains(e.target)) {
      cartDropdown.classList.remove("show");
    }
  });

  // Add to cart buttons
  document.querySelectorAll(".product-btn").forEach(button => {
    button.addEventListener("click", () => {
      const name = button.dataset.name;
      const price = parseFloat(button.dataset.price);
      const image = button.dataset.image;

      const existing = cart.find(i => i.name === name);
      if (existing) {
        existing.quantity += 1;
      } else {
        cart.push({ name, price, image, quantity: 1 });
      }
      saveCart();
      renderCart();

      // Keep dropdown open
      cartDropdown.classList.add("show");
    });
  });

  renderCart();
});