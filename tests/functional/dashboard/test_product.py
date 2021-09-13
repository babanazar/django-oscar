import datetime
import io
import os

from django.conf import settings
from django.urls import reverse
from PIL import Image
from webtest import Upload

from sandbox.oscar.apps.catalogue import Service, ServiceAttribute
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.test import factories
from oscar.test.factories import (
    CategoryFactory, ServiceAttributeFactory, ServiceClassFactory,
    ServiceFactory)
from oscar.test.testcases import WebTestCase

User = get_user_model()
ServiceImage = get_model('catalogue', 'ServiceImage')


def generate_test_image():
    tempfile = io.BytesIO()
    image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
    image.save(tempfile, "PNG")
    tempfile.seek(0)
    return tempfile.read()


def media_file_path(path):
    return os.path.join(settings.MEDIA_ROOT, path)


class ServiceWebTest(WebTestCase):
    is_staff = True

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             email='test@email.com',
                                             password='somefancypassword')
        self.user.is_staff = self.is_staff
        self.user.save()

    def get(self, url, **kwargs):
        kwargs['user'] = self.user
        return self.app.get(url, **kwargs)


class TestGatewayPage(ServiceWebTest):
    is_staff = True

    def test_redirects_to_list_page_when_no_query_param(self):
        url = reverse('dashboard:catalogue-service-create')
        response = self.get(url)
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-service-list'))

    def test_redirects_to_list_page_when_invalid_query_param(self):
        url = reverse('dashboard:catalogue-service-create')
        response = self.get(url + '?service_class=bad')
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-service-list'))

    def test_redirects_to_form_page_when_valid_query_param(self):
        pclass = ServiceClassFactory(name='Books', slug='books')
        url = reverse('dashboard:catalogue-service-create')
        response = self.get(url + '?service_class=%s' % pclass.pk)
        expected_url = reverse('dashboard:catalogue-service-create',
                               kwargs={'service_class_slug': pclass.slug})
        self.assertRedirects(response, expected_url)


class TestCreateParentService(ServiceWebTest):
    is_staff = True

    def setUp(self):
        self.pclass = ServiceClassFactory(name='Books', slug='books')
        super().setUp()

    def submit(self, title=None, category=None, upc=None):
        url = reverse('dashboard:catalogue-service-create',
                      kwargs={'service_class_slug': self.pclass.slug})

        service_form = self.get(url).form

        service_form['title'] = title
        service_form['upc'] = upc
        service_form['structure'] = 'parent'

        if category:
            service_form['servicecategory_set-0-category'] = category.id

        return service_form.submit()

    def test_title_is_required(self):
        response = self.submit(title='')

        self.assertContains(response, "must have a title")
        self.assertEqual(Service.objects.count(), 0)

    def test_requires_a_category(self):
        response = self.submit(title="Nice T-Shirt")
        self.assertContains(response, "must have at least one category")
        self.assertEqual(Service.objects.count(), 0)

    def test_for_smoke(self):
        category = CategoryFactory()
        response = self.submit(title='testing', category=category)
        self.assertIsRedirect(response)
        self.assertEqual(Service.objects.count(), 1)

    def test_doesnt_allow_duplicate_upc(self):
        ServiceFactory(parent=None, upc="12345")
        category = CategoryFactory()
        self.assertTrue(Service.objects.get(upc="12345"))

        response = self.submit(title="Nice T-Shirt", category=category,
                               upc="12345")

        self.assertEqual(Service.objects.count(), 1)
        self.assertNotEqual(Service.objects.get(upc='12345').title,
                            'Nice T-Shirt')
        self.assertContains(response,
                            "Service with this UPC already exists.")


class TestCreateChildService(ServiceWebTest):
    is_staff = True

    def setUp(self):
        self.pclass = ServiceClassFactory(name='Books', slug='books')
        self.parent = ServiceFactory(structure='parent', stockrecords=[])
        super().setUp()

    def test_categories_are_not_required(self):
        url = reverse('dashboard:catalogue-service-create-child',
                      kwargs={'parent_pk': self.parent.pk})
        page = self.get(url)

        service_form = page.form
        service_form['title'] = expected_title = 'Nice T-Shirt'
        service_form.submit()

        try:
            service = Service.objects.get(title=expected_title)
        except Service.DoesNotExist:
            self.fail('creating a child service did not work')

        self.assertEqual(service.parent, self.parent)


class TestServiceUpdate(ServiceWebTest):

    def test_service_update_form(self):
        self.service = factories.ServiceFactory()
        url = reverse('dashboard:catalogue-service',
                      kwargs={'pk': self.service.id})

        page = self.get(url)
        service_form = page.form
        service_form['title'] = expected_title = 'Nice T-Shirt'
        page = service_form.submit()

        service = Service.objects.get(id=self.service.id)

        self.assertEqual(page.context['service'], self.service)
        self.assertEqual(service.title, expected_title)


class TestServiceClass(ServiceWebTest):
    def setUp(self):
        super().setUp()
        self.pclass = ServiceClassFactory(name='T-Shirts', slug='tshirts')

        for attribute_type, __ in ServiceAttribute.TYPE_CHOICES:
            values = {
                'type': attribute_type, 'code': attribute_type,
                'service_class': self.pclass, 'name': attribute_type,
            }
            if attribute_type == ServiceAttribute.OPTION:
                option_group = factories.AttributeOptionGroupFactory()
                self.option = factories.AttributeOptionFactory(group=option_group)
                values['option_group'] = option_group
            elif attribute_type == ServiceAttribute.MULTI_OPTION:
                option_group = factories.AttributeOptionGroupFactory()
                self.multi_option = factories.AttributeOptionFactory(group=option_group)
                values['option_group'] = option_group
            ServiceAttributeFactory(**values)
        self.service = factories.ServiceFactory(service_class=self.pclass)
        self.url = reverse('dashboard:catalogue-service',
                           kwargs={'pk': self.service.id})

    def test_service_update_attribute_values(self):
        page = self.get(self.url)
        service_form = page.form
        # Send string field values due to an error
        # in the Webtest during multipart form encode.
        service_form['attr_text'] = 'test1'
        service_form['attr_integer'] = '1'
        service_form['attr_float'] = '1.2'
        service_form['attr_boolean'] = 'yes'
        service_form['attr_richtext'] = 'longread'
        service_form['attr_date'] = '2016-10-12'

        file1 = Upload('file1.txt', b"test-1", 'text/plain')
        image1 = Upload('image1.png', generate_test_image(), 'image/png')
        service_form['attr_file'] = file1
        service_form['attr_image'] = image1
        service_form.submit()

        # Reloading model instance to re-initiate ServiceAttributeContainer
        # with new attributes.
        self.service = Service.objects.get(pk=self.service.id)
        self.assertEqual(self.service.attr.text, 'test1')
        self.assertEqual(self.service.attr.integer, 1)
        self.assertEqual(self.service.attr.float, 1.2)
        self.assertTrue(self.service.attr.boolean)
        self.assertEqual(self.service.attr.richtext, 'longread')
        self.assertEqual(self.service.attr.date, datetime.date(2016, 10, 12))

        file1_path = media_file_path(self.service.attr.file.name)
        self.assertTrue(
            os.path.isfile(file1_path)
        )
        with open(file1_path) as file1_file:
            self.assertEqual(
                file1_file.read(),
                "test-1"
            )

        image1_path = media_file_path(self.service.attr.image.name)
        self.assertTrue(
            os.path.isfile(image1_path)
        )
        with open(image1_path, "rb") as image1_file:
            self.assertEqual(
                image1_file.read(),
                image1.content
            )

        page = self.get(self.url)
        service_form = page.form
        service_form['attr_text'] = 'test2'
        service_form['attr_integer'] = '2'
        service_form['attr_float'] = '5.2'
        service_form['attr_boolean'] = ''
        service_form['attr_richtext'] = 'article'
        service_form['attr_date'] = '2016-10-10'
        file2 = Upload('file2.txt', b"test-2", 'text/plain')
        image2 = Upload('image2.png', generate_test_image(), 'image/png')
        service_form['attr_file'] = file2
        service_form['attr_image'] = image2
        service_form.submit()

        self.service = Service.objects.get(pk=self.service.id)
        self.assertEqual(self.service.attr.text, 'test2')
        self.assertEqual(self.service.attr.integer, 2)
        self.assertEqual(self.service.attr.float, 5.2)
        self.assertFalse(self.service.attr.boolean)
        self.assertEqual(self.service.attr.richtext, 'article')
        self.assertEqual(self.service.attr.date, datetime.date(2016, 10, 10))

        file2_path = media_file_path(self.service.attr.file.name)
        self.assertTrue(
            os.path.isfile(file2_path)
        )
        with open(file2_path) as file2_file:
            self.assertEqual(
                file2_file.read(),
                "test-2"
            )

        image2_path = media_file_path(self.service.attr.image.name)
        self.assertTrue(
            os.path.isfile(image2_path)
        )
        with open(image2_path, "rb") as image2_file:
            self.assertEqual(
                image2_file.read(),
                image2.content
            )


class TestServiceImages(ServiceWebTest):

    def setUp(self):
        super().setUp()
        self.service = factories.ServiceFactory()
        self.url = reverse('dashboard:catalogue-service',
                           kwargs={'pk': self.service.id})

    def test_service_images_upload(self):
        page = self.get(self.url)
        service_form = page.form
        image1 = Upload('image1.png', generate_test_image(), 'image/png')
        image2 = Upload('image2.png', generate_test_image(), 'image/png')
        image3 = Upload('image3.png', generate_test_image(), 'image/png')

        service_form['images-0-original'] = image1
        service_form['images-1-original'] = image2
        service_form.submit(name='action', value='continue').follow()
        self.service = Service.objects.get(pk=self.service.id)
        self.assertEqual(self.service.images.count(), 2)
        page = self.get(self.url)
        service_form = page.form
        service_form['images-2-original'] = image3
        service_form.submit()
        self.service = Service.objects.get(pk=self.service.id)
        self.assertEqual(self.service.images.count(), 3)
        images = self.service.images.all()

        self.assertEqual(images[0].display_order, 0)
        image1_path = media_file_path(images[0].original.name)
        self.assertTrue(os.path.isfile(image1_path))
        with open(image1_path, "rb") as image1_file:
            self.assertEqual(
                image1_file.read(),
                image1.content
            )

        self.assertEqual(images[1].display_order, 1)
        image2_path = media_file_path(images[1].original.name)
        self.assertTrue(os.path.isfile(image2_path))
        with open(image2_path, "rb") as image2_file:
            self.assertEqual(
                image2_file.read(),
                image2.content
            )

        self.assertEqual(images[2].display_order, 2)
        image3_path = media_file_path(images[2].original.name)
        self.assertTrue(os.path.isfile(image3_path))
        with open(image3_path, "rb") as image3_file:
            self.assertEqual(
                image3_file.read(),
                image3.content
            )

    def test_service_images_reordering(self):
        im1 = factories.ServiceImageFactory(service=self.service, display_order=1)
        im2 = factories.ServiceImageFactory(service=self.service, display_order=2)
        im3 = factories.ServiceImageFactory(service=self.service, display_order=3)

        self.assertEqual(
            list(ServiceImage.objects.all().order_by("display_order")),
            [im1, im2, im3]
        )

        page = self.get(self.url)
        service_form = page.form
        service_form['images-1-display_order'] = '3'  # 1 is im2
        service_form['images-2-display_order'] = '4'  # 2 is im3
        service_form['images-0-display_order'] = '5'  # 0 is im1
        service_form.submit()

        self.assertEqual(
            list(ServiceImage.objects.all().order_by("display_order")),
            [im2, im3, im1]
        )
