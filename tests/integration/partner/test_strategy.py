from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.basket.models import Line
from oscar.apps.catalogue import models
from oscar.apps.partner import strategy
from oscar.test import factories


class TestDefaultStrategy(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()

    def test_no_stockrecords(self):
        service = factories.create_service()
        info = self.strategy.fetch_for_service(service)
        self.assertFalse(info.availability.is_available_to_buy)
        self.assertIsNone(info.price.incl_tax)

    def test_one_stockrecord(self):
        service = factories.create_service(price=D('1.99'), num_in_stock=4)
        info = self.strategy.fetch_for_service(service)
        self.assertTrue(info.availability.is_available_to_buy)
        self.assertEqual(D('1.99'), info.price.excl_tax)
        self.assertEqual(D('1.99'), info.price.incl_tax)

    def test_service_which_doesnt_track_stock(self):
        service_class = models.ServiceClass.objects.create(
            name="Digital", track_stock=False)
        service = factories.create_service(
            service_class=service_class,
            price=D('1.99'), num_in_stock=None)
        info = self.strategy.fetch_for_service(service)
        self.assertTrue(info.availability.is_available_to_buy)

    def test_line_method_is_same_as_service_one(self):
        service = factories.create_service()
        line = Line(service=service)
        info = self.strategy.fetch_for_line(line)
        self.assertFalse(info.availability.is_available_to_buy)
        self.assertIsNone(info.price.incl_tax)

    def test_free_service_is_available_to_buy(self):
        service = factories.create_service(price=D('0'), num_in_stock=1)
        info = self.strategy.fetch_for_service(service)
        self.assertTrue(info.availability.is_available_to_buy)
        self.assertTrue(info.price.exists)

    def test_availability_does_not_require_price(self):
        # regression test for https://github.com/django-oscar/django-oscar/issues/2664
        # The availability policy should be independent of price.
        service_class = factories.ServiceClassFactory(track_stock=False)
        service = factories.ServiceFactory(service_class=service_class, stockrecords=[])
        factories.StockRecordFactory(price=None, service=service)
        info = self.strategy.fetch_for_service(service)
        self.assertTrue(info.availability.is_available_to_buy)


class TestDefaultStrategyForParentServiceWhoseVariantsHaveNoStockRecords(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()
        parent = factories.create_service(structure='parent')
        for x in range(3):
            factories.create_service(parent=parent)
        self.info = self.strategy.fetch_for_parent(parent)

    def test_specifies_service_is_unavailable(self):
        self.assertFalse(self.info.availability.is_available_to_buy)

    def test_specifies_correct_availability_code(self):
        self.assertEqual('unavailable', self.info.availability.code)

    def test_specifies_service_has_no_price(self):
        self.assertFalse(self.info.price.exists)


class TestDefaultStrategyForParentServiceWithInStockVariant(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()
        parent = factories.create_service(structure='parent')
        factories.create_service(parent=parent, price=D('10.00'),
                                 num_in_stock=3)
        for x in range(2):
            factories.create_service(parent=parent)
        self.info = self.strategy.fetch_for_parent(parent)

    def test_specifies_service_is_available(self):
        self.assertTrue(self.info.availability.is_available_to_buy)

    def test_specifies_correct_availability_code(self):
        self.assertEqual('available', self.info.availability.code)

    def test_specifies_service_has_correct_price(self):
        self.assertEqual(D('10.00'), self.info.price.incl_tax)


class TestDefaultStrategyForParentServiceWithOutOfStockVariant(TestCase):

    def setUp(self):
        self.strategy = strategy.Default()
        parent = factories.create_service(structure='parent')
        factories.create_service(
            parent=parent, price=D('10.00'), num_in_stock=0)
        for x in range(2):
            factories.create_service(parent=parent)
        self.info = self.strategy.fetch_for_parent(parent)

    def test_specifies_service_is_unavailable(self):
        self.assertFalse(self.info.availability.is_available_to_buy)

    def test_specifies_correct_availability_code(self):
        self.assertEqual('unavailable', self.info.availability.code)

    def test_specifies_service_has_correct_price(self):
        self.assertEqual(D('10.00'), self.info.price.incl_tax)


class TestFixedRateTax(TestCase):

    def test_pricing_policy_unavailable_if_no_price_excl_tax(self):
        service = factories.ServiceFactory(stockrecords=[])
        factories.StockRecordFactory(price=None, service=service)
        info = strategy.UK().fetch_for_service(service)
        self.assertFalse(info.price.exists)


class TestDeferredTax(TestCase):

    def test_pricing_policy_unavailable_if_no_price_excl_tax(self):
        service = factories.ServiceFactory(stockrecords=[])
        factories.StockRecordFactory(price=None, service=service)
        info = strategy.US().fetch_for_service(service)
        self.assertFalse(info.price.exists)
