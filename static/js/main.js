document.addEventListener('DOMContentLoaded', () => {
  // Function to show toast notification
  function showNotification(message) {
    const notif = document.createElement('div');
    notif.textContent = message;
    notif.style.position = 'fixed';
    notif.style.bottom = '20px';
    notif.style.right = '20px';
    notif.style.background = '#c2b8a3';
    notif.style.color = '#000';
    notif.style.padding = '10px 20px';
    notif.style.borderRadius = '8px';
    notif.style.boxShadow = '0 4px 10px rgba(0,0,0,0.3)';
    notif.style.zIndex = '9999';
    notif.style.opacity = '0';
    notif.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(notif);

    // Fade in
    requestAnimationFrame(() => {
      notif.style.opacity = '1';
    });

    // Remove after 3 seconds
    setTimeout(() => {
      notif.style.opacity = '0';
      setTimeout(() => notif.remove(), 300);
    }, 3000);
  }

  // Add click listeners to product buttons
  document.querySelectorAll('.product-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const productName = btn.dataset.name || "Item";
      showNotification(`${productName} added to cart!`);
    });
  });
});
// either in templates/checkout.html bottom or static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('#checkout-form');
  if (!form) return;
  form.addEventListener('submit', function (e) {
    // show immediate feedback; server-side will still process
    if (window.notify) window.notify('Order Processing', 'Thanks — your order is being placed');
    // allow form to submit normally
  });
});