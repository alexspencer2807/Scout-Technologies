(function () {
  const notifyServer = async (subject, message) => {
    try {
        fetch('/notify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Notify-Secret': 'a-strong-secret'
        },
        body: JSON.stringify({ subject: 'New order', message: 'Order details...' })
        });
    } catch (e) {
      console.warn('server notify failed', e);
    }
  };

  document.addEventListener('click', function (e) {
    const btn = e.target.closest && e.target.closest('.add-to-cart');
    if (!btn) return;
    const name = btn.dataset.name || btn.getAttribute('data-name') || 'Item';
    const qty = btn.dataset.qty || 1;
    if (window.notify) window.notify('Added to Cart', `${name} (x${qty}) added to cart`);
    // send server email notification (optional)
    notifyServer('Item added to cart', `${name} (x${qty}) was added to cart`);
  });

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('#checkout-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      if (window.notify) window.notify('Order Processing', 'Thanks — your order is being placed');
      // If your checkout uses AJAX, send the final email on success instead of on submit:
      notifyServer('New order placed', 'A customer submitted an order. Please check the admin panel.');
    });
  });
})();