from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from oscar.apps.catalogue.models import Service, ServiceAttribute
from oscar.test import factories


class TestContainer(TestCase):

    def test_attributes_initialised_before_write(self):
        # Regression test for https://github.com/django-oscar/django-oscar/issues/3258
        service_class = factories.ServiceClassFactory()
        service_class.attributes.create(name='a1', code='a1', required=True)
        service_class.attributes.create(name='a2', code='a2', required=False)
        service_class.attributes.create(name='a3', code='a3', required=True)
        service = factories.ServiceFactory(service_class=service_class)
        service.attr.a1 = "v1"
        service.attr.a3 = "v3"
        service.attr.save()

        service = Service.objects.get(pk=service.pk)
        service.attr.a1 = "v2"
        service.attr.a3 = "v6"
        service.attr.save()

        service = Service.objects.get(pk=service.pk)
        assert service.attr.a1 == "v2"
        assert service.attr.a3 == "v6"

    def test_attributes_refresh(self):
        service_class = factories.ServiceClassFactory()
        service_class.attributes.create(name='a1', code='a1', required=True)
        service = factories.ServiceFactory(service_class=service_class)
        service.attr.a1 = "v1"
        service.attr.save()

        service_attr = ServiceAttribute.objects.get(code="a1", service=service)
        service_attr.save_value(service, "v2")
        assert service.attr.a1 == "v1"

        service.attr.refresh()
        assert service.attr.a1 == "v2"


class TestBooleanAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="boolean")

    def test_validate_boolean_values(self):
        self.assertIsNone(self.attr.validate_value(True))

    def test_validate_invalid_boolean_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestMultiOptionAttributes(TestCase):

    def setUp(self):
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ServiceAttributeFactory(
            type='multi_option',
            name='Sizes',
            code='sizes',
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group)

    def test_validate_multi_option_values(self):
        self.assertIsNone(self.attr.validate_value([
            self.options[0], self.options[1]]))

    def test_validate_invalid_multi_option_values(self):
        with self.assertRaises(ValidationError):
            # value must be an iterable
            self.attr.validate_value('foobar')

        with self.assertRaises(ValidationError):
            # Items must all be AttributeOption objects
            self.attr.validate_value([self.options[0], 'notanOption'])

    def test_save_multi_option_value(self):
        service = factories.ServiceFactory()
        # We'll save two out of the three available options
        self.attr.save_value(service, [self.options[0], self.options[2]])
        service = Service.objects.get(pk=service.pk)
        self.assertEqual(list(service.attr.sizes), [self.options[0], self.options[2]])

    def test_delete_multi_option_value(self):
        service = factories.ServiceFactory()
        self.attr.save_value(service, [self.options[0], self.options[1]])
        # Now delete these values
        self.attr.save_value(service, None)
        service = Service.objects.get(pk=service.pk)
        self.assertFalse(hasattr(service.attr, 'sizes'))

    def test_multi_option_value_as_text(self):
        service = factories.ServiceFactory()
        self.attr.save_value(service, self.options)
        attr_val = service.attribute_values.get(attribute=self.attr)
        self.assertEqual(attr_val.value_as_text, ", ".join(o.option for o in self.options))


class TestOptionAttributes(TestCase):

    def setUp(self):
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ServiceAttributeFactory(
            type='option',
            name='Size',
            code='size',
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group)

    def test_option_value_as_text(self):
        service = factories.ServiceFactory()
        option_2 = self.options[1]
        self.attr.save_value(service, option_2)
        attr_val = service.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == str(option_2)


class TestDatetimeAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="datetime")

    def test_validate_datetime_values(self):
        self.assertIsNone(self.attr.validate_value(datetime.now()))

    def test_validate_invalid_datetime_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestDateAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="date")

    def test_validate_datetime_values(self):
        self.assertIsNone(self.attr.validate_value(datetime.now()))

    def test_validate_date_values(self):
        self.assertIsNone(self.attr.validate_value(date.today()))

    def test_validate_invalid_date_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestIntegerAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="integer")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_str_integer_values(self):
        self.assertIsNone(self.attr.validate_value('1'))

    def test_validate_invalid_integer_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value('notanInteger')


class TestFloatAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="float")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_float_values(self):
        self.assertIsNone(self.attr.validate_value(1.2))

    def test_validate_str_float_values(self):
        self.assertIsNone(self.attr.validate_value('1.2'))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value('notaFloat')


class TestTextAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="text")

    def test_validate_string_and_unicode_values(self):
        self.assertIsNone(self.attr.validate_value('String'))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestFileAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ServiceAttributeFactory(type="file")

    def test_validate_file_values(self):
        file_field = SimpleUploadedFile('test_file.txt', b'Test')
        self.assertIsNone(self.attr.validate_value(file_field))
