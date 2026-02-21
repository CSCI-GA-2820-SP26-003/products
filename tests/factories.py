"""
Test Factory to make fake objects for testing
"""

import factory
from service.models import Product


class ProductFactory(factory.Factory):
    """Creates fake pets that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Product

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("name")
    sku = factory.Faker("bothify", text="??####??")
    description = factory.Faker("paragraph")
    price = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    image_url = factory.Faker("image_url")

    # Todo: Add your other attributes here...
