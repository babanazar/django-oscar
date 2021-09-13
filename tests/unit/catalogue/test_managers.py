import pytest

from sandbox.oscar.apps.catalogue import Service
from oscar.test.factories import ServiceFactory


@pytest.mark.django_db
def test_public_queryset_method_filters():
    ServiceFactory(is_public=True)
    ServiceFactory(is_public=False)
    assert Service.objects.public().count() == 1
