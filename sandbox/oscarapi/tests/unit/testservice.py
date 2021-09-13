import mock
import decimal
import datetime
import json

from copy import deepcopy
from os.path import dirname, join
from unittest import skipIf
from urllib.error import HTTPError

from django.conf import settings
from django.urls import reverse
from django.test import TestCase, RequestFactory
from django.utils.timezone import make_aware

from oscar.core.loading import get_model

from rest_framework import exceptions

from oscarapi.utils.exists import find_existing_attribute_option_group
from oscarapi.tests.utils import APITest
from oscarapi.serializers.fields import CategoryField
from oscarapi.serializers.service import (
    ServiceLinkSerializer,
    ServiceAttributeValueSerializer,
)
from oscarapi.serializers.admin.partner import AdminStockRecordSerializer
from oscarapi.serializers.admin.service import AdminServiceSerializer
from oscarapi.serializers.service import AttributeOptionGroupSerializer


Service = get_model("catalogue", "Service")
ServiceClass = get_model("catalogue", "ServiceClass")
Category = get_model("catalogue", "Category")
Option = get_model("catalogue", "Option")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
StockRecord = get_model("partner", "StockRecord")


class ServiceListDetailSerializer(ServiceLinkSerializer):
    "subclass of ServiceLinkSerializer to demonstrate showing details in listview"

    class Meta(ServiceLinkSerializer.Meta):
        fields = (
            "url",
            "id",
            "title",
            "structure",
            "description",
            "date_created",
            "date_updated",
            "recommended_services",
            "attributes",
            "categories",
            "service_class",
            "stockrecords",
            "images",
            "price",
            "availability",
            "options",
            "children",
        )


class ServiceTest(APITest):
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
    ]

    def test_service_list(self):
        "Check if we get a list of services with the default attributes"
        self.response = self.get("service-list")
        self.response.assertStatusEqual(200)
        # we should have four services
        self.assertEqual(len(self.response.body), 4)
        # default we have 3 fields
        service = self.response.body[0]
        default_fields = ["id", "url"]
        for field in default_fields:
            self.assertIn(field, service)

    def test_service_list_filter(self):
        standalone_services_url = "%s?structure=standalone" % reverse("service-list")
        self.response = self.get(standalone_services_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 2)

        parent_services_url = "%s?structure=parent" % reverse("service-list")
        self.response = self.get(parent_services_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        child_services_url = "%s?structure=child" % reverse("service-list")
        self.response = self.get(child_services_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        koe_services_url = "%s?structure=koe" % reverse("service-list")
        self.response = self.get(koe_services_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 0)

    @mock.patch("oscarapi.views.service.ServiceList.get_serializer_class")
    def test_servicelist_detail(self, get_serializer_class):
        "The service list should be able to render the same information as the detail page"
        # setup mocks
        get_serializer_class.return_value = ServiceListDetailSerializer

        # define fields to check
        service_detail_fields = (
            "url",
            "id",
            "title",
            "structure",
            "description",
            "date_created",
            "date_updated",
            "recommended_services",
            "attributes",
            "categories",
            "service_class",
            "stockrecords",
            "images",
            "price",
            "availability",
            "options",
            "children",
        )

        # fetch data
        parent_services_url = "%s?structure=parent" % reverse("service-list")
        self.response = self.get(parent_services_url)

        # make assertions
        get_serializer_class.assert_called_once_with()
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        # load service data
        services = self.response.json()
        service_with_children = services[0]

        self.assertEqual(
            service_with_children["structure"],
            "parent",
            "since we filtered on structure=parent the list should contain items with structure=parent",
        )
        # verify all the fields are rendered in the list view
        for field in service_detail_fields:
            self.assertIn(field, service_with_children)

        children = service_with_children["children"]
        self.assertEqual(len(children), 1, "There should be 1 child")
        child = children[0]

        self.assertEqual(
            child["structure"], "child", "the child should have structure=child"
        )
        self.assertNotEqual(service_with_children["id"], child["id"])
        self.assertNotEqual(service_with_children["structure"], child["structure"])
        self.assertNotIn(
            "description", child, "child should not have a description by default"
        )
        self.assertNotIn("images", child, "child should not have images by default")

    def test_service_detail(self):
        "Check service details"
        self.response = self.get(reverse("service-detail", args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = (
            "url",
            "id",
            "title",
            "structure",
            "description",
            "date_created",
            "date_updated",
            "recommended_services",
            "attributes",
            "categories",
            "service_class",
            "images",
            "price",
            "availability",
            "options",
            "children",
        )
        for field in default_fields:
            self.assertIn(field, self.response.body)

        self.response.assertValueEqual("title", "Oscar T-shirt")

    def test_service_attribute_entity(self):
        "Entity attribute type should be supported by means of json method"
        self.response = self.get(reverse("service-detail", args=(4,)))
        self.response.assertStatusEqual(200)

        self.response.assertValueEqual("title", "Entity service")

        attributes = self.response.json()["attributes"]
        attributes_by_name = {a["name"]: a["value"] for a in attributes}

        self.assertIsInstance(attributes_by_name["entity"], str)
        self.assertEqual(
            attributes_by_name["entity"],
            "<User: admin> has no json method, can not convert to json",
        )

    def test_service_attributes(self):
        "All oscar attribute types should be supported except entity"
        self.response = self.get(reverse("service-detail", args=(3,)))
        self.response.assertStatusEqual(200)

        self.response.assertValueEqual("title", "lots of attributes")

        attributes = self.response.json()["attributes"]
        attributes_by_name = {a["name"]: a["value"] for a in attributes}

        # check all the attributes and their types.
        self.assertIsInstance(attributes_by_name["boolean"], bool)
        self.assertEqual(attributes_by_name["boolean"], True)
        self.assertIsInstance(attributes_by_name["date"], str)
        self.assertEqual(attributes_by_name["date"], "2018-01-02")
        self.assertIsInstance(attributes_by_name["datetime"], str)
        self.assertEqual(attributes_by_name["datetime"], "2018-01-02T10:45:00Z")
        self.assertIsInstance(attributes_by_name["file"], str)
        self.assertEqual(
            attributes_by_name["file"], "/media/images/services/2018/01/sony-xa50ES.pdf"
        )
        self.assertIsInstance(attributes_by_name["float"], float)
        self.assertEqual(attributes_by_name["float"], 3.2)
        self.assertIsInstance(attributes_by_name["html"], str)
        self.assertEqual(
            attributes_by_name["html"], "<p>I <strong>am</strong> a test</p>"
        )
        self.assertIsInstance(attributes_by_name["image"], str)
        self.assertEqual(
            attributes_by_name["image"], "/media/images/services/2018/01/IMG_3777.JPG"
        )
        self.assertIsInstance(attributes_by_name["integer"], int)
        self.assertEqual(attributes_by_name["integer"], 7)
        self.assertIsInstance(attributes_by_name["multioption"], list)
        self.assertEqual(attributes_by_name["multioption"], ["Small", "Large"])
        self.assertIsInstance(attributes_by_name["option"], str)
        self.assertEqual(attributes_by_name["option"], "Small")

    def test_service_price(self):
        "See if we get the price information"
        self.response = self.get(reverse("service-price", args=(1,)))
        self.response.assertStatusEqual(200)
        self.assertIn("excl_tax", self.response.body)

        self.response = self.get(reverse("service-price", args=(999999,)))
        self.response.assertStatusEqual(404)

    def test_service_availability(self):
        "See if we get the availability information"
        self.response = self.get(reverse("service-availability", args=(1,)))
        self.response.assertStatusEqual(200)
        self.assertIn("num_available", self.response.body)

        self.response = self.get(reverse("service-availability", args=(999999,)))
        self.response.assertStatusEqual(404)


class _ServiceSerializerTest(TestCase):
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
        "serviceimage",
    ]

    def setUp(self):
        super(_ServiceSerializerTest, self).setUp()
        self.factory = RequestFactory()

    def assertErrorStartsWith(self, ser, name, errorstring):
        self.assertTrue(
            ser.errors[name][0].startswith(errorstring),
            "Error does not start with %s" % errorstring,
        )


@skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
class AdminStockRecordSerializerTest(_ServiceSerializerTest):
    def test_stockrecord_save(self):
        "The AdminStockRecordSerializer should be able to save stuff"
        ser = AdminStockRecordSerializer(
            data={
                "service": 1,
                "partner": "http://testserver/api/admin/partners/1/",
                "partner_sku": "henk",
                "price_currency": "EUR",
                "price": 20,
                "num_in_stock": 34,
                "low_stock_threshold": 4,
            }
        )
        self.assertTrue(ser.is_valid(), "There where errors %s" % ser.errors)

        obj = ser.save()
        self.assertEqual(obj.service.get_title(), "Oscar T-shirt")
        self.assertEqual(obj.partner.name, "Book partner")
        self.assertEqual(obj.price_currency, "EUR")
        self.assertEqual(obj.price, decimal.Decimal("20.00"))
        self.assertEqual(obj.num_in_stock, 34)
        self.assertEqual(obj.low_stock_threshold, 4)
        self.assertEqual(obj.num_allocated, None)


class ServiceAttributeValueSerializerTest(_ServiceSerializerTest):
    def test_serviceattributevalueserializer_error(self):
        "If attributes do not exist on the service class a tidy error should explain"
        ser = ServiceAttributeValueSerializer(
            data={"name": "zult", "code": "zult", "value": "hoolahoop", "service": 1}
        )

        self.assertFalse(
            ser.is_valid(),
            "There should be an error because there is no attribute named zult",
        )
        self.assertEqual(
            ser.errors["value"],
            [
                "No attribute exist with code=zult, please define it in "
                "the service_class first."
            ],
        )

    def test_serviceattributevalueserializer_option(self):
        p = Service.objects.get(pk=1)
        self.assertEqual(str(p.attr.size), "Small")
        ser = ServiceAttributeValueSerializer(
            data={"name": "Size", "code": "size", "value": "Large", "service": 1}
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(str(obj.value), "Large")

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(str(p.attr.size), "Large")

    def test_serviceattributevalueserializer_option_error(self):
        p = Service.objects.get(pk=1)
        self.assertEqual(str(p.attr.size), "Small")
        ser = ServiceAttributeValueSerializer(
            data={"name": "Size", "code": "size", "value": "LUL", "service": 1}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(
            ser.errors, {"value": ["size: Option LUL does not exist."]}
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Size", "code": "size", "value": None, "service": 1}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["Attribute size is required."]})

    def test_serviceattributevalueserializer_text(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.text, "I am some kind of text")
        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Text",
                "code": "text",
                "value": "Donec placerat. Nullam nibh dolor.",
                "service": 3,
            }
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, "Donec placerat. Nullam nibh dolor.")

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.text, "Donec placerat. Nullam nibh dolor.")

    def test_serviceattributevalueserializer_text_error(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.text, "I am some kind of text")
        ser = ServiceAttributeValueSerializer(
            data={"name": "Text", "code": "text", "value": 4, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should fail")

        ser = ServiceAttributeValueSerializer(
            data={"name": "Text", "code": "text", "value": None, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should fail")
        self.assertDictEqual(ser.errors, {"value": ["Attribute text is required."]})

    def test_serviceattributevalueserializer_integer(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.integer, 7)

        ser = ServiceAttributeValueSerializer(
            data={"name": "Integer", "code": "integer", "value": 4, "service": 3}
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, 4)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.integer, 4)

        ser = ServiceAttributeValueSerializer(
            data={"name": "Integer", "code": "integer", "value": "34", "service": 3}
        )
        self.assertTrue(
            ser.is_valid(),
            "Even if the type is wrong, it should still validate because its an integer",
        )
        obj = ser.save()
        self.assertEqual(obj.value, 34)

    def test_serviceattributevalueserializer_integer_error(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.integer, 7)

        ser = ServiceAttributeValueSerializer(
            data={"name": "Integer", "code": "integer", "value": "zult", "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(
            ser.errors,
            {"value": ["Error assigning `zult` to integer, Must be an integer."]},
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Integer", "code": "integer", "value": None, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["Attribute integer is required."]})

    def test_serviceattributevalueserializer_boolean(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.boolean, True)
        ser = ServiceAttributeValueSerializer(
            data={"name": "Boolean", "code": "boolean", "value": False, "service": 3}
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, False)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.boolean, False)

    def test_serviceattributevalueserializer_boolean_error(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.boolean, True)
        ser = ServiceAttributeValueSerializer(
            data={"name": "Boolean", "code": "boolean", "value": object, "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not validate, an object is not a boolean"
        )
        self.assertDictEqual(
            ser.errors,
            {
                "value": [
                    "Error assigning `<class 'object'>` to boolean, Must be a boolean."
                ]
            },
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Boolean", "code": "boolean", "value": None, "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not validate, empty is not allowed"
        )
        self.assertDictEqual(ser.errors, {"value": ["Attribute boolean is required."]})

        ser = ServiceAttributeValueSerializer(
            data={"name": "Boolean", "code": "boolean", "value": 0, "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not validate, an object is not a boolean"
        )
        self.assertDictEqual(
            ser.errors,
            {"value": ["Error assigning `0` to boolean, Must be a boolean."]},
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Boolean", "code": "boolean", "value": "", "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not validate, an object is not a boolean"
        )
        self.assertDictEqual(
            ser.errors, {"value": ["Error assigning `` to boolean, Must be a boolean."]}
        )

    def test_serviceattributevalueserializer_float(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.float, 3.2)
        ser = ServiceAttributeValueSerializer(
            data={"name": "Float", "code": "float", "value": 7.78, "service": 3}
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, 7.78)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.float, 7.78)

        ser = ServiceAttributeValueSerializer(
            data={"name": "Float", "code": "float", "value": 7, "service": 3}
        )
        self.assertTrue(ser.is_valid(), "If the value is an int it should still work")
        obj = ser.save()
        self.assertEqual(obj.value, 7)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.float, 7)

        ser = ServiceAttributeValueSerializer(
            data={"name": "Float", "code": "float", "value": "7.78", "service": 3}
        )
        self.assertTrue(ser.is_valid(), "If a string is a float it should still work")
        obj = ser.save()
        self.assertEqual(obj.value, 7.78)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.float, 7.78)

    def test_serviceattributevalueserializer_float_error(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.float, 3.2)
        ser = ServiceAttributeValueSerializer(
            data={"name": "Float", "code": "float", "value": {}, "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not be valid, a dict is not a float"
        )
        self.assertErrorStartsWith(
            ser,
            "value",
            "Error assigning `{}` to float, float() argument must be a string or a number",
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Float", "code": "float", "value": object, "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not be valid, a dict is not a float"
        )
        self.assertErrorStartsWith(
            ser,
            "value",
            "Error assigning `<class 'object'>` to float, float() argument must be a string or a number",
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Float", "code": "float", "value": "kak", "service": 3}
        )
        self.assertFalse(
            ser.is_valid(), "This should not be valid, a dict is not a float"
        )
        self.assertDictEqual(
            ser.errors, {"value": ["Error assigning `kak` to float, Must be a float."]}
        )

    def test_serviceattributevalueserializer_html(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.html, "<p>I <strong>am</strong> a test</p>")
        ser = ServiceAttributeValueSerializer(
            data={"name": "Html", "code": "html", "value": "<p>koe</p>", "service": 3}
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, "<p>koe</p>")

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.html, "<p>koe</p>")

    def test_serviceattributevalueserializer_html_error(self):
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.text, "I am some kind of text")
        ser = ServiceAttributeValueSerializer(
            data={"name": "Html", "code": "html", "value": 4, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should fail")

        ser = ServiceAttributeValueSerializer(
            data={"name": "Html", "code": "html", "value": None, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should fail")
        self.assertDictEqual(ser.errors, {"value": ["Attribute html is required."]})

        ser = ServiceAttributeValueSerializer(
            data={"name": "Html", "code": "html", "value": object, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should fail")

    def test_serviceattributevalueserializer_date(self):
        p = Service.objects.get(pk=3)
        start_date = datetime.date(2018, 1, 2)
        self.assertEqual(p.attr.date, start_date)
        ser = ServiceAttributeValueSerializer(
            data={"name": "Date", "code": "date", "value": "2030-03-03", "service": 3}
        )
        new_date = datetime.date(2030, 3, 3)
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, new_date)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.date, new_date)

        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Date",
                "code": "date",
                "value": datetime.date(2016, 4, 12),
                "service": 3,
            }
        )
        new_date = datetime.date(2016, 4, 12)
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, new_date)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.date, new_date)

    def test_serviceattributevalueserializer_date_error(self):
        ser = ServiceAttributeValueSerializer(
            data={"name": "Date", "code": "date", "value": "2030", "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertErrorStartsWith(
            ser, "value", "Date has wrong format. Use one of these formats instead:"
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Date", "code": "date", "value": "zult", "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertErrorStartsWith(
            ser, "value", "Date has wrong format. Use one of these formats instead:"
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Date", "code": "date", "value": None, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(ser.errors, {"value": ["Attribute date is required."]})

        ser = ServiceAttributeValueSerializer(
            data={"name": "Date", "code": "date", "value": {}, "service": 3}
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertErrorStartsWith(
            ser, "value", "Date has wrong format. Use one of these formats instead:"
        )

    def test_serviceattributevalueserializer_datetime(self):
        start_date = make_aware(datetime.datetime(2018, 1, 2, 10, 45))
        p = Service.objects.get(pk=3)
        self.assertEqual(p.attr.datetime, start_date)
        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Datetime",
                "code": "datetime",
                "value": "2030-03-03T01:12",
                "service": 3,
            }
        )
        new_date = make_aware(datetime.datetime(2030, 3, 3, 1, 12))
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual(obj.value, new_date)

        p = Service.objects.get(pk=p.pk)
        self.assertEqual(p.attr.datetime, new_date)

    def test_serviceattributevalueserializer_datetime_error(self):
        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Datetime",
                "code": "datetime",
                "value": "2030-03-03LOL01:12",
                "service": 3,
            }
        )
        self.assertFalse(ser.is_valid(), str(ser.errors))
        self.assertErrorStartsWith(
            ser, "value", "Datetime has wrong format. Use one of these formats instead:"
        )

        ser = ServiceAttributeValueSerializer(
            data={"name": "Datetime", "code": "datetime", "value": None, "service": 3}
        )
        self.assertFalse(ser.is_valid(), str(ser.errors))
        self.assertDictEqual(ser.errors, {"value": ["Attribute datetime is required."]})

        ser = ServiceAttributeValueSerializer(
            data={"name": "Datetime", "code": "datetime", "value": list, "service": 3}
        )
        self.assertFalse(ser.is_valid(), str(ser.errors))
        self.assertErrorStartsWith(
            ser, "value", "Datetime has wrong format. Use one of these formats instead:"
        )

    def test_serviceattributevalueserializer_multioption(self):
        p = Service.objects.get(pk=3)
        self.assertEqual([str(o) for o in p.attr.multioption], ["Small", "Large"])

        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Multioption",
                "code": "multioption",
                "value": ["Large"],
                "service": 3,
            }
        )
        self.assertTrue(ser.is_valid(), str(ser.errors))
        obj = ser.save()
        self.assertEqual([str(o) for o in obj.value], ["Large"])

        p = Service.objects.get(pk=p.pk)
        self.assertEqual([str(o) for o in p.attr.multioption], ["Large"])

    def test_serviceattributevalueserializer_multioption_error(self):
        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Multioption",
                "code": "multioption",
                "value": [],
                "service": 3,
            }
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(
            ser.errors, {"value": ["Attribute multioption is required."]}
        )

        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Multioption",
                "code": "multioption",
                "value": None,
                "service": 3,
            }
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(
            ser.errors, {"value": ["Attribute multioption is required."]}
        )

        ser = ServiceAttributeValueSerializer(
            data={
                "name": "Multioption",
                "code": "multioption",
                "value": ["Large", "kip", "geit"],
                "service": 3,
            }
        )
        self.assertFalse(ser.is_valid(), "This should not validate")
        self.assertDictEqual(
            ser.errors, {"value": ["multioption: Option geit,kip does not exist."]}
        )


class CategoryFieldTest(_ServiceSerializerTest):
    def test_write(self):
        "New categories should be created by the field if needed."
        with self.settings(
            CACHES={
                "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
            }
        ):
            self.assertEqual(Category.objects.count(), 1)
            ser = CategoryField(many=True, required=False)
            data = ["Henk > is > een > keel", "En > klaas > is > er > ook > een"]
            validated_data = ser.run_validation(data)
            self.assertEqual(len(validated_data), 2)
            first, second = validated_data
            self.assertEqual(Category.objects.count(), 11)
            self.assertEqual(first.full_slug, "henk/is/een/keel")
            self.assertEqual(second.full_slug, "en/klaas/is/er/ook/een")

    def test_read(self):
        "The field should display categories as a hierarchical string with >"
        self.test_write()
        ser = CategoryField(many=True, required=False)
        val = ser.to_representation(Category.objects.filter(pk__in=[7, 4]))
        self.assertListEqual(val, ["Henk > is > een", "En > klaas"])

    def test_existing_cayegorries_are_not_duplicated(self):
        self.test_write()
        ser = CategoryField(many=True, required=False)
        data = ["Henk > is > een > keel", "En > klaas > is > er > ook > een"]
        validated_data = ser.run_validation(data)
        self.assertEqual(len(validated_data), 2)
        self.assertEqual(
            Category.objects.count(), 11, "No extra categories should have been created"
        )


@skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
class AdminServiceSerializerTest(_ServiceSerializerTest):
    def test_create_service(self):
        "Services should be created by the serializer if needed"
        ser = AdminServiceSerializer(
            data={"service_class": "testtype", "slug": "new-service"}
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 5, "Should be new object, with a high pk")
        self.assertEqual(obj.service_class.slug, "testtype")
        self.assertEqual(obj.slug, "new-service")

    def test_modify_service(self):
        "We should a able to change service fields."
        service = Service.objects.get(pk=3)
        self.assertEqual(service.upc, "attrtypestest")
        self.assertEqual(service.description, "<p>It is a test for the attributes</p>")

        ser = AdminServiceSerializer(
            data={
                "service_class": "testtype",
                "slug": "lots-of-attributes",
                "description": "Henk",
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 3, "service should be the same as passed as instance")
        self.assertEqual(obj.upc, "attrtypestest")
        self.assertEqual(obj.description, "Henk")

    def test_modify_service_error(self):
        """When modifying an attribute, enough information should be passed to be
        able to identify the attribute. An error message should indicate
        missing information"""
        service = Service.objects.get(pk=3)
        self.assertEqual(service.upc, "attrtypestest")
        self.assertEqual(service.description, "<p>It is a test for the attributes</p>")

        ser = AdminServiceSerializer(
            data={
                "service_class": "testtype",
                "slug": "lots-of-attributes",
                "description": "Henk",
                "attributes": [{"name": "Text", "value": "Blaat blaat"}],
            },
            instance=service,
        )
        self.assertFalse(ser.is_valid(), "Should fail because of missing code")
        self.assertDictEqual(
            ser.errors, {"attributes": [{"code": "This field is required."}]}
        )

    def test_switch_service_class(self):
        """When the service class is switched, the service should only have
        attributes from the new service class."""
        service = Service.objects.get(pk=3)
        self.assertEqual(service.attribute_values.count(), 11)
        self.assertEqual(service.attr.boolean, True)
        self.assertEqual(service.attr.date, datetime.date(2018, 1, 2))
        self.assertEqual(
            service.attr.datetime, make_aware(datetime.datetime(2018, 1, 2, 10, 45))
        )
        self.assertEqual(service.attr.float, 3.2)
        self.assertEqual(service.attr.html, "<p>I <strong>am</strong> a test</p>")
        self.assertEqual(service.attr.integer, 7)
        self.assertEqual([str(a) for a in service.attr.multioption], ["Small", "Large"])
        self.assertEqual(str(service.attr.option), "Small")

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "lots-of-attributes",
                "description": "Henk",
                "attributes": [{"name": "Size", "value": "Large", "code": "size"}],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 3, "service should be the same as passed as instance")
        self.assertEqual(obj.service_class.slug, "t-shirt")

        self.assertEqual(
            obj.attribute_values.count(),
            1,
            "Only one attribute should be present now, because the new "
            "service class has none of the old atributes",
        )
        self.assertEqual(str(obj.attr.size), "Large")

        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.date, datetime.date(2018, 1, 2))
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.boolean, True)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(
                obj.attr.datetime, make_aware(datetime.datetime(2018, 1, 2, 10, 45))
            )
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.float, 3.2)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.html, "<p>I <strong>am</strong> a test</p>")
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.integer, 7)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(
                [str(a) for a in obj.attr.multioption], ["Small", "Large"]
            )
        with self.assertRaises(AttributeError):
            self.assertNotEqual(str(obj.attr.option), "Small")

    def test_switch_service_class_patch(self):
        """
        When using patch switching service class should keep existing attributes
        as much as possible. That means we have to look for an existing attribute
        on the new service class with the same code and switch the attribute
        value to that attribute. The rest of the attributes MUST be deleted or
        they may cause errors.
        """
        service = Service.objects.get(pk=3)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "lots-of-attributes",
                "description": "Henk",
                "attributes": [{"name": "Size", "value": "Large", "code": "size"}],
            },
            instance=service,
            partial=True,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(
            obj.attribute_values.count(),
            2,
            "One old attribute is also present on the new service class, so should not be deleted",
        )
        self.assertEqual(str(obj.attr.size), "Large")
        self.assertEqual(obj.attr.text, "I am some kind of text")
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.date, datetime.date(2018, 1, 2))
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.boolean, True)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(
                obj.attr.datetime, make_aware(datetime.datetime(2018, 1, 2, 10, 45))
            )
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.float, 3.2)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.html, "<p>I <strong>am</strong> a test</p>")
        with self.assertRaises(AttributeError):
            self.assertNotEqual(obj.attr.integer, 7)
        with self.assertRaises(AttributeError):
            self.assertNotEqual(
                [str(a) for a in obj.attr.multioption], ["Small", "Large"]
            )
        with self.assertRaises(AttributeError):
            self.assertNotEqual(str(obj.attr.option), "Small")

    def test_add_stockrecords(self):
        "Stockrecords should be added when new."
        service = Service.objects.get(pk=3)
        self.assertEqual(service.stockrecords.count(), 0)

        ser = AdminServiceSerializer(
            data={
                "service_class": "testtype",
                "slug": "lots-of-attributes",
                "description": "Henk",
                "stockrecords": [
                    {
                        "partner_sku": "keiko",
                        "price": "53.67",
                        "partner": "http://testserver/api/admin/partners/1/",
                    }
                ],
            },
            instance=service,
        )

        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.stockrecords.count(), 1)

    def test_modify_stockrecords(self):
        """Even without specifying service id the serializer should be able to
        detect that we are modifying an existing stockrecord because slug is
        unique for stockrecord"""
        service = Service.objects.get(pk=1)
        self.assertEqual(service.stockrecords.count(), 1)
        stockrecord = service.stockrecords.get()
        self.assertEqual(stockrecord.price, decimal.Decimal("10"))

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "stockrecords": [
                    {
                        "partner_sku": "clf-large",
                        "price": "53.67",
                        "partner": "http://testserver/api/admin/partners/1/",
                    }
                ],
            },
            instance=service,
        )

        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "service should be the same as passed as instance")
        self.assertEqual(obj.stockrecords.count(), 1)
        stockrecord.refresh_from_db()
        self.assertEqual(stockrecord.price, decimal.Decimal("53.67"))

    def test_add_stockrecords_error(self):
        "It should not be possible to have multiple stockrecords with same sku for the same partner"
        service = Service.objects.get(pk=1)
        self.assertEqual(service.stockrecords.count(), 1)
        stockrecord = service.stockrecords.get()
        self.assertEqual(stockrecord.price, decimal.Decimal("10"))

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "stockrecords": [
                    {
                        "partner_sku": "clf-med",
                        "price": "53.67",
                        "partner": "http://testserver/api/admin/partners/1/",
                    }
                ],
            },
            instance=service,
        )

        self.assertFalse(ser.is_valid(), "This test should fail the uniqueness test.")

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_add_images(self, urlretrieve):
        "Adding images should work just fine"
        urlretrieve.return_value = (
            join(dirname(__file__), "testdata", "image.jpg"),
            [],
        )

        service = Service.objects.get(pk=3)
        self.assertEqual(service.images.count(), 0)

        request = self.factory.get("%simages/nao-robot.jpg" % settings.STATIC_URL)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "images": [
                    {
                        "original": "https://example.com/testdata/image.jpg",
                        "caption": "HA! IK HEET HARRIE",
                    }
                ],
            },
            instance=service,
            context={"request": request},
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 3, "service should be the same as passed as instance")
        self.assertEqual(obj.images.count(), 1)
        image = obj.images.get()
        self.assertEqual(image.caption, "HA! IK HEET HARRIE")

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_add_broken_image(self, urlretrieve):
        urlretrieve.side_effect = HTTPError(
            url="https://example.com/testdata/image.jpg",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        service = Service.objects.get(pk=3)
        self.assertEqual(service.images.count(), 0)

        request = self.factory.get("%simages/nao-robot.jpg" % settings.STATIC_URL)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "images": [
                    {
                        "original": "https://example.com/image-that-does-not-exist-at-all.png",
                        "caption": "HA! IK HEET HARRIE",
                    }
                ],
            },
            instance=service,
            context={"request": request},
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        with self.assertRaises(exceptions.ValidationError):
            obj = ser.save()

        service.refresh_from_db()
        self.assertEqual(service.images.count(), 0)

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_modify_images(self, urlretrieve):
        "The serializer should automatically detect that an image already exists and update it"
        urlretrieve.return_value = (
            join(dirname(__file__), "testdata", "image.jpg"),
            [],
        )

        service = Service.objects.get(pk=1)
        self.assertEqual(service.images.count(), 1)

        image = service.images.get()
        self.assertEqual(image.original.name, "images/services/2019/05/image.jpg")
        self.assertEqual(image.caption, "I'm a cow")

        request = self.factory.get("%simages/nao-robot.jpg" % settings.STATIC_URL)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "images": [
                    {
                        "original": "https://example.com/testdata/image.jpg",
                        "caption": "HA! IK HEET HARRIE",
                    }
                ],
            },
            instance=service,
            context={"request": request},
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "service should be the same as passed as instance")
        self.assertEqual(obj.images.count(), 1)
        image = obj.images.get()
        self.assertEqual(image.caption, "HA! IK HEET HARRIE")
        self.assertEqual(image.original.name, "images/services/2019/05/image.jpg")

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_modify_images_with_hash(self, urlretrieve):
        "When a hash is included in the url, the serializer should not try to download an image that is allready present locally."
        urlretrieve.return_value.side_effect = Exception(
            "Should not be called because hash was set"
        )

        service = Service.objects.get(pk=1)
        self.assertEqual(service.images.count(), 1)

        image = service.images.get()
        self.assertEqual(image.original.name, "images/services/2019/05/image.jpg")
        self.assertEqual(image.caption, "I'm a cow")

        request = self.factory.get("%simages/nao-robot.jpg" % settings.STATIC_URL)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "images": [
                    {
                        "original": "https://example.com/testdata/image.jpg?sha1=751499a82438277cb3cfb5db268bd41696739b3b",
                        "caption": "HA! IK HEET HoRRIE",
                    }
                ],
            },
            instance=service,
            context={"request": request},
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "service should be the same as passed as instance")
        self.assertEqual(obj.images.count(), 1)
        image = obj.images.get()
        self.assertEqual(image.caption, "HA! IK HEET HoRRIE")
        self.assertEqual(image.original.name, "images/services/2019/05/image.jpg")

    def test_add_options(self):
        self.assertEqual(Option.objects.count(), 0)
        service = Service.objects.get(pk=1)
        self.assertEqual(len(service.options), 0)

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "options": [{"name": "Opdruk", "code": "opdruk", "type": "text"}],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "service should be the same as passed as instance")
        self.assertEqual(Option.objects.count(), 1)
        self.assertGreater(len(service.options), 0)

    def test_modify_options(self):
        self.test_add_options()
        service = Service.objects.get(pk=1)
        (opt,) = service.options
        self.assertEqual(opt.name, "Opdruk")
        self.assertEqual(len(service.options), 1)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "options": [{"name": "Wous", "code": "opdruk", "type": "text"}],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "service should be the same as passed as instance")
        (opt,) = obj.options
        self.assertEqual(opt.name, "Wous")
        self.assertEqual(Option.objects.count(), 1)

    def test_add_existing_options(self):
        self.test_add_options()
        self.assertEqual(Option.objects.count(), 1)
        service = Service.objects.get(pk=3)
        self.assertEqual(len(service.options), 0)

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "options": [{"name": "Opdruk", "code": "opdruk", "type": "text"}],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 3, "service should be the same as passed as instance")
        self.assertEqual(Option.objects.count(), 1)
        self.assertGreater(len(service.options), 0)

    def test_add_recommended_services(self):
        service = Service.objects.get(pk=1)
        self.assertEqual(service.recommended_services.count(), 0)

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "recommended_services": [reverse("service-detail", args=(3,))],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.recommended_services.count(), 1)

    def test_remove_recommended_services(self):
        self.test_add_recommended_services()
        service = Service.objects.get(pk=1)
        self.assertEqual(service.recommended_services.count(), 1)

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "recommended_services": [],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.recommended_services.count(), 0)

    def test_add_categories(self):
        service = Service.objects.get(pk=1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(service.categories.count(), 1)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "categories": [
                    "lal > hoe > laat > is > het",
                    "gin > flauw > idee > gast",
                ],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(Category.objects.count(), 10)
        self.assertEqual(obj.categories.count(), 2)

    def test_remove_categories(self):
        self.test_add_categories()
        service = Service.objects.get(pk=1)
        self.assertEqual(Category.objects.count(), 10)
        self.assertEqual(service.categories.count(), 2)

        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "categories": [],
            },
            instance=service,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(Category.objects.count(), 10)
        self.assertEqual(obj.categories.count(), 0)

    def test_update_categories(self):
        "Partial update should only add categories never delete"
        service = Service.objects.get(pk=1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(service.categories.count(), 1)
        ser = AdminServiceSerializer(
            data={
                "service_class": "t-shirt",
                "slug": "oscar-t-shirt",
                "description": "Henk",
                "categories": ["there can be only one", "ok but two is the maximum"],
            },
            instance=service,
            partial=True,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.categories.count(), 3)


@skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
class TestServiceAdmin(APITest):
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
        "serviceimage",
    ]

    def setUp(self):
        super(TestServiceAdmin, self).setUp()
        with open(join(dirname(__file__), "testdata", "oscar-t-shirt.json")) as p:
            self.tshirt = json.load(p)
        with open(join(dirname(__file__), "testdata", "lots-of-attributes.json")) as p:
            self.attributes = json.load(p)
        with open(join(dirname(__file__), "testdata", "child-service.json")) as p:
            self.child = json.load(p)
        with open(join(dirname(__file__), "testdata", "entity-service.json")) as p:
            self.entity = json.load(p)

    def test_staff_has_no_access_by_default(self):
        "Staff users without explicit admin permissions should not be able to edit services"
        self.login("somebody", "somebody")
        data = deepcopy(self.attributes)
        data["slug"] = "keikeikke"
        data["upc"] = "roekoekoe"
        self.response = self.post("admin-service-list", **data)
        self.response.assertStatusEqual(403)

    def test_post_service(self):
        self.assertEqual(Service.objects.count(), 4)
        self.login("admin", "admin")
        data = deepcopy(self.attributes)
        data["slug"] = "keikeikke"
        data["upc"] = "roekoekoe"
        self.response = self.post("admin-service-list", **data)
        self.response.assertStatusEqual(201)
        self.assertEqual(Service.objects.count(), 5)

        data = deepcopy(self.tshirt)
        data["slug"] = "hoelahoepie"
        data["upc"] = "maalmaal"
        data["stockrecords"][0]["partner_sku"] = "kjdfshkshjfkh"
        self.response = self.post("admin-service-list", **data)
        self.response.assertStatusEqual(201)
        self.assertEqual(Service.objects.count(), 6)

    def test_put_service(self):
        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(3,))
        self.response = self.put(url, **self.attributes)
        self.response.assertStatusEqual(200)

        url = reverse("admin-service-detail", args=(1,))
        self.response = self.put(url, **self.tshirt)
        self.response.assertStatusEqual(200)

    def test_patch_service(self):
        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(3,))
        self.response = self.patch(url, **self.attributes)
        self.response.assertStatusEqual(200)

        url = reverse("admin-service-detail", args=(1,))
        self.response = self.patch(url, **self.tshirt)
        self.response.assertStatusEqual(200)

    def test_post_child_service(self):
        self.login("admin", "admin")
        data = deepcopy(self.child)
        data["slug"] = "child-hoepie"
        data["upc"] = "child-ding"
        data["stockrecords"] = [
            {
                "partner_sku": "henk-het-kind",
                "price_currency": "EUR",
                "price": "110.00",
                "partner": "http://127.0.0.1:8000/api/admin/partners/1/",
            }
        ]
        self.response = self.post("admin-service-list", **data)
        self.response.assertStatusEqual(201)

    def test_patch_service(self):
        self.login("admin", "admin")
        self.response = self.put(
            "admin-service-list",
            **{"upc": 1234, "service_class": "t-shirt", "slug": "oscar-t-shirt-henk"}
        )
        self.response.assertStatusEqual(200)

    def test_put_service_ambiguous(self):
        self.login("admin", "admin")
        self.response = self.put(
            "admin-service-list",
            **{"service_class": "t-shirt", "slug": "oscar-t-shirt-henk"}
        )
        self.response.assertStatusEqual(404)

    def test_put_child(self):
        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(2,))
        self.response = self.put(url, **self.child)
        self.response.assertStatusEqual(200)

    def test_patch_child(self):
        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(2,))
        self.response = self.patch(url, **self.child)
        self.response.assertStatusEqual(200)

    def test_child_error(self):
        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(2,))
        data = deepcopy(self.child)
        data["parent"] = None
        self.response = self.patch(url, **data)
        self.response.assertStatusEqual(400)
        error = str(self.response["attributes"][0]["value"][0])
        self.assertEqual(
            error,
            "Can not find attribute if service_class is empty and parent is empty as well, child without parent?",
        )

    def test_entity_error(self):
        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(4,))

        with self.assertRaises(NotImplementedError) as e:
            self.response = self.put(url, **self.entity)

        msg = (
            "Writable Entity support requires a manual implementation, because "
            "it is not possible to guess how the value sent should be "
            "interpreted. You can override "
            "'oscarapi.serializers.hooks.entity_internal_value' to provide an "
            "implementation"
        )
        self.assertEqual(str(e.exception), msg)

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_image_error(self, urlretrieve):
        urlretrieve.side_effect = HTTPError(
            url="https://example.com/testdata/image.jpg",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        self.login("admin", "admin")
        url = reverse("admin-service-detail", args=(2,))
        data = deepcopy(self.child)
        data["images"] = [{"original": "https://example.com/testdata/image.jpg"}]
        self.response = self.put(url, **data)
        self.response.assertStatusEqual(400)
        self.assertEqual(
            self.response.data,
            [
                "Error when downloading image https://example.com/testdata/image.jpg, 404: Not Found"
            ],
        )


class TestAttributeOptionGroupSerializer(APITest):
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
        "serviceimage",
    ]

    @skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
    def test_put(self):
        self.login("admin", "admin")
        url = reverse("admin-attributeoptiongroup-detail", args=(1,))
        self.response = self.get(url)
        self.assertCountEqual(self.response["options"], ["Large", "Small"])
        self.response = self.put(
            url, options=["Large", "Medium", "Small", "Rokeol"], name="Sizes"
        )
        self.response.assertStatusEqual(200)
        self.assertCountEqual(
            self.response["options"], ["Large", "Medium", "Small", "Rokeol"]
        )

    @skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
    def test_remove(self):
        self.test_put()
        url = reverse("admin-attributeoptiongroup-detail", args=(1,))
        self.response = self.put(url, options=["Small", "Rokeol"], name="Sizes")
        self.response.assertStatusEqual(200)
        self.assertCountEqual(self.response["options"], ["Small", "Rokeol"])

    def test_create(self):
        option_group = AttributeOptionGroup.objects.get()
        self.assertEqual(option_group.options.count(), 2)
        ser = AttributeOptionGroupSerializer(
            data={"options": ["zult", "blup", "knek"], "name": "Hanbrek"}
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.options.count(), 3)

    def test_add_options(self):
        option_group = AttributeOptionGroup.objects.get()
        self.assertEqual(option_group.options.count(), 2)
        ser = AttributeOptionGroupSerializer(
            data={"options": ["Large", "Medium", "Small", "Rokeol"], "name": "Sizes"},
            instance=option_group,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.options.count(), 4)

    def test_remove_options(self):
        self.test_add_options()
        option_group = AttributeOptionGroup.objects.get()
        self.assertEqual(option_group.options.count(), 4)
        ser = AttributeOptionGroupSerializer(
            data={"options": ["Small"], "name": "Sizes"}, instance=option_group
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.options.count(), 1)


class TestServiceClassSerializer(APITest):
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
        "serviceimage",
    ]

    def setUp(self):
        super(TestServiceClassSerializer, self).setUp()
        with open(join(dirname(__file__), "testdata", "service-class.json")) as p:
            self.data = json.load(p)

    def test_find_existing_attribute_option_groups(self):
        o = AttributeOptionGroup.objects.get(name="Sizes")
        self.assertEqual(o.name, "Sizes")
        self.assertCountEqual(
            o.options.values_list("option", flat=True), ["Large", "Small"]
        )

        option = find_existing_attribute_option_group("Sizes", ["Large"])
        self.assertIsNone(option)

        option = find_existing_attribute_option_group(
            "Sizes", ["Large", "Small", "Henk"]
        )
        self.assertIsNone(option)

        option = find_existing_attribute_option_group("Sizes", ["Large", "Small"])
        self.assertEqual(option.name, "Sizes")
        self.assertCountEqual(
            option.options.values_list("option", flat=True), ["Large", "Small"]
        )

    @skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
    def test_post_service_class(self):
        self.login("admin", "admin")
        self.assertEqual(ServiceClass.objects.count(), 3)
        data = deepcopy(self.data)  # remove some of the attributes
        data["name"] = "henk"
        data["slug"] = "henk"
        self.response = self.post("admin-serviceclass-list", **data)
        self.response.assertStatusEqual(201)
        self.assertEqual(ServiceClass.objects.count(), 4)

    @skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
    def test_put_add_options(self):
        "We should be able to options with put"
        self.login("admin", "admin")
        pc = ServiceClass.objects.get(slug="testtype")
        self.assertEqual(pc.options.count(), 0)

        url = reverse("admin-serviceclass-detail", args=("testtype",))
        self.response = self.get(url)
        self.response.assertStatusEqual(200)

        self.assertEqual(
            len(self.response["attributes"]), 11, "Initially there should be 11 options"
        )
        self.assertEqual(
            len(self.response["options"]), 0, "Initially there should be no options"
        )

        data = deepcopy(self.data)  # remove some of the attributes
        data["attributes"] = data["attributes"][:1]
        self.response = self.put(url, **data)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response["attributes"]), 1)
        self.assertEqual(pc.options.count(), 1)
        self.assertEqual(len(self.response["options"]), 1)

    @skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
    def test_put_add_attributes(self):
        "We should be able to add attributes with put"
        self.test_put_add_options()
        pc = ServiceClass.objects.get(slug="testtype")
        self.assertEqual(pc.options.count(), 1)
        self.assertEqual(pc.attributes.count(), 1)

        url = reverse("admin-serviceclass-detail", args=("testtype",))
        data = deepcopy(self.data)
        data["options"] = []
        self.response = self.put(url, **data)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response["attributes"]), 11)
        self.assertEqual(len(self.response["options"]), 0)
        self.assertIsNotNone(
            find_existing_attribute_option_group("Sizes", ["Large", "Small"])
        )

    @skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
    def test_option_group(self):
        "Updating an options group should create new options groups when needed"
        self.assertEqual(AttributeOptionGroup.objects.count(), 1)
        self.assertIsNotNone(
            find_existing_attribute_option_group("Sizes", ["Large", "Small"])
        )

        self.test_put_add_attributes()

        self.assertEqual(AttributeOptionGroup.objects.count(), 3)
        self.assertIsNotNone(
            find_existing_attribute_option_group("Sizes", ["Large", "Small"])
        )
        self.assertIsNotNone(
            find_existing_attribute_option_group("Sizes", ["Large", "Small", "Extreme"])
        )
        self.assertIsNotNone(
            find_existing_attribute_option_group(
                "Sizes", ["Large", "Small", "Humongous"]
            )
        )

        data = deepcopy(self.data)
        data["attributes"] = [
            {
                "option_group": {
                    "options": ["Large", "Small", "Humongous", "Megalomaniac"],
                    "name": "Sizes",
                },
                "name": "multioption",
                "code": "multioption",
                "type": "multi_option",
                "required": True,
            }
        ]
        url = reverse("admin-serviceclass-detail", args=("testtype",))
        self.response = self.put(url, **data)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response["attributes"]), 1)
        self.assertIsNotNone(
            find_existing_attribute_option_group("Sizes", ["Large", "Small"])
        )
        self.assertIsNotNone(
            find_existing_attribute_option_group("Sizes", ["Large", "Small", "Extreme"])
        )
        self.assertIsNone(
            find_existing_attribute_option_group(
                "Sizes", ["Large", "Small", "Humongous"]
            )
        )
        self.assertIsNotNone(
            find_existing_attribute_option_group(
                "Sizes", ["Large", "Small", "Humongous", "Megalomaniac"]
            )
        )


@skipIf(settings.OSCARAPI_BLOCK_ADMIN_API_ACCESS, "Admin API is not enabled")
class AdminCategoryApiTest(APITest):
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
        "serviceimage",
    ]

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_create_category_and_ancestors(self, urlretrieve):
        urlretrieve.return_value = (
            join(dirname(__file__), "testdata", "image.jpg"),
            [],
        )

        self.login("admin", "admin")
        self.assertEqual(Category.objects.count(), 1)
        url = reverse(
            "admin-category-child-list",
            kwargs={"breadcrumbs": "this/does/not/exist/yet"},
        )

        self.response = self.post(
            url,
            **{
                "name": "klaas",
                "slug": "blaat",
                "description": "bloep",
                "image": "https://example.com/testdata/image.jpg",
            }
        )

        self.response.assertStatusEqual(201)
        self.assertEqual(Category.objects.count(), 7)

    def test_create_or_update_category_and_ancestors(self):
        self.test_create_category_and_ancestors()  # pylint: disable=no-value-for-parameter
        self.assertEqual(Category.objects.count(), 7)
        url = reverse(
            "admin-category-child-list",
            kwargs={"breadcrumbs": "this/does/not/exist/yet"},
        )

        self.response = self.post(
            url, **{"name": "klaas", "slug": "blaat", "description": "Klak"}
        )

        self.assertEqual(Category.objects.count(), 7)
        self.response.assertStatusEqual(201)
        self.assertEqual(self.response["description"], "Klak")

    @mock.patch("oscarapi.serializers.fields.urlretrieve")
    def test_create_root_category(self, urlretrieve):
        urlretrieve.return_value = (
            join(dirname(__file__), "testdata", "image.jpg"),
            [],
        )

        self.login("admin", "admin")
        self.assertEqual(Category.objects.count(), 1)

        self.response = self.post(
            "admin-category-list",
            **{
                "name": "blubbie",
                "slug": "blub",
                "description": "brop",
                "image": "https://example.com/testdata/image.jpg",
            }
        )

        self.response.assertStatusEqual(201)
        self.assertEqual(Category.objects.count(), 2)

        # Create category without a slug
        self.response = self.post(
            "admin-category-list",
            **{
                "name": "blubbie blob",
                "description": "brop",
                "image": "https://example.com/testdata/image.jpg",
            }
        )

        self.response.assertStatusEqual(201)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(
            Category.objects.last().slug,
            "blubbie-blob",
            "Category slug not created automatically",
        )

    def test_create_or_update_root_category(self):
        self.test_create_root_category()  # pylint: disable=no-value-for-parameter
        self.assertEqual(Category.objects.count(), 3)

        self.response = self.post(
            "admin-category-list",
            **{"name": "blubbie", "slug": "blub", "description": "Klakaa"}
        )

        self.assertEqual(Category.objects.count(), 3)
        self.response.assertStatusEqual(201)
        self.assertEqual(self.response["description"], "Klakaa")
