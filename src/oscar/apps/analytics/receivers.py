import logging

from django.db import IntegrityError
from django.db.models import F
from django.dispatch import receiver

from oscar.apps.basket.signals import basket_addition
from oscar.apps.catalogue.signals import service_viewed
from oscar.apps.order.signals import order_placed
from oscar.apps.search.signals import user_search
from oscar.core.loading import get_model

ServiceRecord = get_model('analytics', 'ServiceRecord')
UserServiceView = get_model('analytics', 'UserServiceView')
UserRecord = get_model('analytics', 'UserRecord')
UserSearch = get_model('analytics', 'UserSearch')

# Helpers

logger = logging.getLogger('oscar.analytics')


def _update_counter(model, field_name, filter_kwargs, increment=1):
    """
    Efficiently updates a counter field by a given increment. Uses Django's
    update() call to fetch and update in one query.

    TODO: This has a race condition, we should use UPSERT here

    :param model: The model class of the recording model
    :param field_name: The name of the field to update
    :param filter_kwargs: Parameters to the ORM's filter() function to get the
                          correct instance
    """
    try:
        record = model.objects.filter(**filter_kwargs)
        affected = record.update(**{field_name: F(field_name) + increment})
        if not affected:
            filter_kwargs[field_name] = increment
            model.objects.create(**filter_kwargs)
    except IntegrityError:      # pragma: no cover
        # get_or_create has a race condition (we should use upsert in supported)
        # databases. For now just ignore these errors
        logger.error(
            "IntegrityError when updating analytics counter for %s", model)


def _record_services_in_order(order):
    # surely there's a way to do this without causing a query for each line?
    for line in order.lines.all():
        _update_counter(
            ServiceRecord, 'num_purchases',
            {'service': line.service}, line.quantity)


def _record_user_order(user, order):
    try:
        record = UserRecord.objects.filter(user=user)
        affected = record.update(
            num_orders=F('num_orders') + 1,
            num_order_lines=F('num_order_lines') + order.num_lines,
            num_order_items=F('num_order_items') + order.num_items,
            total_spent=F('total_spent') + order.total_incl_tax,
            date_last_order=order.date_placed)
        if not affected:
            UserRecord.objects.create(
                user=user, num_orders=1, num_order_lines=order.num_lines,
                num_order_items=order.num_items,
                total_spent=order.total_incl_tax,
                date_last_order=order.date_placed)
    except IntegrityError:      # pragma: no cover
        logger.error(
            "IntegrityError in analytics when recording a user order.")


# Receivers

@receiver(service_viewed)
def receive_service_view(sender, service, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(ServiceRecord, 'num_views', {'service': service})
    if user and user.is_authenticated:
        _update_counter(UserRecord, 'num_service_views', {'user': user})
        UserServiceView.objects.create(service=service, user=user)


@receiver(user_search)
def receive_service_search(sender, query, user, **kwargs):
    if user and user.is_authenticated and not kwargs.get('raw', False):
        UserSearch._default_manager.create(user=user, query=query)


@receiver(basket_addition)
def receive_basket_addition(sender, service, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(
        ServiceRecord, 'num_basket_additions', {'service': service})
    if user and user.is_authenticated:
        _update_counter(UserRecord, 'num_basket_additions', {'user': user})


@receiver(order_placed)
def receive_order_placed(sender, order, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _record_services_in_order(order)
    if user and user.is_authenticated:
        _record_user_order(user, order)
