import pytest
from django.core.exceptions import ValidationError

from oscar.apps.catalogue import models


def test_service_attributes_can_contain_underscores():
    attr = models.ServiceAttribute(name="A", code="a_b")
    attr.full_clean()


def test_service_attributes_cant_contain_hyphens():
    attr = models.ServiceAttribute(name="A", code="a-b")
    with pytest.raises(ValidationError):
        attr.full_clean()


def test_service_attributes_cant_be_python_keywords():
    attr = models.ServiceAttribute(name="A", code="import")
    with pytest.raises(ValidationError):
        attr.full_clean()


def test_service_boolean_attribute_cant_be_required():
    attr = models.ServiceAttribute(name="A", code="a", type=models.ServiceAttribute.BOOLEAN, required=True)
    with pytest.raises(ValidationError):
        attr.full_clean()
