from django.test import TestCase

from oscar.core.loading import get_model
from oscar.test import factories

Service = get_model('catalogue', 'Service')


class ServiceOptionTests(TestCase):
    def setUp(self):
        self.service_class = factories.ServiceClassFactory()
        self.service = factories.create_service(service_class=self.service_class)
        self.option = factories.OptionFactory()

    def test_service_has_options_per_service_class(self):
        self.service_class.options.add(self.option)
        self.assertTrue(self.service.has_options)

    def test_service_has_options_per_service(self):
        self.service.service_options.add(self.option)
        self.assertTrue(self.service.has_options)

    def test_queryset_per_service_class(self):
        self.service_class.options.add(self.option)
        qs = Service.objects.browsable().base_queryset().filter(id=self.service.id)
        service = qs.first()
        self.assertTrue(service.has_options)
        self.assertTrue(service.has_service_class_options)

    def test_queryset_per_service(self):
        self.service.service_options.add(self.option)
        qs = Service.objects.browsable().base_queryset().filter(id=self.service.id)
        service = qs.first()
        self.assertTrue(service.has_options)
        self.assertTrue(service.has_service_options, 1)

    def test_queryset_both(self):
        "The options attribute on a service should return a queryset containing "
        "both the service class options and any extra options defined on the"
        "service"
        # set up the options on service and service_class
        self.test_service_has_options_per_service_class()
        self.test_service_has_options_per_service()
        self.assertTrue(self.service.has_options, "Options should be present")
        self.assertEqual(
            self.service.options.count(), 1,
            "options attribute should not contain duplicates"
        )
        qs = Service.objects.browsable().base_queryset().filter(id=self.service.id)
        service = qs.first()
        self.assertTrue(
            service.has_service_class_options,
            "has_service_class_options should indicate the service_class option"
        )
        self.assertTrue(
            service.has_service_options,
            "has_service_options should indicate the number of service options"
        )
        self.service_class.options.add(factories.OptionFactory(code="henk"))
        self.assertEqual(
            self.service.options.count(), 2,
            "New service_class options should be immediately visible"
        )
        self.service.service_options.add(factories.OptionFactory(code="klaas"))
        self.assertEqual(
            self.service.options.count(), 3,
            "New service options should be immediately visible"
        )
