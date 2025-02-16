from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from urllib.parse import urlparse

app = Flask(__name__, template_folder="templates")

# Parsujemy DATABASE_URL, aby naprawić błąd związany z 'port'
url = urlparse(os.getenv("DATABASE_URL", ""))
if not url.scheme:
    raise ValueError("DATABASE_URL is required to avoid database resets on Render.com.")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{url.username}:{url.password}@{url.hostname}:{url.port}{url.path}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

# Ustalony login i hasło
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# 📌 Model kategorii
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# 📌 Model produktu
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'), nullable=False)
    category = db.relationship("Category", backref=db.backref("products", cascade="all, delete-orphan", lazy=True))

# 📌 Tworzenie bazy danych
with app.app_context():
    db.create_all()

# 📌 Strona główna (z zabezpieczeniem logowania)
@app.route("/")
def index():
    logged_in = "user" in session
    return render_template("index.html", logged_in=logged_in)

# 📌 Logowanie użytkownika
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if data.get("username") == ADMIN_USERNAME and data.get("password") == ADMIN_PASSWORD:
        session["user"] = ADMIN_USERNAME  # Zapisanie sesji
        session.modified = True  # Wymuszenie zapisu sesji
        return jsonify({"redirect": url_for("index"), "message": "Login successful"})
    return jsonify({"message": "Invalid credentials"}), 401

# 📌 Wylogowanie użytkownika
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()  # Całkowite usunięcie sesji
    return jsonify({"message": "Logged out successfully!", "redirect": url_for("index")})

# 📌 Pobieranie kategorii
@app.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    return jsonify([{"id": c.id, "name": f"{c.name} (Cat. ID: {c.id})"} for c in categories])

# 📌 Pobieranie produktów pogrupowanych według kategorii
@app.route("/products", methods=["GET"])
def get_products():
    categories = Category.query.all()
    products_by_category = {}
    
    for category in categories:
        products = Product.query.filter_by(category_id=category.id).all()
        products_by_category[f"{category.name} (Cat. ID: {category.id})"] = [
            {"id": p.id, "name": p.name, "quantity": p.quantity, "category_id": p.category_id}
            for p in products
        ]
    
    return jsonify(products_by_category)

# 📌 Dodawanie nowej kategorii
@app.route("/category", methods=["POST"])
def add_category():
    data = request.json
    new_category = Category(name=data.get("name"))
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"message": "Category added successfully!"})

# 📌 Edycja kategorii
@app.route("/category/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    data = request.json
    category = Category.query.get_or_404(category_id)
    category.name = data.get("name")
    db.session.commit()
    return jsonify({"message": "Category updated successfully!"})

# 📌 Usunięcie kategorii (najpierw usuwamy produkty)
@app.route("/category/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    Product.query.filter_by(category_id=category_id).delete()
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully!"})

# 📌 Dodawanie nowego produktu
@app.route("/product", methods=["POST"])
def add_product():
    data = request.json
    
    # Walidacja danych wejściowych
    if not data.get("name") or not isinstance(data.get("quantity"), int) or not isinstance(data.get("category_id"), int):
        return jsonify({"message": "Invalid data! Ensure all fields are filled correctly."}), 400

    new_product = Product(
        name=data["name"].strip(),
        quantity=int(data["quantity"]),
        category_id=int(data["category_id"])
    )

    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({"message": "Product added successfully!"})


# 📌 Edycja produktu
@app.route("/product/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.json
    product = Product.query.get_or_404(product_id)
    product.name = data.get("name")
    product.quantity = data.get("quantity")
    
    if "category_id" in data and data.get("category_id") is not None:
        product.category_id = data.get("category_id")
    
    db.session.commit()
    return jsonify({"message": "Product updated successfully!"})

# 📌 Usunięcie produktu
@app.route("/product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
