document.addEventListener("DOMContentLoaded", () => {
  const cartIcon = document.getElementById("cartIcon");
  const cartDropdown = document.getElementById("cartDropdown");
  const cartItemsEl = document.getElementById("cartItems");
  const cartCount = document.getElementById("cartCount");
  const cartTotal = document.getElementById("cartTotal");
  const cartCheckoutBtn = document.getElementById("cartCheckoutBtn");

  let cart = JSON.parse(localStorage.getItem("cart")) || [];

  const saveCart = () => localStorage.setItem("cart", JSON.stringify(cart));

  const renderCart = () => {
    cartItemsEl.innerHTML = "";
    let total = 0, count = 0;
    cart.forEach((item, index) => {
      total += item.price * item.quantity;
      count += item.quantity;
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="cart-item">
          <img src="${item.image}" class="cart-item-img">
          <div class="cart-item-details">
            <strong>${item.name}</strong>
            <span>Qty: ${item.quantity}</span>
            <span>$${(item.price*item.quantity).toFixed(2)}</span>
          </div>
          <button class="removeBtn" data-index="${index}">&times;</button>
        </div>`;
      cartItemsEl.appendChild(li);
    });
    cartCount.textContent = count;
    cartTotal.textContent = total.toFixed(2);
  };

  cartItemsEl.addEventListener("click", e => {
    if(e.target.classList.contains("removeBtn")){
      cart.splice(parseInt(e.target.dataset.index),1);
      saveCart(); renderCart();
    }
  });

  document.querySelectorAll(".product-btn").forEach(btn => {
    btn.addEventListener("click", ()=>{
      const name=btn.dataset.name, price=parseFloat(btn.dataset.price), image=btn.dataset.image;
      if(!name || isNaN(price) || !image) return;
      const existing = cart.find(i=>i.name===name);
      existing ? existing.quantity++ : cart.push({name,price,image,quantity:1});
      saveCart(); renderCart();
    });
  });

  cartIcon.addEventListener("click", e => {
    e.stopPropagation(); cartDropdown.classList.toggle("show");
  });
  document.addEventListener("click", e=>{
    if(!cartDropdown.contains(e.target)&&!cartIcon.contains(e.target)) cartDropdown.classList.remove("show");
  });

  // --- Dropdown checkout button email ---
  cartCheckoutBtn.addEventListener("click", async ()=>{
    await fetch("/notify-checkout", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({name:"Cart User",email:"N/A",cart})
    });
    window.location.href="/checkout";
  });

  renderCart();
});