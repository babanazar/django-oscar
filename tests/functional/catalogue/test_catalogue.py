from http import client as http_client

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext

from oscar.apps.catalogue.models import Category
from oscar.test.factories import create_service
from oscar.test.testcases import WebTestCase


class TestServiceDetailView(WebTestCase):

    def test_enforces_canonical_url(self):
        p = create_service()
        kwargs = {'service_slug': '1_wrong-but-valid-slug_1',
                  'pk': p.id}
        wrong_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(p.get_absolute_url() in response.location)

    def test_child_to_parent_redirect(self):
        """
        We test against separate view in order to isolate tested service
        detail view, since default value of `ServiceDetailView.enforce_parent`
        property has changed. Thus, by default the view should not redirect
        to the parent page, but we need to make sure that original solution
        works well.
        """
        parent_service = create_service(structure='parent')
        kwargs = {'service_slug': parent_service.slug,
                  'pk': parent_service.id}
        parent_service_url = reverse('catalogue:parent_detail', kwargs=kwargs)

        child = create_service(
            title="Variant 1", structure='child', parent=parent_service)
        kwargs = {'service_slug': child.slug,
                  'pk': child.id}
        child_url = reverse('catalogue:parent_detail', kwargs=kwargs)

        response = self.app.get(parent_service_url)
        self.assertEqual(http_client.OK, response.status_code, response.location)

        response = self.app.get(child_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)

    def test_is_public_on(self):
        service = create_service(upc="kleine-bats", is_public=True)

        kwargs = {'service_slug': service.slug, 'pk': service.id}
        url = reverse('catalogue:detail', kwargs=kwargs)
        response = self.app.get(url)

        self.assertEqual(response.status_code, http_client.OK)

    def test_is_public_off(self):
        service = create_service(upc="kleine-bats", is_public=False)

        kwargs = {'service_slug': service.slug, 'pk': service.id}
        url = reverse('catalogue:detail', kwargs=kwargs)
        response = self.app.get(url, expect_errors=True)

        self.assertEqual(response.status_code, http_client.NOT_FOUND)


class TestServiceListView(WebTestCase):

    def test_shows_add_to_basket_button_for_available_service(self):
        service = create_service(num_in_stock=1)
        page = self.app.get(reverse('catalogue:index'))
        self.assertContains(page, service.title)
        self.assertContains(page, gettext("Add to basket"))

    def test_shows_not_available_for_out_of_stock_service(self):
        service = create_service(num_in_stock=0)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, service.title)
        self.assertContains(page, "Unavailable")

    def test_shows_pagination_navigation_for_multiple_pages(self):
        per_page = settings.OSCAR_SERVICES_PER_PAGE
        title = "Service #%d"
        for idx in range(0, int(1.5 * per_page)):
            create_service(title=title % idx)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, "Page 1 of 2")

    def test_is_public_on(self):
        service = create_service(upc="grote-bats", is_public=True)
        page = self.app.get(reverse('catalogue:index'))
        services_on_page = list(page.context['services'].all())
        self.assertEqual(services_on_page, [service])

    def test_is_public_off(self):
        create_service(upc="kleine-bats", is_public=False)
        page = self.app.get(reverse('catalogue:index'))
        services_on_page = list(page.context['services'].all())
        self.assertEqual(services_on_page, [])


class TestServiceCategoryView(WebTestCase):

    def setUp(self):
        self.category = Category.add_root(name="Services")

    def test_browsing_works(self):
        correct_url = self.category.get_absolute_url()
        response = self.app.get(correct_url)
        self.assertEqual(http_client.OK, response.status_code)

    def test_enforces_canonical_url(self):
        kwargs = {'category_slug': '1_wrong-but-valid-slug_1',
                  'pk': self.category.pk}
        wrong_url = reverse('catalogue:category', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(self.category.get_absolute_url() in response.location)

    def test_is_public_off(self):
        category = Category.add_root(name="Foobars", is_public=False)
        response = self.app.get(category.get_absolute_url(), expect_errors=True)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)
        return category

    def test_is_public_on(self):
        category = Category.add_root(name="Barfoos", is_public=True)
        response = self.app.get(category.get_absolute_url())
        self.assertEqual(http_client.OK, response.status_code)
        return category

    def test_browsable_contains_public_child(self):
        "If the parent is public the child should be in browsable if it is public as well"
        cat = self.test_is_public_on()
        child = cat.add_child(name="Koe", is_public=True)
        self.assertTrue(child in Category.objects.all().browsable())

        child.is_public = False
        child.save()
        self.assertTrue(child not in Category.objects.all().browsable())

    def test_browsable_hides_public_child(self):
        "If the parent is not public the child should not be in browsable evn if it is public"
        cat = self.test_is_public_off()
        child = cat.add_child(name="Koe", is_public=True)
        self.assertTrue(child not in Category.objects.all().browsable())

    def test_is_public_child(self):
        cat = self.test_is_public_off()
        child = cat.add_child(name="Koe", is_public=True)
        response = self.app.get(child.get_absolute_url())
        self.assertEqual(http_client.OK, response.status_code)

        child.is_public = False
        child.save()
        response = self.app.get(child.get_absolute_url(), expect_errors=True)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)
