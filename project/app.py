from flask import Flask, render_template, request, redirect, url_for, flash, session,make_response
from flask_mysqldb import MySQL
from flask import request, jsonify, session
from flask import render_template
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'shreya0103'
app.config['MYSQL_DB'] = 'a'

mysql = MySQL(app)
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT user_id, password FROM user WHERE username = '{email}';")
    result = cursor.fetchone()
    cursor.close()
    if result and result[1] == password:
        session['user_id'] = result[0]
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('login'))

    
        



@app.route('/signup')
def signup():
    return render_template('signup.html')




@app.route('/signup', methods=['POST'])
def signup_post():
    data = request.json  # Use request.json to access JSON data
    email = data.get('email')
    password = data.get('password')
    cursor = mysql.connection.cursor()
    print(email,password)
    # Check if the user already exists
    cursor.execute(f"SELECT * FROM user WHERE username = '{email}'")
    existing_user = cursor.fetchone()
    
    if existing_user:
        flash('Email address already registered. Please log in.')
        cursor.close()
        return redirect(url_for('signup'))
    
    # Insert new user into the databas  
    cursor.execute(f"INSERT INTO user (username, password) VALUES  ('{email}', '{password}')")
    mysql.connection.commit()
    cursor.close()

    flash('Sign up successful! You can now log in.')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    print(session.get('user_id'))
    cursor = mysql.connection.cursor()
    query = "SELECT product_name, price FROM products WHERE feature = 1"
    cursor.execute(query)
    featured_products = cursor.fetchall()

    cursor.close()
    
    return render_template('home.html',featured_products=featured_products,u=session.get('user_id'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = session.get('user_id')  # Get the logged-in user ID from the session
    product_id = data['id']
    quantity = data.get('quantity', 1)

    if not user_id:
        return jsonify({'message': 'User not logged in'}), 401  # Unauthorized if user_id is missing

    try:
        conn = mysql.connection
        cursor = conn.cursor()

        # Call the add_to_cart procedure with the required parameters
        cursor.callproc('add_to_cart', (user_id, product_id, quantity))
        
        # Commit the transaction
        conn.commit()

        cursor.close()

        return jsonify({'message': 'Product added to cart successfully!'}), 200
    except Exception as err:
        print(f"Error: {err}")
        return jsonify({'message': 'Failed to add product to cart'}), 500

@app.route('/products')
def products():
    cursor = mysql.connection.cursor()
    query = "SELECT category_name FROM category"
    cursor.execute(query)
    categories= cursor.fetchall()
    categories = [i[0] for i in categories]  # Dictionary access
    cursor.close()
    
    return render_template('categories.html', categories=categories)
@app.route('/cart', methods=['GET','POST'])
def cart():
    user_id = session.get('user_id')
    print(user_id)
    if not user_id:
        flash('Please log in to view your cart.')
        return redirect(url_for('login'))

    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.callproc('show_cart', (user_id,))
        cart_items = cursor.fetchall()
        print(cart_items)
        total=sum([i[4] for i in cart_items ])
        print(total)
        cursor.close()
        response = make_response(render_template('cart.html', cart_items=cart_items, total=total))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        
        return response
    except Exception as err:
        print(f"Error: {err}")
        flash('Failed to load cart items.')
        return redirect(url_for('home'))

        
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    # Get user_id and product_id from the request JSON data
    data = request.json
    print(data)
    user_id = session.get('user_id')
    product_id = data.get('product_id')

    # Validate input
    if not user_id or not product_id:
        return jsonify({"error": "user_id and product_id are required"}), 400

    try:
        # Use flask_mysqldb's mysql.connection
        conn = mysql.connection
        cursor = conn.cursor()

        # Call the stored procedure
        cursor.callproc('remove_from_cart', [user_id, product_id])
        conn.commit()

        # Close the database connection
        cursor.close()

        return jsonify({"message": "Item removed from cart successfully"}), 200

    except Exception as err:
        return jsonify({"error": str(err)}), 500


@app.route('/update_cart', methods=['POST'])
def update_cart():
    # Get user_id from the session and cart items from the request JSON data
    user_id = session.get('user_id')
    cart_items = request.json  # Expecting an array of { product_id, quantity } objects

    # Validate user_id
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        # Use flask_mysqldb's mysql.connection
        conn = mysql.connection
        cursor = conn.cursor()
        print(cart_items)
        # Iterate over each cart item and update the quantity using a stored procedure
        for item in cart_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            # Validate input
            if not product_id or quantity is None:
                return jsonify({"error": "product_id and quantity are required for each item"}), 400
            
            if product_id=='7' and quantity!=1:
                print('kjxdbg')
            else:
                cursor.callproc('update_cart', (user_id, product_id, quantity))
                conn.commit()  # Commit the transaction
        cursor.close()  # Close the cursor

        return jsonify({"message": "Cart updated successfully"}), 200

    except Exception as err:
        return jsonify({"error": str(err)}), 500

@app.route('/fruits')
def fruits():
    cursor = mysql.connection.cursor()
    query='SELECT product_id ,product_name, price FROM products WHERE category_id = 1'
    cursor.execute(query)
    product=cursor.fetchall()
    return render_template('fruits.html' , products=product)

@app.route('/Vegetables')
def Vegetables():
    cursor = mysql.connection.cursor()
    query='SELECT product_id ,product_name, price FROM products WHERE category_id = 3'
    cursor.execute(query)
    product=cursor.fetchall()
    return render_template('Vegetables.html' , products=product)

@app.route('/Beverages')
def Beverages():
    cursor = mysql.connection.cursor()
    query='SELECT product_id ,product_name, price FROM products WHERE category_id = 2'
    cursor.execute(query)
    product=cursor.fetchall()
    return render_template('Beverages.html' , products=product)

@app.route('/Dairy')
def Dairy():
    cursor = mysql.connection.cursor()
    query='SELECT product_id ,product_name, price FROM products WHERE category_id = 4'
    cursor.execute(query)
    product=cursor.fetchall()
    return render_template('Dairy.html' , products=product)

@app.route('/personalcare')
def personalcare():
    cursor = mysql.connection.cursor()
    query='SELECT product_id ,product_name, price FROM products WHERE category_id = 5'
    cursor.execute(query)
    product=cursor.fetchall()
    return render_template('personalcare.html' , products=product)

@app.route('/Snacks')
def Snacks():
    cursor = mysql.connection.cursor()
    query='SELECT product_id ,product_name, price FROM products WHERE category_id = 6'
    cursor.execute(query)
    product=cursor.fetchall()
    return render_template('Snacks.html' , products=product)

@app.route('/checkout',methods=['POST'])
def checkout():
    a={}
    user_id = session.get('user_id')
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.callproc('show_cart', (user_id,))
    cart_items = cursor.fetchall()
    for i in cart_items:
        if i[3]==7:
            continue
        cursor.execute(f"select quantity from inventory where product_id = {i[3]}")
        availabe = cursor.fetchone()
        if i[2] > availabe[0] :
            a[i[3]]=availabe[0]
        else:
            cursor.execute(f"update inventory set quantity = {availabe[0] - i[3]} where product_id = {i[3]}")
    
    if a == {}:
        cursor.execute(f"delete from cart_items where user_id = {user_id}")
        conn.commit()
        return render_template('checkout.html')
    else:
        print(a)
        total=sum([i[4] for i in cart_items ])
        return render_template('cart.html' ,  cart_items=cart_items, total=total, a=a)
        
        


@app.route('/logout')
def logout():
    # Remove 'user_id' from session to log the user out
    session.pop('user_id', None)
    
    # Redirect to the login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
