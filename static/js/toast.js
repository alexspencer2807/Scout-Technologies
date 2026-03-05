function showToast(title, message) {
    const container = document.getElementById('notificationContainer');
    const toast = document.createElement('div');
    toast.className = 'site-toast visible';
    toast.innerHTML = `<span class="site-toast-title">${title}</span>
                       <span class="site-toast-body">${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000); // auto remove after 4 sec
}