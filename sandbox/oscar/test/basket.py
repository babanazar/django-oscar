from decimal import Decimal as D

from oscar.core.loading import get_class
from oscar.test import factories

Default = get_class('partner.strategy', 'Default')


def add_service(basket, price=None, quantity=1, service=None):
    """
    Helper to add a service to the basket.
    """
    has_strategy = False
    try:
        has_strategy = hasattr(basket, 'strategy')
    except RuntimeError:
        pass
    if not has_strategy:
        basket.strategy = Default()
    if price is None:
        price = D('1')
    if service and service.has_stockrecords:
        record = service.stockrecords.first()
    else:
        record = factories.create_stockrecord(
            service=service, price=price,
            num_in_stock=quantity + 1)
    basket.add_service(record.service, quantity)


def add_services(basket, args):
    """
    Helper to add a series of services to the passed basket
    """
    for price, quantity in args:
        add_service(basket, price, quantity)
