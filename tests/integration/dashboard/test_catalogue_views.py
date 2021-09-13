from django.test import TestCase

from oscar.apps.dashboard.catalogue.views import ServiceListView
from oscar.core.loading import get_model
from oscar.test.factories import create_service
from oscar.test.utils import RequestFactory

Service = get_model('catalogue', 'Service')


class ServiceListViewTestCase(TestCase):
    def test_searching_child_service_by_title_returns_parent_service(self):
        self.parent_service = create_service(structure=Service.PARENT, title='Parent', upc='PARENT_UPC')
        create_service(structure=Service.CHILD, title='Child', parent=self.parent_service, upc='CHILD_UPC')
        view = ServiceListView(request=RequestFactory().get('/?title=Child'))
        assert list(view.get_queryset()) == [self.parent_service]

    def test_searching_child_service_by_title_returns_1_parent_service_if_title_is_partially_shared(self):
        self.parent_service = create_service(structure=Service.PARENT, title='Shared', upc='PARENT_UPC')
        create_service(structure=Service.CHILD, title='Shared', parent=self.parent_service, upc='CHILD_UPC')
        create_service(structure=Service.CHILD, title='Shared1', parent=self.parent_service, upc='CHILD_UPC1')
        view = ServiceListView(request=RequestFactory().get('/?title=Shared'))
        assert list(view.get_queryset()) == [self.parent_service]

    def test_searching_child_service_by_upc_returns_parent_service(self):
        self.parent_service = create_service(structure=Service.PARENT, title='Parent', upc='PARENT_UPC')
        create_service(structure=Service.CHILD, title='Child', parent=self.parent_service, upc='CHILD_UPC')
        view = ServiceListView(request=RequestFactory().get('/?upc=CHILD_UPC'))
        assert list(view.get_queryset()) == [self.parent_service]

    def test_searching_child_service_by_upc_returns_1_parent_service_if_upc_is_partially_shared(self):
        self.parent_service = create_service(structure=Service.PARENT, title='Parent', upc='PARENT_UPC')
        create_service(structure=Service.CHILD, title='Child', parent=self.parent_service, upc='CHILD_UPC')
        create_service(structure=Service.CHILD, title='Child1', parent=self.parent_service, upc='CHILD_UPC1')
        view = ServiceListView(request=RequestFactory().get('/?upc=CHILD'))
        assert list(view.get_queryset()) == [self.parent_service]
