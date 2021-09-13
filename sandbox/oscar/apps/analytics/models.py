from oscar.apps.analytics.abstract_models import (
    AbstractServiceRecord, AbstractUserServiceView,
    AbstractUserRecord, AbstractUserSearch)
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('analytics', 'ServiceRecord'):
    class ServiceRecord(AbstractServiceRecord):
        pass

    __all__.append('ServiceRecord')


if not is_model_registered('analytics', 'UserRecord'):
    class UserRecord(AbstractUserRecord):
        pass

    __all__.append('UserRecord')


if not is_model_registered('analytics', 'UserServiceView'):
    class UserServiceView(AbstractUserServiceView):
        pass

    __all__.append('UserServiceView')


if not is_model_registered('analytics', 'UserSearch'):
    class UserSearch(AbstractUserSearch):
        pass

    __all__.append('UserSearch')
