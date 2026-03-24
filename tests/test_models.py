######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Test cases for Pet Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from decimal import Decimal
from service.models import Product, DataValidationError, db
from .factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  Product   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProduct(TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    # PROF's ORIGINAL EXAMPLE
    # def test_example_replace_this(self):
    #     """It should create a Product"""
    #     # Todo: Remove this test case example
    #     resource = ProductFactory()
    #     resource.create()
    #     self.assertIsNotNone(resource.id)
    #     found = Product.all()
    #     self.assertEqual(len(found), 1)
    #     data = Product.find(resource.id)
    #     self.assertEqual(data.name, resource.name)

    def test_create_product(self):
        """It should create a Product"""
        product = ProductFactory()
        product.create()
        self.assertIsNotNone(product.id)
        found = Product.all()
        self.assertEqual(len(found), 1)
        data = Product.find(product.id)
        self.assertEqual(data.name, product.name)
        self.assertEqual(data.price, product.price)
        self.assertEqual(data.description, product.description)
        self.assertEqual(data.image_url, product.image_url)
        self.assertEqual(data.sku, product.sku)

    # Add your test cases here...

    def test_deserialize_missing_name(self):
        """Raises an error if missing product name"""
        product = Product()
        with self.assertRaises(Exception):
            product.deserialize(
                {
                    "price": "10.00",
                    "sku": "123",
                    "image_url": "url",
                    "description": "desc",
                }
            )

    def test_deserialize_missing_name2(self):
        """Raise an error if missing required fields"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({"sku": "123", "price": "10.00"})

    def test_deserialize_bad_type(self):
        """Raises an error if nothing is passed"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(None)

    def test_deserialize_invalid_price(self):
        """Raises an error if price is the wrong datatype"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(
                {
                    "name": "Test",
                    "sku": "123",
                    "description": "desc",
                    "image_url": "url",
                    "price": "not-a-number",
                }
            )

    def test_update_product(self):
        """This checks if update is working correctly"""
        product = ProductFactory()
        product.create()
        product.description = "Updated"
        product.update()
        updated = Product.find(product.id)
        self.assertEqual(updated.description, "Updated")

    def test_delete_product(self):
        """This checks if delete is working correctly"""
        product = ProductFactory()
        product.create()
        product.delete()
        result = Product.find(product.id)
        self.assertIsNone(result)

    def test_serialize(self):
        """This checks if the product is created correctly with the given values"""
        product = ProductFactory()
        product.create()
        data = product.serialize()
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["price"], str(product.price))

    def test_find_by_name(self):
        """This checks if find is working correctly"""
        product = ProductFactory(name="UniqueName")
        product.create()
        results = Product.find_by_name("UniqueName").all()
        self.assertEqual(len(results), 1)

    def test_create_rollback(self):
        """Force create() exception"""
        product = Product()
        product.name = None  # name is nullable=False → 會爆
        product.sku = "bad"
        product.price = 10

        with self.assertRaises(DataValidationError):
            product.create()

    def test_update_rollback(self):
        """Force update() exception"""
        product = ProductFactory()
        product.create()
        product.name = None  # 破壞 constraint

        with self.assertRaises(DataValidationError):
            product.update()

    def test_delete_rollback(self):
        """Force delete() exception properly"""
        product = ProductFactory()
        product.create()

        # Monkey patch commit to force failure
        original_commit = db.session.commit

        def broken_commit():
            # changed Exception to DataValidationError to pass pylint
            raise DataValidationError("DB failure")

        db.session.commit = broken_commit

        with self.assertRaises(DataValidationError):
            product.delete()

        # Restore original commit
        db.session.commit = original_commit

    # ----------------------------------------------------------
    # TEST NEW FIELDS
    # ----------------------------------------------------------

    def test_create_product_with_defaults(self):
        """It should create a Product with default available and category"""
        product = Product(name="Test", sku="DEFAULT01", price=Decimal("10.00"))
        product.create()
        found = Product.find(product.id)
        self.assertTrue(found.available)
        self.assertEqual(found.category, "")

    def test_serialize_includes_new_fields(self):
        """It should include available and category in serialized output"""
        product = ProductFactory()
        product.create()
        data = product.serialize()
        self.assertIn("available", data)
        self.assertIn("category", data)
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category)

    def test_deserialize_available_true(self):
        """It should deserialize available as True"""
        product = Product()
        data = {
            "name": "Test",
            "sku": "AVAIL01",
            "price": "25.00",
            "available": True,
        }
        product.deserialize(data)
        self.assertTrue(product.available)

    def test_deserialize_available_false(self):
        """It should deserialize available as False"""
        product = Product()
        data = {
            "name": "Test",
            "sku": "AVAIL02",
            "price": "25.00",
            "available": False,
        }
        product.deserialize(data)
        self.assertFalse(product.available)

    def test_deserialize_available_default(self):
        """It should default available to True when not provided"""
        product = Product()
        data = {
            "name": "Test",
            "sku": "AVAIL03",
            "price": "25.00",
        }
        product.deserialize(data)
        self.assertTrue(product.available)

    def test_deserialize_available_bad_type(self):
        """It should raise error when available is not a boolean"""
        product = Product()
        data = {
            "name": "Test",
            "sku": "AVAIL04",
            "price": "25.00",
            "available": "yes",
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_category(self):
        """It should deserialize category correctly"""
        product = Product()
        data = {
            "name": "Test",
            "sku": "CAT01",
            "price": "25.00",
            "category": "Electronics",
        }
        product.deserialize(data)
        self.assertEqual(product.category, "Electronics")

    def test_deserialize_category_default(self):
        """It should default category to empty string when not provided"""
        product = Product()
        data = {
            "name": "Test",
            "sku": "CAT02",
            "price": "25.00",
        }
        product.deserialize(data)
        self.assertEqual(product.category, "")

    # ----------------------------------------------------------
    # TEST QUERY METHODS
    # ----------------------------------------------------------

    def test_find_by_name_partial_match(self):
        """It should find Products by partial name (case-insensitive)"""
        ProductFactory(name="Blue Shirt", sku="SHIRT01").create()
        ProductFactory(name="Red Shirt", sku="SHIRT02").create()
        ProductFactory(name="Blue Pants", sku="PANTS01").create()
        results = Product.find_by_name("shirt").all()
        self.assertEqual(len(results), 2)

    def test_find_by_name_no_match(self):
        """It should return empty list when no name matches"""
        ProductFactory(name="Blue Shirt", sku="NM01").create()
        results = Product.find_by_name("nonexistent").all()
        self.assertEqual(len(results), 0)

    def test_find_by_category(self):
        """It should find Products by category (case-insensitive)"""
        ProductFactory(name="Item1", sku="CATQ01", category="Clothing").create()
        ProductFactory(name="Item2", sku="CATQ02", category="Clothing").create()
        ProductFactory(name="Item3", sku="CATQ03", category="Electronics").create()
        results = Product.find_by_category("clothing").all()
        self.assertEqual(len(results), 2)

    def test_find_by_availability_true(self):
        """It should find only available Products"""
        ProductFactory(name="A1", sku="AV01", available=True).create()
        ProductFactory(name="A2", sku="AV02", available=True).create()
        ProductFactory(name="A3", sku="AV03", available=False).create()
        results = Product.find_by_availability(True).all()
        self.assertEqual(len(results), 2)

    def test_find_by_availability_false(self):
        """It should find only unavailable Products"""
        ProductFactory(name="A4", sku="AV04", available=True).create()
        ProductFactory(name="A5", sku="AV05", available=False).create()
        results = Product.find_by_availability(False).all()
        self.assertEqual(len(results), 1)

    def test_find_by_price_range(self):
        """It should find Products within a price range"""
        ProductFactory(name="P1", sku="PR01", price=Decimal("5.00")).create()
        ProductFactory(name="P2", sku="PR02", price=Decimal("25.00")).create()
        ProductFactory(name="P3", sku="PR03", price=Decimal("50.00")).create()
        ProductFactory(name="P4", sku="PR04", price=Decimal("75.00")).create()
        results = Product.find_by_price_range(Decimal("10.00"), Decimal("50.00")).all()
        self.assertEqual(len(results), 2)

    def test_find_by_price_range_no_match(self):
        """It should return empty when no products in price range"""
        ProductFactory(name="P5", sku="PR05", price=Decimal("5.00")).create()
        results = Product.find_by_price_range(
            Decimal("100.00"), Decimal("200.00")
        ).all()
        self.assertEqual(len(results), 0)
