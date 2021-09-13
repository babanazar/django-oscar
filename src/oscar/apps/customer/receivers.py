from django.dispatch import receiver

from oscar.apps.catalogue.signals import service_viewed
from oscar.core.loading import get_class

CustomerHistoryManager = get_class('customer.history', 'CustomerHistoryManager')


@receiver(service_viewed)
def receive_service_view(sender, service, user, request, response, **kwargs):
    """
    Receiver to handle viewing single service pages

    Requires the request and response objects due to dependence on cookies
    """
    return CustomerHistoryManager.update(service, request, response)
