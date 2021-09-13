from django import template

register = template.Library()


@register.simple_tag
def wishlists_containing_service(wishlists, service):
    return wishlists.filter(lines__service=service)
