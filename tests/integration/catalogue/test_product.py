# coding=utf-8
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from oscar.apps.catalogue.models import (
    AttributeOption, Service, ServiceAttribute,
    ServiceClass, ServiceRecommendation)
from oscar.test import factories


class ServiceTests(TestCase):

    def setUp(self):
        self.service_class, _ = ServiceClass.objects.get_or_create(
            name='Clothing')


class ServiceCreationTests(ServiceTests):

    def setUp(self):
        super().setUp()
        ServiceAttribute.objects.create(service_class=self.service_class,
                                        name='Number of pages',
                                        code='num_pages',
                                        type='integer')
        Service.ENABLE_ATTRIBUTE_BINDING = True

    def tearDown(self):
        Service.ENABLE_ATTRIBUTE_BINDING = False

    def test_create_services_with_attributes(self):
        service = Service(upc='1234',
                          service_class=self.service_class,
                          title='testing')
        service.attr.num_pages = 100
        service.save()

    def test_none_upc_is_represented_as_empty_string(self):
        service = Service(service_class=self.service_class,
                          title='testing', upc=None)
        service.save()
        service.refresh_from_db()
        self.assertEqual(service.upc, '')

    def test_upc_uniqueness_enforced(self):
        Service.objects.create(service_class=self.service_class,
                               title='testing', upc='bah')
        self.assertRaises(IntegrityError, Service.objects.create,
                          service_class=self.service_class,
                          title='testing', upc='bah')

    def test_allow_two_services_without_upc(self):
        for x in range(2):
            Service.objects.create(service_class=self.service_class,
                                   title='testing', upc=None)


class TopLevelServiceTests(ServiceTests):

    def test_top_level_services_must_have_titles(self):
        service = Service(service_class=self.service_class)
        self.assertRaises(ValidationError, service.clean)

    def test_top_level_services_must_have_service_class(self):
        service = Service(title="Kopfhörer")
        self.assertRaises(ValidationError, service.clean)

    def test_top_level_services_are_part_of_browsable_set(self):
        service = Service.objects.create(
            service_class=self.service_class, title="Kopfhörer")
        self.assertEqual(set([service]), set(Service.objects.browsable()))


class ChildServiceTests(ServiceTests):

    def setUp(self):
        super().setUp()
        self.parent = Service.objects.create(
            title="Parent service",
            service_class=self.service_class,
            structure=Service.PARENT,
            is_discountable=False)
        ServiceAttribute.objects.create(
            service_class=self.service_class,
            name='The first attribute',
            code='first_attribute',
            type='text')
        ServiceAttribute.objects.create(
            service_class=self.service_class,
            name='The second attribute',
            code='second_attribute',
            type='text')

    def test_child_services_dont_need_titles(self):
        Service.objects.create(
            parent=self.parent, structure=Service.CHILD)

    def test_child_services_dont_need_a_service_class(self):
        Service.objects.create(parent=self.parent, structure=Service.CHILD)

    def test_child_services_inherit_fields(self):
        p = Service.objects.create(
            parent=self.parent,
            structure=Service.CHILD,
            is_discountable=True)
        self.assertEqual("Parent service", p.get_title())
        self.assertEqual("Clothing", p.get_service_class().name)
        self.assertEqual(False, p.get_is_discountable())

    def test_child_services_are_not_part_of_browsable_set(self):
        Service.objects.create(
            service_class=self.service_class, parent=self.parent,
            structure=Service.CHILD)
        self.assertEqual(set([self.parent]), set(Service.objects.browsable()))

    def test_child_services_attribute_values(self):
        service = Service.objects.create(
            service_class=self.service_class, parent=self.parent,
            structure=Service.CHILD)

        self.parent.attr.first_attribute = "klats"
        service.attr.second_attribute = "henk"
        self.parent.save()
        service.save()

        service = Service.objects.get(pk=service.pk)
        parent = Service.objects.get(pk=self.parent.pk)

        self.assertEqual(parent.get_attribute_values().count(), 1)
        self.assertEqual(service.get_attribute_values().count(), 2)
        self.assertTrue(hasattr(parent.attr, "first_attribute"))
        self.assertFalse(hasattr(parent.attr, "second_attribute"))
        self.assertTrue(hasattr(service.attr, "first_attribute"))
        self.assertTrue(hasattr(service.attr, "second_attribute"))

    def test_child_services_attribute_values_no_parent_values(self):
        service = Service.objects.create(
            service_class=self.service_class, parent=self.parent,
            structure=Service.CHILD)

        service.attr.second_attribute = "henk"
        service.save()

        service = Service.objects.get(pk=service.pk)

        self.assertEqual(self.parent.get_attribute_values().count(), 0)
        self.assertEqual(service.get_attribute_values().count(), 1)
        self.assertFalse(hasattr(self.parent.attr, "first_attribute"))
        self.assertFalse(hasattr(self.parent.attr, "second_attribute"))
        self.assertFalse(hasattr(service.attr, "first_attribute"))
        self.assertTrue(hasattr(service.attr, "second_attribute"))


class TestAChildService(TestCase):

    def setUp(self):
        clothing = ServiceClass.objects.create(
            name='Clothing', requires_shipping=True)
        self.parent = clothing.services.create(
            title="Parent", structure=Service.PARENT)
        self.child = self.parent.children.create(structure=Service.CHILD)

    def test_delegates_requires_shipping_logic(self):
        self.assertTrue(self.child.is_shipping_required)


class ServiceAttributeCreationTests(TestCase):

    def test_validating_option_attribute(self):
        option_group = factories.AttributeOptionGroupFactory()
        option_1 = factories.AttributeOptionFactory(group=option_group)
        option_2 = factories.AttributeOptionFactory(group=option_group)
        pa = factories.ServiceAttribute(
            type='option', option_group=option_group)

        self.assertRaises(ValidationError, pa.validate_value, 'invalid')
        pa.validate_value(option_1)
        pa.validate_value(option_2)

        invalid_option = AttributeOption(option='invalid option')
        self.assertRaises(
            ValidationError, pa.validate_value, invalid_option)

    def test_entity_attributes(self):
        unrelated_object = factories.PartnerFactory()
        attribute = factories.ServiceAttributeFactory(type='entity')

        attribute_value = factories.ServiceAttributeValueFactory(
            attribute=attribute, value_entity=unrelated_object)

        self.assertEqual(attribute_value.value, unrelated_object)


class ServiceRecommendationTests(ServiceTests):

    def setUp(self):
        super().setUp()
        self.primary_service = Service.objects.create(
            upc='1234', service_class=self.service_class, title='Primary Service'
        )

    def test_recommended_services_ordering(self):
        secondary_services = []
        for i in range(5):
            secondary_services.append(Service.objects.create(
                upc='secondary%s' % i, service_class=self.service_class, title='Secondary Service #%s' % i
            ))

        ServiceRecommendation.objects.create(
            primary=self.primary_service, recommendation=secondary_services[3], ranking=5)
        ServiceRecommendation.objects.create(
            primary=self.primary_service, recommendation=secondary_services[1], ranking=2)
        ServiceRecommendation.objects.create(
            primary=self.primary_service, recommendation=secondary_services[2], ranking=4)
        ServiceRecommendation.objects.create(
            primary=self.primary_service, recommendation=secondary_services[4], ranking=1)
        ServiceRecommendation.objects.create(
            primary=self.primary_service, recommendation=secondary_services[0], ranking=3)
        recommended_services = [
            secondary_services[3], secondary_services[2], secondary_services[0],
            secondary_services[1], secondary_services[4]
        ]
        self.assertEqual(self.primary_service.sorted_recommended_services, recommended_services)
