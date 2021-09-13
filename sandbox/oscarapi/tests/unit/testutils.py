from django.test import TestCase
from oscar.core.loading import get_model
from oscarapi.utils import exists

Service = get_model("catalogue", "Service")
Category = get_model("catalogue", "Category")
ServiceAttributeValue = get_model("catalogue", "ServiceAttributeValue")


class UtilsExistTest(TestCase):
    fixtures = [
        "service",
        "servicecategory",
        "serviceattribute",
        "serviceclass",
        "serviceattributevalue",
        "category",
        "attributeoptiongroup",
        "attributeoption",
        "stockrecord",
        "partner",
        "option",
    ]

    def _test_construct_id_filter(self, model, data):

        query = exists.construct_id_filter(model, data)
        qs = model.objects.filter(query)
        self.assertEqual(qs.count(), 1)
        p = qs.first()
        return p

    def test_service_construct_id_filter_pk(self):
        for pk in [1, 2, 3, 4]:
            p = self._test_construct_id_filter(Service, {"id": pk, "title": "klaas"})
            self.assertEqual(p.id, pk)

    def test_category_construct_id_filter_pk(self):
        c = self._test_construct_id_filter(Category, {"id": 1, "name": "zult"})
        self.assertEqual(c.id, 1)

    def test_service_construct_id_filter_upc(self):
        for upc in ["1234", "child-1234", "attrtypestest", "entity"]:
            p = self._test_construct_id_filter(Service, {"upc": upc, "title": "henk"})
            self.assertEqual(p.upc, upc)

    def test_service_attribute_value_construct_id_filter_unique_together(self):
        av = self._test_construct_id_filter(
            ServiceAttributeValue, {"attribute": 1, "service": 1, "value_text": "klaas"}
        )
        self.assertEqual(av.id, 1)
