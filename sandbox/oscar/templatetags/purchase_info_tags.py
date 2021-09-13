from django import template

register = template.Library()


@register.simple_tag
def purchase_info_for_service(request, service):
    if service.is_parent:
        return request.strategy.fetch_for_parent(service)

    return request.strategy.fetch_for_service(service)


@register.simple_tag
def purchase_info_for_line(request, line):
    return request.strategy.fetch_for_line(line)
