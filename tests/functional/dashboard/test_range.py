from django.contrib.messages.constants import SUCCESS, WARNING
from django.test import TestCase
from django.urls import reverse
from webtest.forms import Upload

from oscar.apps.dashboard.ranges import forms
from oscar.apps.offer.models import Range, RangeServiceFileUpload
from oscar.test.factories import create_service
from oscar.test.testcases import WebTestCase


class RangeServiceFormTests(TestCase):

    def setUp(self):
        self.range = Range.objects.create(name='dummy')

    def tearDown(self):
        Range.objects.all().delete()

    def submit_form(self, data):
        return forms.RangeServiceForm(self.range, data)

    def test_either_query_or_file_must_be_submitted(self):
        form = self.submit_form({'query': ''})
        self.assertFalse(form.is_valid())

    def test_non_match_becomes_error(self):
        form = self.submit_form({'query': '123123'})
        self.assertFalse(form.is_valid())

    def test_matching_query_is_valid(self):
        create_service(partner_sku='123123')
        form = self.submit_form({'query': '123123'})
        self.assertTrue(form.is_valid())

    def test_passing_form_return_service_list(self):
        service = create_service(partner_sku='123123')
        form = self.submit_form({'query': '123123'})
        form.is_valid()
        self.assertEqual(1, len(form.get_services()))
        self.assertEqual(service.id, form.get_services()[0].id)

    def test_missing_skus_are_available(self):
        create_service(partner_sku='123123')
        form = self.submit_form({'query': '123123, 123xxx'})
        form.is_valid()
        self.assertEqual(1, len(form.get_missing_skus()))
        self.assertTrue('123xxx' in form.get_missing_skus())

    def test_only_dupes_is_invalid(self):
        service = create_service(partner_sku='123123')
        self.range.add_service(service)
        form = self.submit_form({'query': '123123'})
        self.assertFalse(form.is_valid())

    def test_dupe_skus_are_available(self):
        service = create_service(partner_sku='123123')
        create_service(partner_sku='123124')
        self.range.add_service(service)
        form = self.submit_form({'query': '123123, 123124'})
        self.assertTrue(form.is_valid())
        self.assertTrue('123123' in form.get_duplicate_skus())


class RangeServiceViewTest(WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.range = Range.objects.create(name='dummy')
        self.url = reverse('dashboard:range-services', args=(self.range.id,))
        self.service1 = create_service(
            title='Service 1', partner_sku='123123', partner_name='Partner 1'
        )
        self.service2 = create_service(
            title='Service 2', partner_sku='123123', partner_name='Partner 2'
        )
        self.service3 = create_service(partner_sku='456')
        self.service4 = create_service(partner_sku='789')
        self.parent = create_service(upc="1234", structure="parent")
        self.child1 = create_service(upc="1234.345", structure="child", parent=self.parent)
        self.child2 = create_service(upc="1234-345", structure="child", parent=self.parent)

    def test_upload_file_with_skus(self):
        range_services_page = self.get(self.url)
        form = range_services_page.form
        form['file_upload'] = Upload('new_skus.txt', b'456')
        form.submit().follow()
        all_services = self.range.all_services()
        self.assertEqual(len(all_services), 1)
        self.assertTrue(self.service3 in all_services)
        range_service_file_upload = RangeServiceFileUpload.objects.get()
        self.assertEqual(range_service_file_upload.range, self.range)
        self.assertEqual(range_service_file_upload.num_new_skus, 1)
        self.assertEqual(range_service_file_upload.status, RangeServiceFileUpload.PROCESSED)
        self.assertEqual(range_service_file_upload.size, 3)

    def test_dupe_skus_warning(self):
        self.range.add_service(self.service3)
        range_services_page = self.get(self.url)
        form = range_services_page.forms[0]
        form['query'] = '456'
        response = form.submit()
        self.assertEqual(list(response.context['messages']), [])
        self.assertEqual(
            response.context['form'].errors['query'],
            ['The services with SKUs or UPCs matching 456 are already in this range']
        )

        form = response.forms[0]
        form['query'] = '456, 789'
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, '1 service added to range')
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message,
            'The services with SKUs or UPCs matching 456 are already in this range'
        )

    def test_missing_skus_warning(self):
        range_services_page = self.get(self.url)
        form = range_services_page.form
        form['query'] = '321'
        response = form.submit()
        self.assertEqual(list(response.context['messages']), [])
        self.assertEqual(
            response.context['form'].errors['query'],
            ['No services exist with a SKU or UPC matching 321']
        )
        form = range_services_page.form
        form['query'] = '456, 321'
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, SUCCESS)
        self.assertEqual(messages[0].message, '1 service added to range')
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, 'No service(s) were found with SKU or UPC matching 321'
        )

    def test_same_skus_within_different_services_warning_query(self):
        range_services_page = self.get(self.url)
        form = range_services_page.form
        form['query'] = '123123'
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, 'There are more than one service with SKU 123123'
        )

    def test_same_skus_within_different_services_warning_file_upload(self):
        range_services_page = self.get(self.url)
        form = range_services_page.form
        form['file_upload'] = Upload('skus.txt', b'123123')
        response = form.submit().follow()
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1].level, WARNING)
        self.assertEqual(
            messages[1].message, 'There are more than one service with SKU 123123'
        )

    def test_adding_child_does_not_add_parent(self):
        range_services_page = self.get(self.url)
        form = range_services_page.forms[0]
        form['query'] = '1234.345'
        form.submit().follow()
        all_services = self.range.all_services()
        self.assertEqual(len(all_services), 1)
        self.assertFalse(self.range.contains_service(self.parent))
        self.assertTrue(self.range.contains_service(self.child1))
        self.assertFalse(self.range.contains_service(self.child2))

        form = range_services_page.forms[0]
        form['query'] = '1234-345'
        form.submit().follow()
        all_services = self.range.all_services()
        self.assertEqual(len(all_services), 1)
        self.assertTrue(self.range.contains_service(self.child1))
        self.assertTrue(self.range.contains_service(self.child2))
        self.assertFalse(self.range.contains_service(self.parent))

    def test_adding_multiple_children_does_not_add_parent(self):
        range_services_page = self.get(self.url)
        form = range_services_page.forms[0]
        form['query'] = '1234.345 1234-345'
        form.submit().follow()
        all_services = self.range.all_services()
        self.assertEqual(len(all_services), 2)
        self.assertTrue(self.range.contains_service(self.child1))
        self.assertTrue(self.range.contains_service(self.child2))
        self.assertFalse(self.range.contains_service(self.parent))

    def test_adding_multiple_comma_separated_children_does_not_add_parent(self):
        range_services_page = self.get(self.url)
        form = range_services_page.forms[0]
        form['query'] = '1234.345, 1234-345'
        form.submit().follow()
        all_services = self.range.all_services()
        self.assertEqual(len(all_services), 2)
        self.assertTrue(self.range.contains_service(self.child1))
        self.assertTrue(self.range.contains_service(self.child2))
        self.assertFalse(self.range.contains_service(self.parent))
