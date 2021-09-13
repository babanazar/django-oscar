from django.test import TestCase

from oscar.apps.catalogue.models import Service
from oscar.test.factories.catalogue import ServiceFactory


class ServiceTestCase(TestCase):

    @staticmethod
    def _get_saved(model_obj):
        model_obj.save()
        model_obj.refresh_from_db()
        return model_obj

    def test_get_meta_title(self):
        parent_title, child_title = "P title", "C title"
        parent_meta_title, child_meta_title = "P meta title", "C meta title"
        parent_service = ServiceFactory(structure=Service.PARENT, title=parent_title, meta_title=parent_meta_title)
        child_service = ServiceFactory(structure=Service.CHILD, title=child_title, meta_title=child_meta_title,
                                       parent=parent_service)
        self.assertEqual(child_service.get_meta_title(), child_meta_title)
        child_service.meta_title = ""
        self.assertEqual(self._get_saved(child_service).get_meta_title(), parent_meta_title)
        parent_service.meta_title = ""
        child_service.parent = self._get_saved(parent_service)
        self.assertEqual(self._get_saved(child_service).get_meta_title(), child_title)

    def test_get_meta_description(self):
        parent_description, child_description = "P description", "C description"
        parent_meta_description, child_meta_description = "P meta description", "C meta description"
        parent_service = ServiceFactory(structure=Service.PARENT, description=parent_description,
                                        meta_description=parent_meta_description)
        child_service = ServiceFactory(structure=Service.CHILD, description=child_description,
                                       meta_description=child_meta_description, parent=parent_service)
        self.assertEqual(child_service.get_meta_description(), child_meta_description)
        child_service.meta_description = ""
        self.assertEqual(self._get_saved(child_service).get_meta_description(), parent_meta_description)
        parent_service.meta_description = ""
        child_service.parent = self._get_saved(parent_service)
        self.assertEqual(self._get_saved(child_service).get_meta_description(), child_description)
