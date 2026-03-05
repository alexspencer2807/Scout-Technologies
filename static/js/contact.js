// contact.js with toast notifications
document.addEventListener("DOMContentLoaded", () => {
  const contactForm = document.getElementById("contactForm");

  contactForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(contactForm);
    const data = {
      name: formData.get("name"),
      email: formData.get("email"),
      message: formData.get("message")
    };

    try {
      const response = await fetch("/notify-contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await response.json();
      if (result.ok) {
        notify("Message Sent!", "Your contact form message was sent successfully.");
        contactForm.reset();
      } else {
        notify("Error", "Failed to send message. Please try again.");
      }
    } catch (err) {
      console.error("Contact form error:", err);
      notify("Error", "An unexpected error occurred. Please try again later.");
    }
  });
});