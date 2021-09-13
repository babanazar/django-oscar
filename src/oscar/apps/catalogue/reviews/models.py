from oscar.apps.catalogue.reviews.abstract_models import (
    AbstractServiceReview, AbstractVote)
from oscar.core.loading import is_model_registered

if not is_model_registered('reviews', 'ServiceReview'):
    class ServiceReview(AbstractServiceReview):
        pass


if not is_model_registered('reviews', 'Vote'):
    class Vote(AbstractVote):
        pass
