(function () {
  function ensureContainer() {
    let c = document.querySelector('.site-notification-container');
    if (!c) {
      c = document.createElement('div');
      c.className = 'site-notification-container';
      document.body.appendChild(c);
    }
    return c;
  }

  function showToast(title, text, timeout = 4000) {
    const container = ensureContainer();
    const toast = document.createElement('div');
    toast.className = 'site-toast';
    toast.innerHTML = `
      <strong class="site-toast-title">${title}</strong>
      <div class="site-toast-body">${text}</div>
    `;
    container.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('visible'));

    setTimeout(() => {
      toast.classList.remove('visible');
      setTimeout(() => toast.remove(), 300);
    }, timeout);
  }

  function notify(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body: message });
    } else {
      showToast(title, message);
    }
  }

  window.notify = notify;
})();
