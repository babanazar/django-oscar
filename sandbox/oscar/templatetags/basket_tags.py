from django import template

from oscar.core.loading import get_class, get_model

AddToBasketForm = get_class('basket.forms', 'AddToBasketForm')
SimpleAddToBasketForm = get_class('basket.forms', 'SimpleAddToBasketForm')
Service = get_model('catalogue', 'service')

register = template.Library()

QNT_SINGLE, QNT_MULTIPLE = 'single', 'multiple'


@register.simple_tag
def basket_form(request, service, quantity_type='single'):
    if not isinstance(service, Service):
        return ''

    initial = {}
    if not service.is_parent:
        initial['service_id'] = service.id

    form_class = AddToBasketForm
    if quantity_type == QNT_SINGLE:
        form_class = SimpleAddToBasketForm

    form = form_class(request.basket, service=service, initial=initial)

    return form
