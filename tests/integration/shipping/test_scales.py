from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.shipping.scales import Scale
from oscar.test import factories


class TestScales(TestCase):

    def test_weighs_uses_specified_attribute(self):
        scale = Scale(attribute_code='weight')
        p = factories.create_service(attributes={'weight': '1'})
        self.assertEqual(1, scale.weigh_service(p))

    def test_uses_default_weight_when_attribute_is_missing(self):
        scale = Scale(attribute_code='weight', default_weight=0.5)
        p = factories.create_service()
        self.assertEqual(0.5, scale.weigh_service(p))

    def test_raises_exception_when_attribute_is_missing(self):
        scale = Scale(attribute_code='weight')
        p = factories.create_service()
        with self.assertRaises(ValueError):
            scale.weigh_service(p)

    def test_returns_zero_for_empty_basket(self):
        basket = Basket()

        scale = Scale(attribute_code='weight')
        self.assertEqual(0, scale.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket(self):
        basket = factories.create_basket(empty=True)
        services = [
            factories.create_service(attributes={'weight': '1'},
                                     price=D('5.00')),
            factories.create_service(attributes={'weight': '2'},
                                     price=D('5.00'))]
        for service in services:
            basket.add(service)

        scale = Scale(attribute_code='weight')
        self.assertEqual(1 + 2, scale.weigh_basket(basket))

    def test_returns_correct_weight_for_nonempty_basket_with_line_quantities(self):
        basket = factories.create_basket(empty=True)
        services = [
            (factories.create_service(attributes={'weight': '1'},
                                      price=D('5.00')), 3),
            (factories.create_service(attributes={'weight': '2'},
                                      price=D('5.00')), 4)]
        for service, quantity in services:
            basket.add(service, quantity=quantity)

        scale = Scale(attribute_code='weight')
        self.assertEqual(1 * 3 + 2 * 4, scale.weigh_basket(basket))

    def test_decimals(self):
        basket = factories.create_basket(empty=True)
        service = factories.create_service(attributes={'weight': '0.3'},
                                           price=D('5.00'))
        basket.add(service)

        scale = Scale(attribute_code='weight')
        self.assertEqual(D('0.3'), scale.weigh_basket(basket))

        basket.add(service)
        self.assertEqual(D('0.6'), scale.weigh_basket(basket))

        basket.add(service)
        self.assertEqual(D('0.9'), scale.weigh_basket(basket))
