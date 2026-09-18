from app import app, db
from models import User, Supplier, Warehouse, Product, Stock, Transaction, Vehicle, Driver, ShipmentRoute


def seed_database():
    with app.app_context():
        # Clear existing data and create fresh tables
        db.drop_all()
        db.create_all()

        print("Database tables created.")

        # Create sample user accounts with specific roles
        admin = User(username="admin", role="Admin")
        admin.set_password("admin123")
        operator = User(username="operator1", role="Operator")
        operator.set_password("operator456")
        db.session.add_all([admin, operator])

        # Create sample suppliers
        supplier1 = Supplier(name="TechCorp Industries", contact_info="Tehran, Iran")
        supplier2 = Supplier(name="Global Logistics Co.", contact_info="Shiraz, Iran")
        db.session.add_all([supplier1, supplier2])

        # Create sample warehouses (name added to match model requirements)
        warehouse1 = Warehouse(name="انبار مرکزی", location="Central Warehouse - Tehran", capacity=5000)
        warehouse2 = Warehouse(name="انبار شمال", location="North Warehouse - Karaj", capacity=3000)
        db.session.add_all([warehouse1, warehouse2])

        db.session.commit()

        # Create sample products mapped to suppliers
        product1 = Product(name="Industrial Server Rack", sku="SRV-001", price=1200.0, supplier_id=supplier1.id)
        product2 = Product(name="Network Switch 24-Port", sku="SW-24-02", price=450.0, supplier_id=supplier2.id)
        db.session.add_all([product1, product2])
        db.session.commit()

        # Create sample vehicles (status removed unless added to Vehicle model)
        vehicle1 = Vehicle(plate_number="12الف345-تهران", model_name="ایفکو تن چرخ", capacity=10000.0)
        vehicle2 = Vehicle(plate_number="88ب991-ایران11", model_name="نیسان زامیاد", capacity=2000.0)
        db.session.add_all([vehicle1, vehicle2])

        # Create sample drivers
        driver1 = Driver(name="رضا حامی", license_number="DL-987654", phone="09123456789")
        driver2 = Driver(name="امین باقری", license_number="DL-123456", phone="09198765432")
        db.session.add_all([driver1, driver2])
        db.session.commit()

        # Create sample route
        route1 = ShipmentRoute(origin="انبار مرکزی تهران", destination="انبار منطقه شمال", vehicle_id=vehicle2.id,
                               driver_id=driver1.id, status="Dispatched")
        db.session.add(route1)
        db.session.commit()

        # Register initial stock levels across warehouses
        stock1 = Stock(product_id=product1.id, warehouse_id=warehouse1.id, quantity=50)
        stock2 = Stock(product_id=product2.id, warehouse_id=warehouse2.id, quantity=120)
        db.session.add_all([stock1, stock2])

        # Log initial inbound audit transactions
        tx1 = Transaction(
            product_id=product1.id,
            warehouse_id=warehouse1.id,
            user_id=admin.id,
            change_amount=50,
            transaction_type="INBOUND"
        )
        tx2 = Transaction(
            product_id=product2.id,
            warehouse_id=warehouse2.id,
            user_id=operator.id,
            change_amount=120,
            transaction_type="INBOUND"
        )
        db.session.add_all([tx1, tx2])

        db.session.commit()
        print("Database seeded successfully with enterprise test data!")


if __name__ == '__main__':
    seed_database()