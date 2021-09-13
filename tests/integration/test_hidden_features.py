from django.urls import reverse

from oscar.test.factories import create_service
from oscar.test.testcases import WebTestCase


class TestHiddenFeatures(WebTestCase):
    is_anonymous = False

    def setUp(self):
        super().setUp()
        self.service = create_service()
        self.wishlists_url = reverse('customer:wishlists-list')

    def test_reviews_enabled(self):
        service_detail_page = self.get(self.service.get_absolute_url())
        self.assertContains(service_detail_page, 'Number of reviews')

    def test_reviews_disabled(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['reviews']):
            service_detail_page = self.get(self.service.get_absolute_url())
            self.assertNotContains(service_detail_page, 'Number of reviews')

    def test_wishlists_enabled(self):
        account_page = self.get(reverse('customer:profile-view'))
        self.assertContains(account_page, self.wishlists_url)
        service_detail_page = self.get(self.service.get_absolute_url())
        self.assertContains(service_detail_page, 'Add to wish list')

    def test_wishlists_disabled(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['wishlists']):
            account_page = self.get(reverse('customer:profile-view'))

            self.assertNotContains(account_page, self.wishlists_url)
            service_detail_page = self.get(self.service.get_absolute_url())
            self.assertNotContains(service_detail_page, 'Add to wish list')
