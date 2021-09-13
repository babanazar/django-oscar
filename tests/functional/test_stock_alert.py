from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.partner.models import StockAlert
from oscar.test import factories
from oscar.test.basket import add_service
from tests._site.apps.partner.models import StockRecord


class TestPlacingAnOrder(TestCase):

    def setUp(self):
        self.service = factories.create_service()
        self.stockrecord = factories.create_stockrecord(
            self.service, D('12.00'), num_in_stock=5)
        self.basket = factories.create_basket(empty=True)
        add_service(self.basket, service=self.service)

    def set_threshold(self, threshold):
        self.stockrecord.low_stock_threshold = threshold
        self.stockrecord.save()

    def test_correctly_allocates_stock(self):
        factories.create_order(basket=self.basket)

        record = StockRecord.objects.get(service=self.service)
        self.assertEqual(5, record.num_in_stock)
        self.assertEqual(1, record.num_allocated)
        self.assertEqual(4, record.net_stock_level)

    def test_does_not_raise_an_alert_if_threshold_not_broken(self):
        self.set_threshold(4)
        factories.create_order(basket=self.basket)

        alerts = StockAlert.objects.all()
        self.assertEqual(0, len(alerts))

    def test_raises_alert_when_threshold_is_reached(self):
        self.set_threshold(5)
        factories.create_order(basket=self.basket)

        alerts = StockAlert.objects.filter(
            stockrecord=self.stockrecord)
        self.assertEqual(1, len(alerts))

    def test_only_raises_an_alert_once(self):
        self.set_threshold(5)
        StockAlert.objects.create(stockrecord=self.stockrecord,
                                  threshold=10)
        factories.create_order(basket=self.basket)

        alerts = StockAlert.objects.filter(
            stockrecord=self.stockrecord)
        self.assertEqual(1, len(alerts))


class TestRestockingService(TestCase):

    def setUp(self):
        self.service = factories.create_service()
        self.stockrecord = factories.create_stockrecord(
            self.service, D('12.00'), num_in_stock=5)
        self.basket = factories.create_basket(empty=True)
        add_service(self.basket, service=self.service)

    def set_threshold(self, threshold):
        self.stockrecord.low_stock_threshold = threshold
        self.stockrecord.save()

    def test_closes_open_alert(self):
        # Set threshold as same as current level
        self.set_threshold(5)
        factories.create_order(basket=self.basket)

        alert = StockAlert.objects.get(stockrecord=self.stockrecord)
        self.assertEqual(StockAlert.OPEN, alert.status)

        # Restock service
        self.stockrecord.num_in_stock = 15
        self.stockrecord.save()

        alert = StockAlert.objects.get(stockrecord=self.stockrecord)
        self.assertEqual(StockAlert.CLOSED, alert.status)
        self.assertIsNotNone(alert.date_closed)
