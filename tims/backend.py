import json
from flask import Flask, jsonify, request

# Initialize the Flask application
app = Flask(__name__)

# --- In-Memory Data Stores (Simulating a Database) ---

# Hardcoded user accounts with roles for a simple authentication demo.
users = {
    "admin": {"password": "adminpassword", "role": "Admin"},
    "manager": {"password": "managerpassword", "role": "Manager"},
    "staff": {"password": "staffpassword", "role": "Staff"}
}

# Data stores for products and suppliers. Using dictionaries for quick lookup by ID.
# These will hold our in-memory data for the duration of the application.
products = {
    1: {"id": 1, "name": "Fiber Optic Cable", "category": "Cables", "stock_level": 500, "reorder_point": 100},
    2: {"id": 2, "name": "Router X-500", "category": "Networking", "stock_level": 50, "reorder_point": 20},
    3: {"id": 3, "name": "Modem Pro-100", "category": "Networking", "stock_level": 75, "reorder_point": 15},
    4: {"id": 4, "name": "Satellite Dish", "category": "Antennas", "stock_level": 10, "reorder_point": 5}
}
suppliers = {
    1: {"id": 1, "name": "Global Telecom Solutions", "contact_info": "contact@globaltele.com"},
    2: {"id": 2, "name": "FiberLink Inc.", "contact_info": "sales@fiberlink.net"}
}

# Counters for generating unique IDs for new items.
product_id_counter = 5
supplier_id_counter = 3

# --- Helper Function for Role-Based Access Control ---

def get_user_role(username, password):
    """
    Simulates a login check and returns the user's role if credentials are valid.
    In a real app, this would involve a secure token (JWT).
    For this demo, we'll just check the username and password against our in-memory store.
    """
    user = users.get(username)
    if user and user['password'] == password:
        return user['role']
    return None

# --- API Endpoints ---

@app.route('/login', methods=['POST'])
def login():
    """
    Handles user authentication.
    Returns the user's role on successful login.
    """
    auth_data = request.json
    username = auth_data.get('username')
    password = auth_data.get('password')
    
    role = get_user_role(username, password)
    if role:
        return jsonify({"message": "Login successful", "username": username, "role": role}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/products', methods=['GET'])
def get_products():
    """
    Retrieves all products, with optional search and filtering.
    """
    name_query = request.args.get('name', '').lower()
    category_query = request.args.get('category', '').lower()
    stock_status_query = request.args.get('stock_status', '').lower()
    
    filtered_products = list(products.values())

    if name_query:
        filtered_products = [p for p in filtered_products if name_query in p['name'].lower()]
    
    if category_query:
        filtered_products = [p for p in filtered_products if category_query in p['category'].lower()]
        
    if stock_status_query:
        if stock_status_query == 'low':
            filtered_products = [p for p in filtered_products if p['stock_level'] < p['reorder_point']]
        elif stock_status_query == 'out of stock':
            filtered_products = [p for p in filtered_products if p['stock_level'] <= 0]
            
    return jsonify(filtered_products)

@app.route('/products', methods=['POST'])
def add_product():
    """
    Adds a new product. Requires Admin or Manager role.
    """
    global product_id_counter
    # For a hackathon, we can pass the username/password in the body.
    # A real app would use an auth token in the header.
    auth_data = request.json
    role = get_user_role(auth_data.get('username'), auth_data.get('password'))
    
    if role not in ['Admin', 'Manager']:
        return jsonify({"error": "Unauthorized access"}), 403

    product_data = auth_data.get('product', {})
    if not product_data or not all(k in product_data for k in ['name', 'category', 'stock_level', 'reorder_point']):
        return jsonify({"error": "Invalid product data"}), 400

    new_product = {
        'id': product_id_counter,
        'name': product_data['name'],
        'category': product_data['category'],
        'stock_level': product_data['stock_level'],
        'reorder_point': product_data['reorder_point']
    }
    products[product_id_counter] = new_product
    product_id_counter += 1
    
    return jsonify(new_product), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    Updates an existing product. Requires Admin or Manager role.
    """
    auth_data = request.json
    role = get_user_role(auth_data.get('username'), auth_data.get('password'))
    
    if role not in ['Admin', 'Manager']:
        return jsonify({"error": "Unauthorized access"}), 403

    product = products.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
        
    update_data = auth_data.get('product', {})
    product.update(update_data)
    
    return jsonify(product)

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Deletes a product. Requires Admin role.
    """
    auth_data = request.json
    role = get_user_role(auth_data.get('username'), auth_data.get('password'))
    
    if role != 'Admin':
        return jsonify({"error": "Unauthorized access"}), 403

    if product_id not in products:
        return jsonify({"error": "Product not found"}), 404
    
    del products[product_id]
    return jsonify({"message": "Product deleted"}), 200

@app.route('/products/<int:product_id>/stock', methods=['PUT'])
def update_stock(product_id):
    """
    Records a stock transaction (in/out). Requires Admin, Manager, or Staff role.
    """
    auth_data = request.json
    role = get_user_role(auth_data.get('username'), auth_data.get('password'))
    
    if role not in ['Admin', 'Manager', 'Staff']:
        return jsonify({"error": "Unauthorized access"}), 403

    product = products.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    change = auth_data.get('change', 0)
    if not isinstance(change, int) or change == 0:
        return jsonify({"error": "Invalid stock change value"}), 400
        
    product['stock_level'] += change
    
    return jsonify(product)

@app.route('/suppliers', methods=['GET'])
def get_suppliers():
    """
    Retrieves all suppliers.
    """
    return jsonify(list(suppliers.values()))

@app.route('/suppliers', methods=['POST'])
def add_supplier():
    """
    Adds a new supplier. Requires Admin role.
    """
    global supplier_id_counter
    auth_data = request.json
    role = get_user_role(auth_data.get('username'), auth_data.get('password'))
    
    if role != 'Admin':
        return jsonify({"error": "Unauthorized access"}), 403
        
    supplier_data = auth_data.get('supplier', {})
    if not supplier_data or 'name' not in supplier_data:
        return jsonify({"error": "Invalid supplier data"}), 400
    
    new_supplier = {
        'id': supplier_id_counter,
        'name': supplier_data['name'],
        'contact_info': supplier_data.get('contact_info', '')
    }
    suppliers[supplier_id_counter] = new_supplier
    supplier_id_counter += 1
    
    return jsonify(new_supplier), 201

# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=True)
