from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- PAGES ---------------- #
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/products")
def products():
    return render_template("products.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        card_number = request.form.get("card_number")
        exp_date = request.form.get("exp_date")
        cvv = request.form.get("cvv")
        # In a real app, you'd process payment here
        flash("Payment processed successfully!", "success")
        return redirect(url_for("home"))
    return render_template("checkout.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)