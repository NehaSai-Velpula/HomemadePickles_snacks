from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# AWS DynamoDB Setup
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
orders_table = dynamodb.Table('Orders')  # Make sure table is created

products = {
    "veg_pickles": [
        {"id": 1, "name": "Mango Pickle", "price": 150, "image": "mango.jpg"},
        {"id": 2, "name": "Lemon Pickle", "price": 100, "image": "lemon.webp"},
        {"id": 3, "name": "Gongura Pickle", "price": 150, "image": "gongura.webp"},
        {"id": 4, "name": "Tomato Pickle", "price": 180, "image": "tomato.jpg"}
    ],
    "non_veg_pickles": [
        {"id": 5, "name": "Fish Pickle", "price": 270, "image": "fish.webp"},
        {"id": 6, "name": "Chicken Pickle", "price": 230, "image": "chicken.jpg"},
        {"id": 7, "name": "Boneless Chicken Pickle", "price": 250, "image": "bonelesschicken.jpeg"},
        {"id": 8, "name": "Mutton Pickle", "price": 300, "image": "mutton.webp"}
    ],
    "snacks": [
        {"id": 9, "name": "Banana Chips", "price": 70, "image": "banana.png"},
        {"id": 10, "name": "Murukku", "price": 60, "image": "murukku.jpeg"},
        {"id": 11, "name": "Dryfruit Laddu", "price": 200, "image": "DryfruitLaddu.webp"},
        {"id": 12, "name": "Kajju Masala", "price": 180, "image": "kajjumasala.jpg"}
    ]
}
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact_us.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email] == password:
            session['user'] = email
            return redirect(url_for('home'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users[email] = password
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/veg_pickles')
def veg_pickles():
    return render_template('veg_pickles.html', products=products['veg_pickles'])

@app.route('/non_veg_pickles')
def non_veg_pickles():
    return render_template('non_veg_pickles.html', products=products['non_veg_pickles'])

@app.route('/snacks')
def snacks():
    return render_template('snacks.html', products=products['snacks'])

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_id)
    flash("Item added to cart!")
    return redirect(request.referrer)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [int(item) for item in session['cart']]
        if product_id in session['cart']:
            session['cart'].remove(product_id)
            flash("Item removed from cart!")
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    for category in products.values():
        for item in category:
            if 'cart' in session and item['id'] in session['cart']:
                cart_items.append(item)
                total += item['price']
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/success')
def success():
    if 'cart' not in session or 'user' not in session:
        return redirect(url_for('index'))

    cart_items = []
    total = 0
    for category in products.values():
        for item in category:
            if item['id'] in session['cart']:
                cart_items.append(item)
                total += item['price']

    # Generate order ID and store in DynamoDB
    order_id = str(uuid.uuid4())
    orders_table.put_item(Item={
        'order_id': order_id,
        'email': session['user'],
        'items': cart_items,
        'total': total,
        'timestamp': datetime.now().isoformat()
    })

    session.pop('cart', None)
    return render_template('success.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
