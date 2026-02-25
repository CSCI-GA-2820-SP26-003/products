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

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Product
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    api_details = {
        "name": "Products REST API Service",
        "version": "0.1.0",
        "description": "This is the products service API. Below is how you use it.",
        "endpoints": [
            {
                "method": "POST",
                "path": "/products",
                "description": "Creates a new product with the data in the body that is posted",
            },
            {
                "method": "GET",
                "path": "/products/<product_id>",
                "description": "Returns a product based on its id",
            },
            {
                "method": "GET",
                "path": "/products",
                "description": "Returns a list of all products",
            },
            {
                "method": "PUT",
                "path": "/products/<product_id>",
                "description": "Updates a product based on its id with the data in the body that is posted",
            },
            {
                "method": "DELETE",
                "path": "/products/<product_id>",
                "description": "Deletes a product based on its id",
            },
        ],
        "status": "online",
    }
    return (jsonify(api_details), status.HTTP_200_OK)


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# CREATE A NEW PRODUCT
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Create a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    product = Product()
    # Get the data from the request and deserialize it
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product.deserialize(data)

    # Save the new Product to the database
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    # Return the location of the new Product
    # Todo: uncomment this code(just one single line below this) when get_products endpoint is implemented
    location_url = url_for("get_products", product_id=product.id, _external=True)

    return (
        jsonify(product.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# READ A PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """
    Retrieve a single Product

    This endpoint will return a Product based on it's id
    """
    app.logger.info("Request to Retrieve a product with id [%s]", product_id)

    # Attempt to find the Product and abort if not found
    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found."
        )

    app.logger.info("Returning product: %s", product.name)
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE A NEW PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Update a single product

    This endpoint will return whether it was successful or not
    """
    app.logger.info("Request to Update a product with id [%s]", product_id)

    # Attempt to find the Product and abort if not found
    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found."
        )

    # Update the Product with the data in the request
    check_content_type("application/json")
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product.deserialize(data)
    product.update()
    app.logger.info("Product with id [%s] updated!", product.id)
    return jsonify(product.serialize()), status.HTTP_200_OK


# Todo: Place your REST API code here ...


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


######################################################################
# Checks the ContentType of a request
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
