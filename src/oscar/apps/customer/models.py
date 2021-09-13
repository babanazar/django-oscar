from oscar.apps.customer import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('customer', 'ServiceAlert'):
    class ServiceAlert(abstract_models.AbstractServiceAlert):
        pass

    __all__.append('ServiceAlert')
