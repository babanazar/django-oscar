from decimal import Decimal as D
from unittest import mock

from django.test import TestCase

from oscar.apps.partner import availability, strategy


class TestStockRequiredMixin(TestCase):

    def setUp(self):
        self.mixin = strategy.StockRequired()
        self.service = mock.Mock()
        self.stockrecord = mock.Mock()
        self.stockrecord.price = D('12.00')

    def test_returns_unavailable_without_stockrecord(self):
        policy = self.mixin.availability_policy(
            self.service, None)
        self.assertIsInstance(policy, availability.Unavailable)

    def test_returns_available_when_service_class_doesnt_track_stock(self):
        service_class = mock.Mock(track_stock=False)
        self.service.get_service_class = mock.Mock(return_value=service_class)
        policy = self.mixin.availability_policy(
            self.service, self.stockrecord)
        self.assertIsInstance(policy, availability.Available)

    def test_returns_stockrequired_when_service_class_does_track_stock(self):
        service_class = mock.Mock(track_stock=True)
        self.service.get_service_class = mock.Mock(return_value=service_class)
        policy = self.mixin.availability_policy(
            self.service, self.stockrecord)
        self.assertIsInstance(policy, availability.StockRequired)
