from django.test import TestCase

from sandbox.oscar.apps.catalogue import models


class TestServiceClassModel(TestCase):

    def test_slug_is_auto_created(self):
        books = models.ServiceClass.objects.create(
            name="Book",
        )
        self.assertEqual('book', books.slug)

    def test_has_attribute_for_whether_shipping_is_required(self):
        models.ServiceClass.objects.create(
            name="Download",
            requires_shipping=False,
        )
