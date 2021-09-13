from django.test import TestCase

from oscar.apps.catalogue.reviews import forms
from oscar.test.factories import UserFactory, create_service


class TestReviewForm(TestCase):

    def test_cleans_title(self):
        service = create_service()
        reviewer = UserFactory()
        data = {
            'title': '  This service is lovely',
            'body': 'I really like this cheese',
            'score': 0,
            'name': 'JR Hartley',
            'email': 'hartley@example.com'
        }
        form = forms.ServiceReviewForm(
            service=service, user=reviewer, data=data)

        assert form.is_valid()

        review = form.save()
        assert review.title == "This service is lovely"

    def test_validates_empty_data_correctly(self):
        form = forms.ServiceReviewForm(service=None, user=None, data={})
        assert form.is_valid() is False

    def test_validates_correctly(self):
        data = {
            'title': 'This service is lovely',
            'body': 'I really like this cheese',
            'score': 0,
            'name': 'JR Hartley',
            'email': 'hartley@example.com'
        }
        form = forms.ServiceReviewForm(service=None, user=None, data=data)
        assert form.is_valid()


class TestVoteForm(TestCase):

    def setUp(self):
        self.service = create_service()
        self.reviewer = UserFactory()
        self.voter = UserFactory()
        self.review = self.service.reviews.create(
            title='This is nice',
            score=3,
            body="This is the body",
            user=self.reviewer)

    def test_allows_real_users_to_vote(self):
        form = forms.VoteForm(self.review, self.voter, data={'delta': 1})
        self.assertTrue(form.is_valid())

    def test_prevents_users_from_voting_more_than_once(self):
        self.review.vote_up(self.voter)
        form = forms.VoteForm(self.review, self.voter, data={'delta': 1})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors['__all__']) > 0)

    def test_prevents_users_voting_on_their_own_reviews(self):
        form = forms.VoteForm(self.review, self.reviewer, data={'delta': 1})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors['__all__']) > 0)
