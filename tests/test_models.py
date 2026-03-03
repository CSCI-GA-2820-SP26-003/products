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

    # Todo: Add your test cases here...

    def test_deserialize_missing_name(self):
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

    def test_deserialize_missing_name(self):
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({"sku": "123", "price": "10.00"})

    def test_deserialize_bad_type(self):
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize(None)

    def test_deserialize_invalid_price(self):
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
        product = ProductFactory()
        product.create()
        product.description = "Updated"
        product.update()
        updated = Product.find(product.id)
        self.assertEqual(updated.description, "Updated")

    def test_delete_product(self):
        product = ProductFactory()
        product.create()
        product.delete()
        result = Product.find(product.id)
        self.assertIsNone(result)

    def test_serialize(self):
        product = ProductFactory()
        product.create()
        data = product.serialize()
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["price"], str(product.price))

    def test_find_by_name(self):
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
            raise Exception("DB failure")

        db.session.commit = broken_commit

        with self.assertRaises(DataValidationError):
            product.delete()

        # Restore original commit
        db.session.commit = original_commit
