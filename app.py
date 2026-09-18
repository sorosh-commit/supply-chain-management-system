from flask import Flask, render_template, request, flash, redirect, url_for
from models import db, User, Product, Warehouse, Supplier, Stock, Transaction, Vehicle, Driver, ShipmentRoute, Customer, \
    CustomerOrder, CustomerOrderItem, Invoice, Category, Route
import io
import pandas as pd
from flask import send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///enterprise_supply_chain.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    else:
        admin.set_password('admin123')

    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Check username and password validity
        if user and user.check_password(password):
            login_user(user)
            flash('با موفقیت وارد شدید.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')

    return render_template('login.html')


# Route for user registration and creating a new account
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user already exists with this username
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('این نام کاربری قبلاً ثبت شده است.', 'danger')
            return redirect(url_for('signup'))

        # Hash password for enhanced security
        hashed_password = generate_password_hash(password)

        new_user = User(username=username, role="Operator")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('ثبت‌نام با موفقیت انجام شد. لطفاً وارد شوید.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    total_products = Product.query.count()
    total_warehouses = Warehouse.query.count()
    total_suppliers = Supplier.query.count()
    transactions_count = Transaction.query.count()
    recent_transactions = Transaction.query.order_by(Transaction.id.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_products=total_products,
        total_warehouses=total_warehouses,
        total_suppliers=total_suppliers,
        t_count=transactions_count,
        transactions=recent_transactions
    )


@app.route('/reports/export/excel')
@login_required
def export_excel():
    # Fetch stock and product data joined together
    stocks = Stock.query.all()

    data = []
    for s in stocks:
        data.append({
            'کد کالا (SKU)': s.product.sku if s.product else '',
            'نام کالا': s.product.name if s.product else '',
            'دسته‌بندی': getattr(s.product, 'category', 'عمومی'),
            'انبار': s.warehouse.location if s.warehouse else '',
            'موجودی فعلی': s.quantity,
            'قیمت واحد (تومان)': s.product.price if s.product else 0,
            'ارزش کل (تومان)': s.quantity * (s.product.price if s.product else 0)
        })

    df = pd.DataFrame(data)

    # Create an in-memory output buffer for the Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory Report')

    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='supply_chain_inventory_report.xlsx'
    )


@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku')
        price = float(request.form.get('price'))
        supplier_id = int(request.form.get('supplier_id'))
        category_id = request.form.get('category_id')  # Retrieve category ID

        # Add category_id to the product constructor
        new_product = Product(
            name=name,
            sku=sku,
            price=price,
            supplier_id=supplier_id,
            category_id=category_id
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('list_products'))

    suppliers = Supplier.query.all()
    categories = Category.query.all()  # 1. Read categories from database
    return render_template('add_product.html', suppliers=suppliers, categories=categories)  # 2. Pass to HTML template


@app.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        product_id = int(request.form.get('product_id'))
        warehouse_id = int(request.form.get('warehouse_id'))
        change_amount = int(request.form.get('change_amount'))
        transaction_type = request.form.get('transaction_type')  # 'INBOUND' or 'OUTBOUND'

        # If transaction type is outbound, negate the change amount
        actual_change = change_amount if transaction_type == 'INBOUND' else -change_amount

        # Validate warehouse stock availability for outbound operations
        if transaction_type == 'OUTBOUND':
            stock_record = Stock.query.filter_by(product_id=product_id, warehouse_id=warehouse_id).first()
            current_qty = stock_record.quantity if stock_record else 0
            if current_qty < change_amount:
                return "Error: Insufficient stock in warehouse for this outbound quantity!", 400

            # 1. Register the transaction in the audit trail (Transaction table)
            new_tx = Transaction(
                product_id=product_id,
                warehouse_id=warehouse_id,
                user_id=current_user.id,  # Use current logged-in user ID
                change_amount=actual_change,
                transaction_type=transaction_type
            )
            db.session.add(new_tx)

        # 2. Update inventory stock levels in the Stock table
        stock_record = Stock.query.filter_by(product_id=product_id, warehouse_id=warehouse_id).first()
        if stock_record:
            stock_record.quantity += actual_change
        else:
            if transaction_type == 'INBOUND':
                new_stock = Stock(product_id=product_id, warehouse_id=warehouse_id, quantity=change_amount)
                db.session.add(new_stock)
            else:
                return "Error: Product does not exist in this warehouse stock!", 400

        db.session.commit()
        return redirect(url_for('reports'))

    products = Product.query.all()
    warehouses = Warehouse.query.all()
    return render_template('add_transaction.html', products=products, warehouses=warehouses)


# Route for creating a new shipment route and assigning a vehicle and driver
@app.route('/routes/add', methods=['GET', 'POST'])
@login_required
def add_route():
    if request.method == 'POST':
        # Retrieve form input data
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        vehicle_id = int(request.form.get('vehicle_id'))
        driver_id = int(request.form.get('driver_id'))

        # Initialize a new ShipmentRoute record
        new_route = ShipmentRoute(
            origin=origin,
            destination=destination,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            status='Pending'
        )

        # Commit the route to the database
        db.session.add(new_route)
        db.session.commit()

        return redirect(url_for('list_routes'))

    # Query available vehicles and active drivers for selection dropdowns
    vehicles = Vehicle.query.filter_by(status='Available').all()
    drivers = Driver.query.filter_by(status='Active').all()

    return render_template('add_route.html', vehicles=vehicles, drivers=drivers)


@app.route('/routes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_route(id):
    # Find the target record from database or return 404 if not found
    route = Route.query.get_or_404(id)

    if request.method == 'POST':
        # Retrieve new data from form
        route.origin = request.form.get('origin')
        route.destination = request.form.get('destination')
        route.vehicle_id = request.form.get('vehicle_id')
        route.driver_id = request.form.get('driver_id')

        # Save changes to the database
        db.session.commit()
        flash('مسیر با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('list_routes'))

    # In GET method, render form with current data, vehicles, and drivers list
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    return render_template('edit_route.html', route=route, vehicles=vehicles, drivers=drivers)


@app.route('/products')
@login_required
def list_products():
    # Get the search query parameter from the URL if it exists
    search_query = request.args.get('q', '').strip()

    if search_query:
        # Filter products by name or SKU matching the search query
        products_list = Product.query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.sku.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        # Fetch all products if no search query is provided
        products_list = Product.query.all()

    return render_template('products.html', products=products_list, search_query=search_query)


@app.route('/vehicles')
@login_required
def list_vehicles():
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    return render_template('vehicles.html', vehicles=vehicles, drivers=drivers)


@app.route('/routes')
@login_required
def list_routes():
    routes = ShipmentRoute.query.all()
    return render_template('routes.html', routes=routes)


@app.route('/reports')
@login_required
def reports():
    total_products = Product.query.count()
    total_warehouses = Warehouse.query.count()
    total_suppliers = Supplier.query.count()
    total_vehicles = Vehicle.query.count()
    total_drivers = Driver.query.count()
    total_routes = ShipmentRoute.query.count()
    total_transactions = Transaction.query.count()

    stocks = Stock.query.all()
    total_inventory_value = sum([stock.quantity * stock.product.price for stock in stocks])

    recent_transactions = Transaction.query.order_by(Transaction.id.desc()).all()

    return render_template(
        'reports.html',
        total_products=total_products,
        total_warehouses=total_warehouses,
        total_suppliers=total_suppliers,
        total_vehicles=total_vehicles,
        total_drivers=total_drivers,
        total_routes=total_routes,
        total_transactions=total_transactions,
        total_inventory_value=total_inventory_value,
        transactions=recent_transactions
    )


# Route for adding a new vehicle to the fleet
@app.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        plate_number = request.form.get('plate_number')
        capacity = float(request.form.get('capacity', 0))

        # Initialize a new Vehicle record with Available status
        new_vehicle = Vehicle(
            model_name=model_name,
            plate_number=plate_number,
            capacity=capacity,
            status='Available'
        )

        db.session.add(new_vehicle)
        db.session.commit()

        flash('خودروی جدید با موفقیت ثبت شد.', 'success')
        return redirect(url_for('list_vehicles'))

    return render_template('add_vehicle.html')


# Route for adding a new driver to the system
@app.route('/add_driver', methods=['GET', 'POST'])
@app.route('/drivers/add', methods=['GET', 'POST'])
@login_required
def add_driver():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        license_number = request.form.get('license_number')

        new_driver = Driver(
            name=name,
            phone=phone,
            license_number=license_number,
            status='Active'
        )
        db.session.add(new_driver)
        db.session.commit()
        return redirect(url_for('list_vehicles'))

    return render_template('add_driver.html')


@app.route('/drivers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_driver(id):
    driver = Driver.query.get_or_404(id)
    if request.method == 'POST':
        driver.name = request.form.get('name')
        driver.license_number = request.form.get('license_number')
        driver.phone = request.form.get('phone')

        db.session.commit()
        flash('اطلاعات راننده با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('list_drivers'))

    return render_template('edit_driver.html', driver=driver)


# --- Drivers ---
@app.route('/drivers')
@login_required
def list_drivers():
    drivers = Driver.query.all()
    return render_template('drivers.html', drivers=drivers)


@app.route('/drivers/add', methods=['GET', 'POST'])
@login_required
def create_driver():
    if request.method == 'POST':
        name = request.form.get('name')
        license_number = request.form.get('license_number')
        phone = request.form.get('phone')

        new_driver = Driver(name=name, license_number=license_number, phone=phone)
        db.session.add(new_driver)
        db.session.commit()
        flash('راننده جدید با موفقیت ثبت شد.', 'success')
        return redirect(url_for('list_drivers'))
    return render_template('add_driver.html')


# --- Fleet (Vehicles) ---
@app.route('/vehicles')
@login_required
def vehicles_list():
    vehicles = Vehicle.query.all()
    # Note: Pay attention to uppercase/lowercase 'V' in your image file name (Vehicles.html)
    return render_template('Vehicles.html', vehicles=vehicles)


@app.route('/vehicles/add', methods=['GET', 'POST'])
@login_required
def create_vehicle():
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        plate_number = request.form.get('plate_number')
        capacity = request.form.get('capacity')

        new_vehicle = Vehicle(model_name=model_name, plate_number=plate_number, capacity=capacity)
        db.session.add(new_vehicle)
        db.session.commit()
        flash('خودروی جدید با موفقیت ثبت شد.', 'success')
        return redirect(url_for('list_vehicles'))
    return render_template('add_vehicle.html')


@app.route('/vehicles/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)
    if request.method == 'POST':
        vehicle.model_name = request.form.get('model_name')
        vehicle.plate_number = request.form.get('plate_number')
        vehicle.capacity = float(request.form.get('capacity'))
        vehicle.status = request.form.get('status')

        db.session.commit()
        flash('اطلاعات خودرو با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('list_vehicles'))

    return render_template('edit_vehicle.html', vehicle=vehicle)


# --- Routes ---
@app.route('/routes')
@login_required
def routes_list():
    routes = Route.query.all()
    return render_template('routes.html', routes=routes)


@app.route('/routes/add', methods=['GET', 'POST'])
@login_required
def create_route():
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        vehicle_id = request.form.get('vehicle_id')
        driver_id = request.form.get('request.form.get("driver_id")')  # Form fix

        new_route = Route(origin=origin, destination=destination, vehicle_id=vehicle_id,
                          driver_id=request.form.get('driver_id'))
        db.session.add(new_route)
        db.session.commit()
        flash('مسیر جدید ثبت شد.', 'success')
        return redirect(url_for('list_routes'))

    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    return render_template('add_route.html', vehicles=vehicles, drivers=drivers)


# Route to view customers list
@app.route('/customers')
@login_required
def list_customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)


# Route to add a new customer
@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')

        new_customer = Customer(name=name, phone=phone, email=email, address=address)
        db.session.add(new_customer)
        db.session.commit()
        flash('مشتری جدید با موفقیت ثبت شد.', 'success')
        return redirect(url_for('list_customers'))

    return render_template('add_customer.html')


@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.phone = request.form.get('phone')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')

        db.session.commit()
        flash('اطلاعات مشتری با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('list_customers'))

    return render_template('edit_customer.html', customer=customer)


# --- Customer Orders Management Section ---
@app.route('/orders')
@login_required
def list_orders():
    orders = CustomerOrder.query.all()
    return render_template('orders.html', orders=orders)


@app.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add_order():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))

        product = Product.query.get_or_404(product_id)
        total_amount = product.price * quantity

        new_order = CustomerOrder(
            customer_id=customer_id,
            user_id=current_user.id,
            total_amount=total_amount,
            status='Pending'
        )
        db.session.add(new_order)
        db.session.flush()  # Retrieve order ID before final commit

        order_item = CustomerOrderItem(
            customer_order_id=new_order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price
        )
        db.session.add(order_item)

        # Automatically issue an invoice for the order
        invoice = Invoice(
            customer_order_id=new_order.id,
            amount=total_amount,
            tax=total_amount * 0.09,  # 9 percent VAT
            status='Unpaid'
        )
        db.session.add(invoice)
        db.session.commit()

        flash('سفارش جدید و فاکتور مربوطه با موفقیت ثبت شدند.', 'success')
        return redirect(url_for('list_orders'))

    customers = Customer.query.all()
    products = Product.query.all()
    return render_template('add_order.html', customers=customers, products=products)


@app.route('/orders/invoice/<int:order_id>')
@login_required
def view_invoice(order_id):
    order = CustomerOrder.query.get_or_404(order_id)
    return render_template('invoice.html', order=order)


@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))

        db.session.commit()
        flash('محصول با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('list_products'))

    return render_template('edit_product.html', product=product)


@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            existing = Category.query.filter_by(name=name).first()
            if existing:
                flash('این دسته‌بندی قبلاً ثبت شده است.', 'danger')
            else:
                new_cat = Category(name=name)
                db.session.add(new_cat)
                db.session.commit()
                flash('دسته‌بندی جدید با موفقیت اضافه شد.', 'success')
        return redirect(url_for('manage_categories'))

    categories = Category.query.all()
    return render_template('categories.html', categories=categories)


@app.route('/warehouses')
@login_required
def list_warehouses():
    warehouses = Warehouse.query.all()
    return render_template('warehouses.html', warehouses=warehouses)


@app.route('/warehouses/add', methods=['GET', 'POST'])
@login_required
def add_warehouse():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        capacity = request.form.get('capacity')

        new_warehouse = Warehouse(name=name, location=location, capacity=int(capacity))
        db.session.add(new_warehouse)
        db.session.commit()
        flash('انبار جدید با موفقیت اضافه شد.', 'success')
        return redirect(url_for('list_warehouses'))

    return render_template('add_warehouse.html')


@app.route('/warehouses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_warehouse(id):
    warehouse = Warehouse.query.get_or_404(id)
    if request.method == 'POST':
        warehouse.name = request.form.get('name')
        warehouse.location = request.form.get('location')
        warehouse.capacity = int(request.form.get('capacity'))
        db.session.commit()
        flash('اطلاعات انبار با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('list_warehouses'))
    return render_template('edit_warehouse.html', warehouse=warehouse)


@app.route('/warehouses/<int:warehouse_id>/stock')
@login_required
def warehouse_stock(warehouse_id):
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    stocks = Stock.query.filter_by(warehouse_id=warehouse.id).all()
    return render_template('warehouse_stock.html', warehouse=warehouse, stocks=stocks)


if __name__ == '__main__':
    app.run(debug=True)