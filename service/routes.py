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
    """Base URL for our service"""
    return app.send_static_file("index.html")
    # """Root URL response"""
    # api_details = {
    #     "name": "Products REST API Service",
    #     "version": "0.1.0",
    #     "description": "This is the products service API. Below is how you use it.",
    #     "endpoints": [
    #         {
    #             "method": "POST",
    #             "path": "/products",
    #             "description": "Creates a new product with the data in the body that is posted",
    #         },
    #         {
    #             "method": "GET",
    #             "path": "/products/<product_id>",
    #             "description": "Returns a product based on its id",
    #         },
    #         {
    #             "method": "GET",
    #             "path": "/products",
    #             "description": "Returns a list of all products",
    #         },
    #         {
    #             "method": "PUT",
    #             "path": "/products/<product_id>",
    #             "description": "Updates a product based on its id with the data in the body that is posted",
    #         },
    #         {
    #             "method": "DELETE",
    #             "path": "/products/<product_id>",
    #             "description": "Deletes a product based on its id",
    #         },
    #     ],
    #     "status": "online",
    # }
    # return (jsonify(api_details), status.HTTP_200_OK)


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
# UPDATE A NEW PRODUCT PUT AND PATCH
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


@app.route("/products/<int:product_id>", methods=["PATCH"])
def patch_products(product_id):
    """
    Update a single product
    Returns 200 if the update is successful
    Returns 400 if no valid fields are provided for update
    """
    app.logger.info("Request to Update a product with id [%s]", product_id)

    # Attempt to find the Product and abort if not found
    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found."
        )

    # Check data in the request
    check_content_type("application/json")
    data = request.get_json()
    app.logger.info("Processing: %s", data)

    # Update the Product with the data in the request
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

    try:
        for key, value in data.items():
            if key in allowed_fields:
                setattr(product, key, value)
                touched = True
            else:
                app.logger.warning(
                    "Attempted to update non-existent or protected field: %s", key
                )
    except AttributeError:
        abort(
            status.HTTP_400_BAD_REQUEST, "Invalid JSON format: Expected a dictionary."
        )

    if touched:
        product.update()
        app.logger.info("Product with id [%s] updated!", product.id)
        return jsonify(product.serialize()), status.HTTP_200_OK
    # If nothing is valid in the request it will break the update and return a 400 error
    app.logger.warning("No valid fields provided for update.")
    abort(status.HTTP_400_BAD_REQUEST, "No valid fields provided for update.")


@app.route("/products/<int:product_id>/purchase", methods=["PUT"])
def purchase_products(product_id):
    """
    Purchase a Product

    This endpoint will perform a state-changing operation on a product
    outside of standard CRUD by marking it as unavailable.
    """
    app.logger.info("Request to Purchase a product with id [%s]", product_id)

    product = Product.find(product_id)
    if not product:
        abort(
            status.HTTP_404_NOT_FOUND, f"Product with id '{product_id}' was not found."
        )

    # Check if the product is already unavailable
    if not product.available:
        abort(
            status.HTTP_409_CONFLICT,
            f"Product with id '{product_id}' is already out of stock/unavailable.",
        )

    # Perform the state change
    product.available = False
    product.update()
    app.logger.info("Product with id [%s] has been purchased!", product.id)
    return jsonify(product.serialize()), status.HTTP_200_OK


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


######################################################################
# LIST ALL PRODUCTS WITH QUERY SUPPORT
######################################################################
@app.route("/products", methods=["GET"])  # fixed merge confict with ChatGPT
def list_products():
    """
    List all Products

    This endpoint returns a list of products, capped at 50 results
    """
    app.logger.info("Request to list Products...")

    # Get query parameters
    name = request.args.get("name")

    if name:
        app.logger.info("Filtering by name: %s", name)
        products = Product.find_by_name(name).limit(50).all()
    else:
        products = Product.query.limit(50).all()

    results = [product.serialize() for product in products]
    app.logger.info("Returning %d products", len(results))
    return jsonify(results), status.HTTP_200_OK


######################################################################
# DELETE A PRODUCT
######################################################################
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Delete a Product"""
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
