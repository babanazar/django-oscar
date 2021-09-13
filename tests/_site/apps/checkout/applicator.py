from decimal import Decimal as D

from sandbox.oscar.apps.checkout import (
    SurchargeApplicator as BaseSurchargeApplicator)
from sandbox.oscar.apps.checkout import FlatCharge


class SurchargeApplicator(BaseSurchargeApplicator):
    def get_surcharges(self, basket, **kwargs):
        return (
            FlatCharge(excl_tax=D("10.0"), incl_tax=D("10.0")),
            FlatCharge(excl_tax=D("10.0"), incl_tax=D("12.0")),
        )

    def is_applicable(self, surcharge, basket, **kwargs):
        if surcharge.incl_tax > surcharge.excl_tax:
            if basket.is_tax_known:
                return True
        else:
            return True

        return False
