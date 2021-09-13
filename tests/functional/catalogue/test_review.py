from django.urls import reverse

from sandbox.oscar.apps.catalogue import review_added
from sandbox.oscar.test.contextmanagers import mock_signal_receiver
from oscar.test.factories import UserFactory, create_service
from oscar.test.testcases import WebTestCase


class TestACustomer(WebTestCase):

    def setUp(self):
        self.service = create_service()

    def test_reviews_list_sorting_form(self):
        reviews_page = self.app.get(reverse(
            'catalogue:reviews-list',
            kwargs={'service_slug': self.service.slug, 'service_pk': self.service.id}
        ))
        self.assertFalse(reviews_page.context['form'].errors)

    def test_can_add_a_review_when_anonymous(self):
        detail_page = self.app.get(self.service.get_absolute_url())
        add_review_page = detail_page.click(linkid='write_review')
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form['name'] = 'John Doe'
        form['email'] = 'john@example.com'
        form.submit()

        self.assertEqual(1, self.service.reviews.all().count())

    def test_can_add_a_review_when_signed_in(self):
        user = UserFactory()
        detail_page = self.app.get(self.service.get_absolute_url(),
                                   user=user)
        add_review_page = detail_page.click(linkid="write_review")
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form.submit()

        self.assertEqual(1, self.service.reviews.all().count())

    def test_adding_a_review_sends_a_signal(self):
        review_user = UserFactory()
        detail_page = self.app.get(self.service.get_absolute_url(),
                                   user=review_user)
        with mock_signal_receiver(review_added) as receiver:
            add_review_page = detail_page.click(linkid="write_review")
            form = add_review_page.forms['add_review_form']
            form['title'] = 'This is great!'
            form['score'] = 5
            form['body'] = 'Loving it, loving it, loving it'
            form.submit()
            self.assertEqual(receiver.call_count, 1)
        self.assertEqual(1, self.service.reviews.all().count())
