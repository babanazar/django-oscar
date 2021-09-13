"""
Vanilla service models
"""
from oscar.apps.catalogue.abstract_models import *  # noqa
from oscar.core.loading import is_model_registered

__all__ = ['ServiceAttributesContainer']


if not is_model_registered('catalogue', 'ServiceClass'):
    class ServiceClass(AbstractServiceClass):
        pass

    __all__.append('ServiceClass')


if not is_model_registered('catalogue', 'Category'):
    class Category(AbstractCategory):
        pass

    __all__.append('Category')


if not is_model_registered('catalogue', 'ServiceCategory'):
    class ServiceCategory(AbstractServiceCategory):
        pass

    __all__.append('ServiceCategory')


if not is_model_registered('catalogue', 'Service'):
    class Service(AbstractService):
        pass

    __all__.append('Service')


if not is_model_registered('catalogue', 'ServiceRecommendation'):
    class ServiceRecommendation(AbstractServiceRecommendation):
        pass

    __all__.append('ServiceRecommendation')


if not is_model_registered('catalogue', 'ServiceAttribute'):
    class ServiceAttribute(AbstractServiceAttribute):
        pass

    __all__.append('ServiceAttribute')


if not is_model_registered('catalogue', 'ServiceAttributeValue'):
    class ServiceAttributeValue(AbstractServiceAttributeValue):
        pass

    __all__.append('ServiceAttributeValue')


if not is_model_registered('catalogue', 'AttributeOptionGroup'):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass

    __all__.append('AttributeOptionGroup')


if not is_model_registered('catalogue', 'AttributeOption'):
    class AttributeOption(AbstractAttributeOption):
        pass

    __all__.append('AttributeOption')


if not is_model_registered('catalogue', 'Option'):
    class Option(AbstractOption):
        pass

    __all__.append('Option')


if not is_model_registered('catalogue', 'ServiceImage'):
    class ServiceImage(AbstractServiceImage):
        pass

    __all__.append('ServiceImage')
