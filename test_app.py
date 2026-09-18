import unittest
from app import app, db
from models import User, Product, Warehouse, Supplier, Stock, Transaction

class SupplyChainTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and initialize a temporary in-memory database."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up the database session and drop tables after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_dashboard_route(self):
        """Test if the dashboard route responds successfully with status 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_product_creation(self):
        """Test relational integrity and product creation mapped to a supplier."""
        with app.app_context():
            supplier = Supplier(name="Test Supplier", contact_info="Test Address")
            db.session.add(supplier)
            db.commit_if_needed = db.session.commit()
            db.session.commit()

            product = Product(name="Test Item", sku="TST-999", price=100.0, supplier_id=supplier.id)
            db.session.add(product)
            db.session.commit()

            saved_product = Product.query.filter_by(sku="TST-999").first()
            self.assertIsNotNone(saved_product)
            self.assertEqual(saved_product.name, "Test Item")
            self.assertEqual(saved_product.supplier.name, "Test Supplier")

if __name__ == '__main__':
    unittest.main()
