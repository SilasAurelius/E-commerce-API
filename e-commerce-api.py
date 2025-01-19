from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Password1@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Customer Schema
class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)
    
    class Meta:
        fields = ('name', 'email', 'phone', 'id')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

# Order Schema
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order  # Use the actual model class
        include_fk = True

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# Customer Model
class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(350))
    phone = db.Column(db.String(15))
    orders = db.relationship('Order', backref='customer')

# Order Model
class Order(db.Model):
    __tablename__ = "Orders"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))

# Product Model
order_product = db.Table('Order_Product',
    db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True)
)

class Product(db.Model):
    __tablename__ = "Products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    orders = db.relationship('Order', secondary=order_product, backref=db.backref('products'))

# Product Schema
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        include_fk = True

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Customer Account Model (added)
class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))
    customer = db.relationship('Customer', backref='customer_account', uselist=False)

# Routes for Orders

# Get All Orders
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

# Get Order by ID
@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return order_schema.jsonify(order)

# Create New Order
@app.route('/orders', methods=['POST'])
def add_order():
    try:
        order_data = request.get_json()
        date_str = order_data.get('date')
        customer_id = order_data.get('customer_id')

        if not date_str or not customer_id:
            return jsonify({"message": "Date and customer_id are required"}), 400

        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use 'YYYY-MM-DD'."}), 400

        new_order = Order(date=date, customer_id=customer_id)
        db.session.add(new_order)
        db.session.commit()

        return jsonify({"message": "New order created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update Order by ID
@app.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    order = Order.query.get_or_404(id)
    try:
        order_data = request.get_json()
        order.date = order_data.get('date', order.date)
        order.customer_id = order_data.get('customer_id', order.customer_id)
        db.session.commit()

        return jsonify({"message": "Order updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete Order by ID
@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Order deleted successfully"}), 200

# Routes for Customers

# Get All Customers
@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)

# Add New Customer
@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_customer = Customer(
        name=customer_data['name'],
        email=customer_data['email'],
        phone=customer_data['phone']
    )
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify({'message': 'New customer added successfully'}), 201

# Update Customer by ID
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()

    return jsonify({'message': 'Customer details updated successfully'}), 200

# Delete Customer by ID
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": 'Customer removed successfully'}), 200

# Routes for Customer Account

@app.route('/customer_accounts', methods=['POST'])
def add_customer_account():
    try:
        account_data = request.get_json()
        username = account_data.get('username')
        password = account_data.get('password')
        customer_id = account_data.get('customer_id')

        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        new_account = CustomerAccount(
            username=username, password=password, customer_id=customer_id
        )
        db.session.add(new_account)
        db.session.commit()
        return jsonify({"message": "Customer account created successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Routes for Products

@app.route('/products', methods=['POST'])
def add_product():
    try:
        product_data = request.get_json()
        name = product_data.get('name')
        price = product_data.get('price')

        if not name or not price:
            return jsonify({"message": "Product name and price are required"}), 400
        
        new_product = Product(name=name, price=price)
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "New product added successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price
    })

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = request.get_json()
        product.name = product_data.get('name', product.name)
        product.price = product_data.get('price', product.price)
        db.session.commit()
        return jsonify({"message": "Product updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
