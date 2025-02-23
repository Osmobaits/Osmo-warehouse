from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'tajny_klucz'  # Klucz do szyfrowania sesji

# Ścieżka do bazy danych
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "kontrahenci.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model klienta
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='client', lazy=True, cascade="all, delete-orphan")

# Model produktu przypisanego do klienta
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False, default=0)
    quantity_packed = db.Column(db.Integer, nullable=False, default=0)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

# Tworzenie bazy danych
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' in session:
        clients = Client.query.all()
        
        for client in clients:
            client.has_active_order = any(product.quantity_ordered > 0 for product in client.products)

        return render_template('index1.html', username=session['user'], clients=clients)

    message = ""
    if request.method == 'POST':
        user_login = request.form.get('login')
        user_password = request.form.get('password')

        if user_login == "admin" and user_password == "magazyn12":
            session['user'] = user_login
            return redirect(url_for('home'))
        else:
            message = "Błędny login lub hasło. Spróbuj ponownie."

    return render_template('index1.html', message=message)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/add_client', methods=['POST'])
def add_client():
    if 'user' not in session:
        return redirect(url_for('home'))

    name = request.form.get('name')

    if name:
        new_client = Client(name=name)
        db.session.add(new_client)
        db.session.commit()

    return redirect(url_for('home'))

@app.route('/edit_client/<int:client_id>', methods=['POST'])
def edit_client(client_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    client = Client.query.get_or_404(client_id)
    new_name = request.form.get('name')
    if new_name:
        client.name = new_name
        db.session.commit()

    return redirect(url_for('home'))

@app.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()

    return redirect(url_for('home'))

@app.route('/client/<int:client_id>')
def client_details(client_id):
    client = Client.query.get_or_404(client_id)
    products = Product.query.filter_by(client_id=client.id).all()
    return render_template('client_details.html', client=client, products=products)

@app.route('/reset_orders/<int:client_id>', methods=['POST'])
def reset_orders(client_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    products = Product.query.filter_by(client_id=client_id).all()

    for product in products:
        product.quantity_ordered = 0
        product.quantity_packed = 0

    db.session.commit()
    return jsonify({'success': True})

@app.route('/add_product/<int:client_id>', methods=['POST'])
def add_product(client_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    product_name = request.form.get('product_name')

    if product_name:
        new_product = Product(
            name=product_name,
            quantity_ordered=0,
            quantity_packed=0,
            client_id=client_id
        )
        db.session.add(new_product)
        db.session.commit()

    return redirect(url_for('client_details', client_id=client_id))

@app.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    product = Product.query.get_or_404(product_id)
    new_name = request.form.get('name')
    if new_name:
        product.name = new_name
        db.session.commit()

    return redirect(url_for('client_details', client_id=product.client_id))

@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    product = Product.query.get_or_404(product_id)
    data = request.json

    # Aktualizacja tylko ilości zamówionej i spakowanej
    if 'quantity_ordered' in data:
        product.quantity_ordered = int(data['quantity_ordered'])
    if 'quantity_packed' in data:
        product.quantity_packed = int(data['quantity_packed'])

    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user' not in session:
        return redirect(url_for('home'))

    product = Product.query.get_or_404(product_id)
    client_id = product.client_id
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('client_details', client_id=client_id))

if __name__ == "__main__":
    app.run(debug=True)
