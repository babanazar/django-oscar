from django.test import TestCase

from oscar.apps.dashboard.catalogue import forms
from oscar.test import factories


class TestCreateServiceForm(TestCase):

    def setUp(self):
        self.service_class = factories.ServiceClassFactory()

    def submit(self, data, parent=None):
        return forms.ServiceForm(self.service_class, parent=parent, data=data)

    def test_validates_that_parent_services_must_have_title(self):
        form = self.submit({'structure': 'parent'})
        self.assertFalse(form.is_valid())
        form = self.submit({'structure': 'parent', 'title': 'foo'})
        self.assertTrue(form.is_valid())

    def test_validates_that_child_services_dont_need_a_title(self):
        parent = factories.ServiceFactory(
            service_class=self.service_class, structure='parent')
        form = self.submit({'structure': 'child'}, parent=parent)
        self.assertTrue(form.is_valid())


class TestCreateServiceAttributeForm(TestCase):

    def test_can_create_without_code(self):
        form = forms.ServiceAttributesForm(data={
            "name": "Attr",
            "type": "text"
        })

        self.assertTrue(form.is_valid())

        service_attribute = form.save()

        # check that code is not None or empty string
        self.assertTrue(service_attribute.code)

    def test_option_group_required_if_attribute_is_option_or_multi_option(self):
        option_form = forms.ServiceAttributesForm(data={
            "name": "Attr",
            "type": "option"
        })
        self.assertFalse(option_form.is_valid())
        self.assertEqual(option_form.errors, {'option_group': ['An option group is required']})

        multi_option_form = forms.ServiceAttributesForm(data={
            "name": "Attr",
            "type": "option"
        })
        self.assertFalse(multi_option_form.is_valid())
        self.assertEqual(multi_option_form.errors, {'option_group': ['An option group is required']})
