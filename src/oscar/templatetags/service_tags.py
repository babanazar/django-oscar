from django import template
from django.template.loader import select_template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_service(context, service):
    """
    Render a service snippet as you would see in a browsing display.

    This templatetag looks for different templates depending on the UPC and
    service class of the passed service.  This allows alternative templates to
    be used for different service classes.
    """
    if not service:
        # Search index is returning services that don't exist in the
        # database...
        return ''

    names = ['oscar/catalogue/partials/service/upc-%s.html' % service.upc,
             'oscar/catalogue/partials/service/class-%s.html'
             % service.get_service_class().slug,
             'oscar/catalogue/partials/service.html']
    template_ = select_template(names)
    context = context.flatten()

    # Ensure the passed service is in the context as 'service'
    context['service'] = service
    return template_.render(context)
