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
Product Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Product
"""

from flask import request, url_for, abort
from flask import current_app as app  # Import Flask application
from flask_restx import Api, Resource, fields, reqparse, inputs
from service.models import Product
from service.common import status  # HTTP Status Codes


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Products REST API Service",
    description="This is the products service API. Below is how you use it.",
    default="products",
    default_label="Products operations",
    doc="/apidocs",
    prefix="/api",
)

# ── Swagger Models ────────────────────────────────────────────────────────────

create_model = api.model(
    "Product",
    {
        "name": fields.String(required=True, description="The name of the Product"),
        "sku": fields.String(
            required=True, description="The unique Stock Keeping Unit identifier"
        ),
        "description": fields.String(
            required=False, description="A description of the Product"
        ),
        "price": fields.Fixed(
            decimals=2, required=True, description="The price of the Product"
        ),
        "image_url": fields.String(
            required=False, description="URL to the Product image"
        ),
        "available": fields.Boolean(
            required=True, description="Is the Product available for purchase?"
        ),
        "category": fields.String(
            required=True, description="The category of the Product"
        ),
    },
)

product_model = api.inherit(
    "ProductModel",
    create_model,
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique id assigned internally by the service",
        ),
    },
)

# ── Query String Arguments ────────────────────────────────────────────────────

product_args = reqparse.RequestParser()
product_args.add_argument(
    "name", type=str, location="args", required=False, help="Filter Products by name"
)
product_args.add_argument(
    "category",
    type=str,
    location="args",
    required=False,
    help="Filter Products by category",
)
product_args.add_argument(
    "available",
    type=inputs.boolean,
    location="args",
    required=False,
    help="Filter Products by availability",
)


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@api.route("/products", strict_slashes=False)
class ProductCollection(Resource):
    """Handles /api/products"""

    ######################################################################
    # LIST ALL PRODUCTS
    ######################################################################
    @api.doc("list_products")
    @api.expect(product_args)
    @api.marshal_list_with(product_model)
    def get(self):
        """
        List all Products

        Returns a list of products, capped at 50 results.
        Supports optional query parameters: name, category, available.
        """
        app.logger.info("Request to list Products...")

        args = product_args.parse_args()
        name = args.get("name")
        category = args.get("category")
        available = args.get("available")

        query = Product.query

        if name:
            app.logger.info("Filtering by name: %s", name)
            query = query.filter(Product.name.ilike(f"%{name}%"))

        if category:
            app.logger.info("Filtering by category: %s", category)
            query = query.filter(Product.category.ilike(category))

        if available is not None:
            app.logger.info("Filtering by available: %s", available)
            query = query.filter(Product.available == available)

        products = query.limit(50).all()
        results = [product.serialize() for product in products]
        app.logger.info("Returning %d products", len(results))
        return results, status.HTTP_200_OK

    ######################################################################
    # CREATE A NEW PRODUCT
    ######################################################################
    @api.doc("create_product")
    @api.expect(create_model)
    @api.response(400, "The posted data was not valid")
    @api.response(415, "Unsupported Media Type")
    @api.marshal_with(product_model, code=201)
    def post(self):
        """
        Create a Product
        This endpoint will create a Product based on the data in the body that is posted
        """
        app.logger.info("Request to Create a Product...")
        check_content_type("application/json")

        product = Product()
        data = request.get_json()
        app.logger.info("Processing: %s", data)
        product.deserialize(data)

        product.create()
        app.logger.info("Product with new id [%s] saved!", product.id)

        location_url = url_for(
            "product_resource", product_id=product.id, _external=True
        )

        return (
            product.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


@api.route("/products/<int:product_id>", strict_slashes=False)
@api.param("product_id", "The Product identifier")
class ProductResource(Resource):
    """Handles /api/products/<product_id>"""

    ######################################################################
    # READ A PRODUCT
    ######################################################################
    @api.doc("get_product")
    @api.response(404, "Product not found")
    @api.marshal_with(product_model)
    def get(self, product_id):
        """
        Retrieve a single Product
        This endpoint will return a Product based on its id
        """
        app.logger.info("Request to Retrieve a product with id [%s]", product_id)

        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )

        app.logger.info("Returning product: %s", product.name)
        return product.serialize(), status.HTTP_200_OK

    ######################################################################
    # UPDATE A PRODUCT (PUT)
    ######################################################################
    @api.doc("update_product")
    @api.expect(create_model)
    @api.response(404, "Product not found")
    @api.response(400, "The posted data was not valid")
    @api.response(415, "Unsupported Media Type")
    @api.marshal_with(product_model)
    def put(self, product_id):
        """
        Update a Product
        This endpoint will update a Product based on the data in the body
        """
        app.logger.info("Request to Update a product with id [%s]", product_id)

        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )

        check_content_type("application/json")
        data = request.get_json()
        app.logger.info("Processing: %s", data)
        product.deserialize(data)
        product.update()
        app.logger.info("Product with id [%s] updated!", product.id)
        return product.serialize(), status.HTTP_200_OK

    ######################################################################
    # PARTIAL UPDATE A PRODUCT (PATCH)
    ######################################################################
    @api.doc("patch_product")
    @api.expect(create_model)
    @api.response(400, "No valid fields provided or invalid JSON")
    @api.response(404, "Product not found")
    @api.response(415, "Unsupported Media Type")
    @api.marshal_with(product_model)
    def patch(self, product_id):
        """
        Partially Update a Product
        Returns 200 if the update is successful
        Returns 400 if no valid fields are provided for update
        """
        app.logger.info("Request to Patch a product with id [%s]", product_id)

        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )

        check_content_type("application/json")
        data = request.get_json()
        app.logger.info("Processing: %s", data)

        allowed_fields = [
            "name",
            "description",
            "price",
            "sku",
            "image_url",
            "available",
            "category",
        ]
        touched = False

        if not isinstance(data, dict):
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Invalid JSON format: Expected a dictionary.",
            )

        for key, value in data.items():
            if key in allowed_fields:
                setattr(product, key, value)
                touched = True
            else:
                app.logger.warning(
                    "Attempted to update non-existent or protected field: %s", key
                )

        if touched:
            product.update()
            app.logger.info("Product with id [%s] updated!", product.id)
            return product.serialize(), status.HTTP_200_OK

        app.logger.warning("No valid fields provided for update.")
        abort(status.HTTP_400_BAD_REQUEST, "No valid fields provided for update.")

    ######################################################################
    # DELETE A PRODUCT
    ######################################################################
    @api.doc("delete_product")
    @api.response(204, "Product deleted")
    def delete(self, product_id):
        """
        Delete a Product
        This endpoint will delete a Product based on its id
        """
        app.logger.info("Request to Delete a product with id [%s]", product_id)

        product = Product.find(product_id)
        if not product:
            app.logger.info(
                "Product with id [%s] was not found; treating delete as idempotent",
                product_id,
            )
            return "", status.HTTP_204_NO_CONTENT

        product.delete()
        return "", status.HTTP_204_NO_CONTENT


@api.route("/products/<int:product_id>/purchase", strict_slashes=False)
@api.param("product_id", "The Product identifier")
class PurchaseResource(Resource):
    """Handles /api/products/<product_id>/purchase"""

    ######################################################################
    # PURCHASE A PRODUCT
    ######################################################################
    @api.doc("purchase_product")
    @api.response(404, "Product not found")
    @api.response(409, "Product is already unavailable")
    @api.marshal_with(product_model)
    def put(self, product_id):
        """
        Purchase a Product
        This endpoint marks a product as unavailable after purchase
        """
        app.logger.info("Request to Purchase a product with id [%s]", product_id)

        product = Product.find(product_id)
        if not product:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Product with id '{product_id}' was not found.",
            )

        if not product.available:
            abort(
                status.HTTP_409_CONFLICT,
                f"Product with id '{product_id}' is already out of stock/unavailable.",
            )

        product.available = False
        product.update()
        app.logger.info("Product with id [%s] has been purchased!", product.id)
        return product.serialize(), status.HTTP_200_OK


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )
