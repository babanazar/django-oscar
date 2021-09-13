from django.db import models
from django.db.models import Exists, OuterRef


def service_class_as_queryset(service):
    "Returns a queryset with the service_classes of a service (only one)"
    ServiceClass = service._meta.get_field("service_class").related_model
    return ServiceClass.objects.filter(
        pk__in=service.__class__.objects.filter(pk=service.pk)
        .annotate(
            _service_class_id=models.Case(
                models.When(
                    structure=service.CHILD, then=models.F("parent__service_class")
                ),
                models.When(
                    structure__in=[service.PARENT, service.STANDALONE],
                    then=models.F("service_class"),
                ),
            )
        )
        .values("_service_class_id")
    )


class RangeQuerySet(models.query.QuerySet):
    """
    This queryset add ``contains_service`` which allows selecting the
    ranges that contain the service in question.
    """
    def contains_service(self, service):
        "Return ranges that contain ``service`` in a single query"
        if service.structure == service.CHILD:
            return self._ranges_that_contain_service(
                service.parent
            ) | self._ranges_that_contain_service(service)
        return self._ranges_that_contain_service(service)

    def _ranges_that_contain_service(self, service):
        Category = service.categories.model
        included_in_subtree = service.categories.filter(
            path__startswith=OuterRef("path")
        )
        category_tree = Category.objects.annotate(
            is_included_in_subtree=Exists(included_in_subtree.values("id"))
        ).filter(is_included_in_subtree=True)

        wide = self.filter(
            ~models.Q(excluded_services=service), includes_all_services=True
        )
        narrow = self.filter(
            ~models.Q(excluded_services=service),
            models.Q(included_services=service)
            | models.Q(included_categories__in=category_tree)
            | models.Q(classes__in=service_class_as_queryset(service)),
            includes_all_services=False,
        )
        return wide | narrow
