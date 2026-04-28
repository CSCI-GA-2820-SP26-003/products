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
TestProduct API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Product
from .factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test product",
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["price"], str(test_product.price))
        self.assertEqual(new_product["sku"], test_product.sku)
        self.assertEqual(new_product["image_url"], test_product.image_url)
        self.assertEqual(new_product["description"], test_product.description)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["price"], str(test_product.price))
        self.assertEqual(new_product["sku"], test_product.sku)
        self.assertEqual(new_product["image_url"], test_product.image_url)
        self.assertEqual(new_product["description"], test_product.description)

    def test_create_product_missing_name(self):
        """It should return 400 when required fields are missing"""
        response = self.client.post(
            BASE_URL,
            json={
                "sku": "MISSING-001",
                "description": "No name provided",
                "price": 10.00,
                "image_url": "https://example.com/test.png",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.get_json()
        self.assertIn("missing", data["message"])

    def test_get_product(self):
        """It should Get a single Product"""
        test_product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_update_product(self):
        """It should Update a single Product"""
        test_product = self._create_products(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_product_data = response.get_json()
        new_product_data["description"] = "Updated Description"
        original_id = new_product_data["id"]

        response = self.client.put(
            f"{BASE_URL}/{test_product.id}",
            json=new_product_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(updated_product["id"], original_id)
        self.assertEqual(updated_product["description"], "Updated Description")

    def test_update_product_partial(self):
        """It should Update only the price of a Product"""
        test_product = self._create_products(1)[0]
        new_data = {"price": 150.00}
        response = self.client.patch(
            f"{BASE_URL}/{test_product.id}",
            json=new_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_product = response.get_json()
        self.assertEqual(float(updated_product["price"]), 150.0)
        self.assertEqual(updated_product["name"], test_product.name)

    def test_update_product_invalid_data(self):
        """It should return 400 when sending invalid fields"""
        test_product = self._create_products(1)[0]
        bad_data = {"unknown_field": "some_value"}
        response = self.client.patch(
            f"{BASE_URL}/{test_product.id}",
            json=bad_data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_malformed_json(self):
        """It should return 400 for malformed JSON structure"""
        test_product = self._create_products(1)[0]
        response = self.client.patch(
            f"{BASE_URL}/{test_product.id}",
            data="this is just a string, not a dict",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_products(self):
        """It should return a list of Products"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)

    def test_list_products_empty(self):
        """It should return an empty list when no Products exist"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_list_products_limit(self):
        """It should return at most 50 Products"""
        self._create_products(55)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 50)

    def test_delete_product(self):
        """It should Delete a Product"""
        test_product = self._create_products(1)[0]

        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_not_found(self):
        """It should return 204 when deleting a Product that is not found"""
        response = self.client.delete(f"{BASE_URL}/9999")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_product_is_idempotent(self):
        """It should allow deleting the same Product more than once"""
        test_product = self._create_products(1)[0]

        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_product_not_found(self):
        """It should not update a product that is not found"""
        response = self.client.put(
            f"{BASE_URL}/9999",
            json={"name": "Test"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_405_handler_json(self):
        """It should return JSON for 405"""
        response = self.client.post(f"{BASE_URL}/1")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = response.get_json()
        self.assertIn("message", data)

    def test_404_handler_json(self):
        """It should return JSON for 404"""
        response = self.client.get("/no_route_here")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("message", data)

    def test_400_bad_request(self):
        """It should return 415 for bad content type"""
        response = self.client.post(BASE_URL, data="not json")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_415_unsupported_media_type(self):
        """It should return 415 if wrong content type"""
        response = self.client.post(
            BASE_URL,
            json={"name": "Test"},
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST PURCHASE (ACTION)
    # ----------------------------------------------------------
    def test_purchase_a_product(self):
        """It should Purchase a Product"""
        # Create a test product that is available
        test_product = self._create_products(1)[0]
        test_product.available = True
        test_product.available = True

        # flaky test fixed by Zhen:
        response = self.client.put(
            f"{BASE_URL}/{test_product.id}", json=test_product.serialize()
        )

        # Ensure it is actually available before the test
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.get_json()["available"])

        # Perform the purchase action
        response = self.client.put(f"{BASE_URL}/{test_product.id}/purchase")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the state change
        data = response.get_json()
        self.assertFalse(data["available"])

    def test_purchase_not_found(self):
        """It should not Purchase a Product that is not found"""
        response = self.client.put(f"{BASE_URL}/0/purchase")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_purchase_already_sold(self):
        """It should not Purchase a Product that is already unavailable"""
        test_product = self._create_products(1)[0]
        # Initial purchase
        self.client.put(f"{BASE_URL}/{test_product.id}/purchase")
        # Second purchase attempt
        response = self.client.put(f"{BASE_URL}/{test_product.id}/purchase")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        # Safely get JSON
        data = response.get_json()
        self.assertIsNotNone(data, "Response body should not be empty")
        self.assertIn("already out of stock", data["message"])

    # ----------------------------------------------------------
    # TEST LIST FILTERING
    # ----------------------------------------------------------
    def test_list_products_filter_by_name(self):
        """It should return only products matching the given name"""
        product1 = ProductFactory(name="Widget Alpha")
        product2 = ProductFactory(name="Gadget Beta")
        self.client.post(BASE_URL, json=product1.serialize())
        self.client.post(BASE_URL, json=product2.serialize())

        response = self.client.get(f"{BASE_URL}?name=Widget")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertIn("Widget", data[0]["name"])

    def test_list_products_filter_by_category(self):
        """It should return only products matching the given category"""
        clothing = ProductFactory(category="Clothing", available=True)
        electronics = ProductFactory(category="Electronics", available=True)
        self.client.post(BASE_URL, json=clothing.serialize())
        self.client.post(BASE_URL, json=electronics.serialize())

        response = self.client.get(f"{BASE_URL}?category=Clothing")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["category"], "Clothing")

    def test_list_products_filter_by_available(self):
        """It should return only available products when available=true"""
        available_product = ProductFactory(available=True)
        unavailable_product = ProductFactory(available=False)
        self.client.post(BASE_URL, json=available_product.serialize())
        self.client.post(BASE_URL, json=unavailable_product.serialize())

        response = self.client.get(f"{BASE_URL}?available=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertTrue(len(data) >= 1)
        for product in data:
            self.assertTrue(product["available"])

    def test_list_products_filter_by_category_and_available(self):
        """It should filter by both category and available simultaneously"""
        clothing_available = ProductFactory(category="Clothing", available=True)
        clothing_unavailable = ProductFactory(category="Clothing", available=False)
        electronics_available = ProductFactory(category="Electronics", available=True)
        self.client.post(BASE_URL, json=clothing_available.serialize())
        self.client.post(BASE_URL, json=clothing_unavailable.serialize())
        self.client.post(BASE_URL, json=electronics_available.serialize())

        response = self.client.get(f"{BASE_URL}?category=Clothing&available=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["category"], "Clothing")
        self.assertTrue(data[0]["available"])
