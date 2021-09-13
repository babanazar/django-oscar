from django.db.models import F

from oscar.core.loading import get_model

ServiceRecord = get_model('analytics', 'ServiceRecord')


class Calculator(object):

    # Map of field name to weight
    weights = {
        'num_views': 1,
        'num_basket_additions': 3,
        'num_purchases': 5
    }

    def __init__(self, logger):
        self.logger = logger

    def run(self):
        self.calculate_scores()

    def calculate_scores(self):
        self.logger.info("Calculating service scores")
        total_weight = float(sum(self.weights.values()))
        weighted_fields = [
            self.weights[name] * F(name) for name in self.weights.keys()]
        ServiceRecord.objects.update(
            score=sum(weighted_fields) / total_weight)
