# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.catalogue.models import Option
from oscar.apps.partner import availability, prices, strategy
from oscar.test import factories
from oscar.test.factories import (
    BasketFactory, BasketLineAttributeFactory, OptionFactory, ServiceFactory)


class TestANewBasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()

    def test_has_zero_lines(self):
        self.assertEqual(0, self.basket.num_lines)

    def test_has_zero_items(self):
        self.assertEqual(0, self.basket.num_items)

    def test_doesnt_contain_vouchers(self):
        self.assertFalse(self.basket.contains_a_voucher)

    def test_can_be_edited(self):
        self.assertTrue(self.basket.can_be_edited)

    def test_is_empty(self):
        self.assertTrue(self.basket.is_empty)

    def test_is_not_submitted(self):
        self.assertFalse(self.basket.is_submitted)

    def test_has_no_applied_offers(self):
        self.assertEqual({}, self.basket.applied_offers())


class TestBasketLine(TestCase):

    def test_description(self):
        basket = BasketFactory()
        service = ServiceFactory(title="A service")
        basket.add_service(service)

        line = basket.lines.first()
        self.assertEqual(line.description, "A service")

    def test_description_with_attributes(self):
        basket = BasketFactory()
        service = ServiceFactory(title="A service")
        basket.add_service(service)

        line = basket.lines.first()
        BasketLineAttributeFactory(
            line=line, value='\u2603', option__name='with')
        self.assertEqual(line.description, "A service (with = '\u2603')")

    def test_create_line_reference(self):
        basket = BasketFactory()
        service = ServiceFactory(title="A service")
        option = OptionFactory(name="service_option", code="service_option")
        option_service = ServiceFactory(title='Asunción')
        options = [{'option': option, 'value': option_service}]
        basket.add_service(service, options=options)

    def test_basket_lines_queryset_is_ordered(self):
        # This is needed to make sure a formset is not performing the query
        # again with an order_by clause (losing all calculated discounts)
        basket = BasketFactory()
        service = ServiceFactory(title="A service")
        another_service = ServiceFactory(title="Another service")
        basket.add_service(service)
        basket.add_service(another_service)
        queryset = basket.all_lines()
        self.assertTrue(queryset.ordered)

    def test_line_tax_for_zero_tax_strategies(self):
        basket = Basket()
        basket.strategy = strategy.Default()
        service = factories.create_service()
        # Tax for the default strategy will be 0
        factories.create_stockrecord(
            service, price=D('75.00'), num_in_stock=10)
        basket.add(service, 1)

        self.assertEqual(basket.lines.first().line_tax, D('0'))

    def test_line_tax_for_unknown_tax_strategies(self):

        class UnknownTaxStrategy(strategy.Default):
            """ A test strategy where the tax is not known """

            def pricing_policy(self, service, stockrecord):
                return prices.FixedPrice('GBP', stockrecord.price, tax=None)

        basket = Basket()
        basket.strategy = UnknownTaxStrategy()
        service = factories.create_service()
        factories.create_stockrecord(service, num_in_stock=10)
        basket.add(service, 1)

        self.assertEqual(basket.lines.first().line_tax, None)


class TestAddingAServiceToABasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.service = factories.create_service()
        self.record = factories.create_stockrecord(
            currency='GBP',
            service=self.service, price=D('10.00'))
        self.purchase_info = factories.create_purchase_info(self.record)
        self.basket.add(self.service)

    def test_creates_a_line(self):
        self.assertEqual(1, self.basket.num_lines)

    def test_sets_line_prices(self):
        line = self.basket.lines.all()[0]
        self.assertEqual(line.price_incl_tax, self.purchase_info.price.incl_tax)
        self.assertEqual(line.price_excl_tax, self.purchase_info.price.excl_tax)

    def test_adding_negative_quantity(self):
        self.assertEqual(1, self.basket.num_lines)
        self.basket.add(self.service, quantity=4)
        self.assertEqual(5, self.basket.line_quantity(self.service, self.record))
        self.basket.add(self.service, quantity=-10)
        self.assertEqual(0, self.basket.line_quantity(self.service, self.record))

    def test_means_another_currency_service_cannot_be_added(self):
        service = factories.create_service()
        factories.create_stockrecord(
            currency='USD', service=service, price=D('20.00'))
        with self.assertRaises(ValueError):
            self.basket.add(service)

    def test_cannot_add_a_service_without_price(self):
        service = factories.create_service(price=None)
        with self.assertRaises(ValueError):
            self.basket.add(service)


class TestANonEmptyBasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.service = factories.create_service()
        self.record = factories.create_stockrecord(
            self.service, price=D('10.00'))
        self.purchase_info = factories.create_purchase_info(self.record)
        self.basket.add(self.service, 10)

    def test_can_be_flushed(self):
        self.basket.flush()
        self.assertEqual(self.basket.num_items, 0)

    def test_returns_correct_service_quantity(self):
        self.assertEqual(10, self.basket.service_quantity(
            self.service))

    def test_returns_correct_line_quantity_for_existing_service_and_stockrecord(self):
        self.assertEqual(10, self.basket.line_quantity(
            self.service, self.record))

    def test_returns_zero_line_quantity_for_alternative_stockrecord(self):
        record = factories.create_stockrecord(
            self.service, price=D('5.00'))
        self.assertEqual(0, self.basket.line_quantity(
            self.service, record))

    def test_returns_zero_line_quantity_for_missing_service_and_stockrecord(self):
        service = factories.create_service()
        record = factories.create_stockrecord(
            service, price=D('5.00'))
        self.assertEqual(0, self.basket.line_quantity(
            service, record))

    def test_returns_correct_quantity_for_existing_service_and_stockrecord_and_options(self):
        service = factories.create_service()
        record = factories.create_stockrecord(
            service, price=D('5.00'))
        option = Option.objects.create(name="Message")
        options = [{"option": option, "value": "2"}]

        self.basket.add(service, options=options)
        self.assertEqual(0, self.basket.line_quantity(
            service, record))
        self.assertEqual(1, self.basket.line_quantity(
            service, record, options))

    def test_total_sums_service_totals(self):
        service = factories.create_service()
        factories.create_stockrecord(
            service, price=D('5.00'))
        self.basket.add(service, 1)
        self.assertEqual(self.basket.total_excl_tax, 105)

    def test_totals_for_free_services(self):
        basket = Basket()
        basket.strategy = strategy.Default()
        # Add a zero-priced service to the basket
        service = factories.create_service()
        factories.create_stockrecord(
            service, price=D('0.00'), num_in_stock=10)
        basket.add(service, 1)

        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.total_excl_tax, 0)
        self.assertEqual(basket.total_incl_tax, 0)

    def test_basket_prices_calculation_for_unavailable_pricing(self):
        new_service = factories.create_service()
        factories.create_stockrecord(
            new_service, price=D('5.00'))
        self.basket.add(new_service, 1)

        class UnavailableServiceStrategy(strategy.Default):
            """ A test strategy that makes a specific service unavailable """

            def availability_policy(self, service, stockrecord):
                if service == new_service:
                    return availability.Unavailable()
                return super().availability_policy(service, stockrecord)

            def pricing_policy(self, service, stockrecord):
                if service == new_service:
                    return prices.Unavailable()
                return super().pricing_policy(service, stockrecord)

        self.basket.strategy = UnavailableServiceStrategy()
        line = self.basket.all_lines()[1]
        self.assertEqual(line.get_warning(), "'D\xf9\uff4d\u03fb\u03d2 title' is no longer available")
        self.assertIsNone(line.line_price_excl_tax)
        self.assertIsNone(line.line_price_incl_tax)
        self.assertIsNone(line.line_price_excl_tax_incl_discounts)
        self.assertIsNone(line.line_price_incl_tax_incl_discounts)
        self.assertIsNone(line.line_tax)
        self.assertEqual(self.basket.total_excl_tax, 100)
        self.assertEqual(self.basket.total_incl_tax, 100)
        self.assertEqual(self.basket.total_excl_tax_excl_discounts, 100)
        self.assertEqual(self.basket.total_incl_tax_excl_discounts, 100)

    def test_max_allowed_quantity(self):
        self.basket.add_service(self.service, quantity=3)

        # max allowed here is 7 (20-10+3)
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=20):
            max_allowed, basket_threshold = self.basket.max_allowed_quantity()
            self.assertEqual(max_allowed, 7)
            self.assertEqual(basket_threshold, 20)

        # but we can also completely disable the threshold
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=None):
            max_allowed, basket_threshold = self.basket.max_allowed_quantity()
            self.assertEqual(max_allowed, None)
            self.assertEqual(basket_threshold, None)

    def test_is_quantity_allowed(self):
        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=20):
            # 7 or below is possible
            allowed, message = self.basket.is_quantity_allowed(qty=7)
            self.assertTrue(allowed)
            self.assertIsNone(message)
            # but above it's not
            allowed, message = self.basket.is_quantity_allowed(qty=11)
            self.assertFalse(allowed)
            self.assertIsNotNone(message)

        with self.settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=None):
            # with the treshold disabled all quantities are possible
            allowed, message = self.basket.is_quantity_allowed(qty=7)
            self.assertTrue(allowed)
            self.assertIsNone(message)
            allowed, message = self.basket.is_quantity_allowed(qty=5000)
            self.assertTrue(allowed)
            self.assertIsNone(message)


class TestMergingTwoBaskets(TestCase):

    def setUp(self):
        self.service = factories.create_service()
        self.record = factories.create_stockrecord(
            self.service, price=D('10.00'))
        self.purchase_info = factories.create_purchase_info(self.record)

        self.main_basket = Basket()
        self.main_basket.strategy = strategy.Default()
        self.main_basket.add(self.service, quantity=2)

        self.merge_basket = Basket()
        self.merge_basket.strategy = strategy.Default()
        self.merge_basket.add(self.service, quantity=1)

        self.main_basket.merge(self.merge_basket)

    def test_doesnt_sum_quantities(self):
        self.assertEqual(1, self.main_basket.num_lines)

    def test_changes_status_of_merge_basket(self):
        self.assertEqual(Basket.MERGED, self.merge_basket.status)


class TestASubmittedBasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.basket.submit()

    def test_has_correct_status(self):
        self.assertTrue(self.basket.is_submitted)

    def test_can_be_edited(self):
        self.assertFalse(self.basket.can_be_edited)


class TestMergingAVoucherBasket(TestCase):

    def test_transfers_vouchers_to_new_basket(self):
        baskets = [factories.BasketFactory(), factories.BasketFactory()]
        voucher = factories.VoucherFactory()
        baskets[0].vouchers.add(voucher)
        baskets[1].merge(baskets[0])

        self.assertEqual(1, baskets[1].vouchers.all().count())
