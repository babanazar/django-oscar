from http import client as http_client

from django.urls import reverse

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    CategoryFactory, PartnerFactory, ServiceAttributeFactory, ServiceFactory,
    create_service)
from oscar.test.testcases import WebTestCase, add_permissions

Service = get_model('catalogue', 'Service')
ServiceClass = get_model('catalogue', 'ServiceClass')
ServiceCategory = get_model('catalogue', 'ServiceCategory')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'stockrecord')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')

AttributeOptionGroupForm = get_class('dashboard.catalogue.forms',
                                     'AttributeOptionGroupForm')
AttributeOptionFormSet = get_class('dashboard.catalogue.formsets',
                                   'AttributeOptionFormSet')
RelatedFieldWidgetWrapper = get_class('dashboard.widgets',
                                      'RelatedFieldWidgetWrapper')


class TestCatalogueViews(WebTestCase):
    is_staff = True

    def test_exist(self):
        urls = [reverse('dashboard:catalogue-service-list'),
                reverse('dashboard:catalogue-category-list'),
                reverse('dashboard:stock-alert-list'),
                reverse('dashboard:catalogue-service-lookup')]
        for url in urls:
            self.assertIsOk(self.get(url))

    def test_upc_filter(self):
        service1 = create_service(upc='123')
        service2 = create_service(upc='12')
        service3 = create_service(upc='1')

        # no value for upc, all results
        page = self.get("%s?upc=" %
                        reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertIn(service1, services_on_page)
        self.assertIn(service2, services_on_page)
        self.assertIn(service3, services_on_page)

        # filter by upc, one result
        page = self.get("%s?upc=123" %
                        reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertIn(service1, services_on_page)
        self.assertNotIn(service2, services_on_page)
        self.assertNotIn(service3, services_on_page)

        # exact match, one result, no multiple
        page = self.get("%s?upc=12" %
                        reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertNotIn(service1, services_on_page)
        self.assertIn(service2, services_on_page)
        self.assertNotIn(service3, services_on_page)

        # part of the upc, one result
        page = self.get("%s?upc=3" %
                        reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertIn(service1, services_on_page)
        self.assertNotIn(service2, services_on_page)
        self.assertNotIn(service3, services_on_page)

        # part of the upc, two results
        page = self.get("%s?upc=2" %
                        reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertIn(service1, services_on_page)
        self.assertIn(service2, services_on_page)
        self.assertNotIn(service3, services_on_page)

    def test_is_public(self):
        # Can I still find non-public services in dashboard?
        service = create_service(is_public=False, upc="kleine-bats")
        page = self.get("%s?upc=%s" % (
            reverse('dashboard:catalogue-service-list'), service.upc
        ))
        services_on_page = [row.record for row in page.context['services'].page.object_list]
        self.assertEqual(services_on_page, [service])


class TestAStaffUser(WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.partner = PartnerFactory()

    def test_can_create_a_service_without_stockrecord(self):
        category = CategoryFactory()
        service_class = ServiceClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-service-create',
                                args=(service_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new service'
        form['servicecategory_set-0-category'] = category.id
        form.submit()

        self.assertEqual(Service.objects.count(), 1)

    def test_can_create_and_continue_editing_a_service(self):
        category = CategoryFactory()
        service_class = ServiceClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-service-create',
                                args=(service_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new service'
        form['servicecategory_set-0-category'] = category.id
        form['stockrecords-0-partner'] = self.partner.id
        form['stockrecords-0-partner_sku'] = '14'
        form['stockrecords-0-num_in_stock'] = '555'
        form['stockrecords-0-price'] = '13.99'
        page = form.submit(name='action', value='continue')

        self.assertEqual(Service.objects.count(), 1)
        service = Service.objects.all()[0]
        self.assertEqual(service.stockrecords.all()[0].partner, self.partner)
        self.assertRedirects(page, reverse('dashboard:catalogue-service',
                                           kwargs={'pk': service.id}))

    def test_can_update_a_service_without_stockrecord(self):
        new_title = 'foobar'
        category = CategoryFactory()
        service = ServiceFactory(stockrecords=[])

        page = self.get(
            reverse('dashboard:catalogue-service',
                    kwargs={'pk': service.id})
        )
        form = page.forms[0]
        form['servicecategory_set-0-category'] = category.id
        self.assertNotEqual(form['title'].value, new_title)
        form['title'] = new_title
        form.submit()

        try:
            service = Service.objects.get(pk=service.pk)
        except Service.DoesNotExist:
            pass
        else:
            self.assertTrue(service.title == new_title)
            if service.has_stockrecords:
                self.fail('Service has stock records but should not')

    def test_can_create_service_with_required_attributes(self):
        category = CategoryFactory()
        attribute = ServiceAttributeFactory(required=True)
        service_class = attribute.service_class
        page = self.get(reverse('dashboard:catalogue-service-create',
                                args=(service_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new service'
        form['attr_weight'] = '5'
        form['servicecategory_set-0-category'] = category.id
        form.submit()

        self.assertEqual(Service.objects.count(), 1)

    def test_can_delete_a_standalone_service(self):
        service = create_service(partner_users=[self.user])
        category = Category.add_root(name='Test Category')
        ServiceCategory.objects.create(category=category, service=service)

        page = self.get(reverse('dashboard:catalogue-service-delete',
                                args=(service.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-service-list'))
        self.assertEqual(Service.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(ServiceCategory.objects.count(), 0)

    def test_can_delete_a_parent_service(self):
        parent_service = create_service(structure='parent')
        create_service(parent=parent_service)

        url = reverse(
            'dashboard:catalogue-service-delete',
            args=(parent_service.id,))
        page = self.get(url).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-service-list'))
        self.assertEqual(Service.objects.count(), 0)

    def test_can_delete_a_child_service(self):
        parent_service = create_service(structure='parent')
        child_service = create_service(parent=parent_service)

        url = reverse(
            'dashboard:catalogue-service-delete',
            args=(child_service.id,))
        page = self.get(url).form.submit()

        expected_url = reverse(
            'dashboard:catalogue-service', kwargs={'pk': parent_service.pk})
        self.assertRedirects(page, expected_url)
        self.assertEqual(Service.objects.count(), 1)

    def test_can_list_her_services(self):
        service1 = create_service(partner_users=[self.user, ])
        service2 = create_service(partner_name="sneaky", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertIn(service1, services_on_page)
        self.assertIn(service2, services_on_page)

    def test_can_create_a_child_service(self):
        parent_service = create_service(structure='parent')
        url = reverse(
            'dashboard:catalogue-service-create-child',
            kwargs={'parent_pk': parent_service.pk})
        form = self.get(url).form
        form.submit()

        self.assertEqual(Service.objects.count(), 2)

    def test_cant_create_child_service_for_invalid_parents(self):
        # Creates a service with stockrecords.
        invalid_parent = create_service(partner_users=[self.user])
        self.assertFalse(invalid_parent.can_be_parent())
        url = reverse(
            'dashboard:catalogue-service-create-child',
            kwargs={'parent_pk': invalid_parent.pk})
        self.assertRedirects(
            self.get(url), reverse('dashboard:catalogue-service-list'))


class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = ['partner.dashboard_access', ]

    def setUp(self):
        super().setUp()
        add_permissions(self.user, self.permissions)
        self.partner.users.add(self.user)

    def test_can_list_her_services(self):
        service1 = create_service(partner_name="A", partner_users=[self.user])
        service2 = create_service(partner_name="B", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-service-list'))
        services_on_page = [row.record for row
                            in page.context['services'].page.object_list]
        self.assertIn(service1, services_on_page)
        self.assertNotIn(service2, services_on_page)

    def test_cant_create_a_child_service(self):
        parent_service = create_service(structure='parent')
        url = reverse(
            'dashboard:catalogue-service-create-child',
            kwargs={'parent_pk': parent_service.pk})
        response = self.get(url, status='*')
        self.assertEqual(http_client.FORBIDDEN, response.status_code)

    # Tests below can't work because they don't create a stockrecord

    def test_can_create_a_service_without_stockrecord(self):
        pass

    def test_can_update_a_service_without_stockrecord(self):
        pass

    def test_can_create_service_with_required_attributes(self):
        pass

    # Tests below can't work because child services aren't supported with the
    # permission-based dashboard

    def test_can_delete_a_child_service(self):
        pass

    def test_can_delete_a_parent_service(self):
        pass

    def test_can_create_a_child_service(self):
        pass

    def test_cant_create_child_service_for_invalid_parents(self):
        pass
