"""
Models for Product

All of the models are stored in this module
"""

import logging
from decimal import Decimal, InvalidOperation
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Product(db.Model):
    """
    Class that represents a Product
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    available = db.Column(db.Boolean, nullable=False, default=True)
    category = db.Column(db.String(63), nullable=False, default="")

    def __repr__(self):
        return f"<Product {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Product to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # pylint: disable=invalid-name
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates a Product to the database
        """
        logger.info("Saving %s", self.name)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes a Product from the data store"""
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Product into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "price": str(self.price),
            "image_url": self.image_url,
            "available": self.available,
            "category": self.category,
        }

    def deserialize(self, data):
        """
        Deserializes a Product from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.name = data["name"]
            self.sku = data["sku"]
            self.description = data.get("description")
            self.image_url = data.get("image_url")
            self.category = data.get("category", "")

            # available must be a boolean
            if "available" in data:
                if not isinstance(data["available"], bool):
                    raise DataValidationError(
                        "Invalid type for boolean [available]: "
                        + str(type(data["available"]))
                    )
                self.available = data["available"]
            else:
                self.available = True

            # price's format issue

            price_val = data.get("price")
            if price_val is not None:
                try:
                    self.price = Decimal(str(price_val))
                except (InvalidOperation, TypeError) as exc:
                    raise DataValidationError(
                        f"Invalid price format: {price_val}"
                    ) from exc
            else:
                raise DataValidationError("Price is required")

        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Product: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Product: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Products in the database"""
        logger.info("Processing all Products")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Product by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all Products with the given name

        Args:
            name (string): the name of the Products you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name.ilike(f"%{name}%"))

    @classmethod
    def find_by_category(cls, category):
        """Returns all Products with the given category (exact match, case-insensitive)

        Args:
            category (string): the category of the Products you want to match
        """
        logger.info("Processing category query for %s ...", category)
        return cls.query.filter(cls.category.ilike(category))

    @classmethod
    def find_by_availability(cls, available=True):
        """Returns all Products by their availability

        Args:
            available (boolean): True for available products, False otherwise
        """
        logger.info("Processing availability query for %s ...", available)
        return cls.query.filter(cls.available == available)

    @classmethod
    def find_by_price_range(cls, minimum_price, maximum_price):
        """Returns all Products within the given price range

        Args:
            minimum_price (Decimal): the minimum price
            maximum_price (Decimal): the maximum price
        """
        logger.info(
            "Processing price range query for %s to %s ...",
            minimum_price,
            maximum_price,
        )
        return cls.query.filter(cls.price >= minimum_price, cls.price <= maximum_price)
