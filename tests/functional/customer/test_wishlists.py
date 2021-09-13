# -*- coding: utf-8 -*-
from django.urls import reverse_lazy

from oscar.core.loading import get_model
from oscar.test.factories import WishListFactory, create_service
from oscar.test.testcases import WebTestCase

WishList = get_model('wishlists', 'WishList')


class WishListTestMixin(object):
    is_anonymous = False

    def setUp(self):
        super().setUp()
        self.service = create_service()


class TestServiceDetailPage(WishListTestMixin, WebTestCase):

    def test_allows_a_service_to_be_added_to_wishlist(self):
        # Click add to wishlist button
        detail_page = self.get(self.service.get_absolute_url())
        form = detail_page.forms['add_to_wishlist_form']
        response = form.submit()
        self.assertIsRedirect(response)

        # Check a wishlist has been created
        wishlists = self.user.wishlists.all()
        self.assertEqual(1, len(wishlists))

        lines = wishlists[0].lines.all()
        self.assertEqual(1, len(lines))
        self.assertEqual(self.service, lines[0].service)


class TestMoveServiceToAnotherWishList(WishListTestMixin, WebTestCase):
    def setUp(self):
        super().setUp()
        self.wishlist1 = WishListFactory(owner=self.user)
        self.wishlist2 = WishListFactory(owner=self.user)

    def test_move_service_to_another_wishlist_already_containing_it(self):
        self.wishlist1.add(self.service)
        line1 = self.wishlist1.lines.get(service=self.service)
        self.wishlist2.add(self.service)
        url = reverse_lazy('customer:wishlists-move-service-to-another', kwargs={'key': self.wishlist1.key,
                                                                                 'line_pk': line1.pk,
                                                                                 'to_key': self.wishlist2.key})
        self.get(url)
        self.assertEqual(self.wishlist1.lines.filter(service=self.service).count(), 1)
        self.assertEqual(self.wishlist2.lines.filter(service=self.service).count(), 1)

    def test_move_service_to_another_wishlist(self):
        self.wishlist1.add(self.service)
        line1 = self.wishlist1.lines.get(service=self.service)
        url = reverse_lazy('customer:wishlists-move-service-to-another', kwargs={'key': self.wishlist1.key,
                                                                                 'line_pk': line1.pk,
                                                                                 'to_key': self.wishlist2.key})
        self.get(url)
        self.assertEqual(self.wishlist1.lines.filter(service=self.service).count(), 0)
        self.assertEqual(self.wishlist2.lines.filter(service=self.service).count(), 1)
        # Test WishList doesnt contain line and return 404
        self.assertEqual(self.get(url, expect_errors=True).status_code, 404)


class TestWishListRemoveService(WishListTestMixin, WebTestCase):

    def setUp(self):
        super().setUp()
        self.wishlist = WishListFactory(owner=self.user)
        self.wishlist.add(self.service)
        self.line = self.wishlist.lines.get(service=self.service)

    def test_remove_wishlist_line(self):
        delete_wishlist_line_url = reverse_lazy(
            'customer:wishlists-remove-service', kwargs={'key': self.wishlist.key, 'line_pk': self.line.pk}
        )
        self.get(delete_wishlist_line_url).forms[0].submit()
        # Test WishList doesnt contain line and return 404
        self.assertEqual(self.get(delete_wishlist_line_url, expect_errors=True).status_code, 404)

    def test_remove_wishlist_service(self):
        delete_wishlist_service_url = reverse_lazy(
            'customer:wishlists-remove-service', kwargs={'key': self.wishlist.key, 'service_pk': self.line.service.id}
        )
        self.get(delete_wishlist_service_url).forms[0].submit()
        # Test WishList doesnt contain line and return 404
        self.assertEqual(self.get(delete_wishlist_service_url, expect_errors=True).status_code, 404)
