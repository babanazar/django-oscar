from django.test.testcases import TestCase
from django.urls import reverse

from sandbox.oscar.apps.catalogue import ServiceReview, Vote
from oscar.test.factories import UserFactory, create_service


class TestAddVoteView(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_voting_on_service_review_returns_404_on_non_public_service(self):
        service = create_service(is_public=False)
        review = ServiceReview.objects.create(service=service, **{
            "title": "Awesome!",
            "score": 5,
            "body": "Wonderful service",
        })
        path = reverse("catalogue:reviews-vote",
                       kwargs={"service_slug": service.slug, "service_pk": service.pk, "pk": review.pk})

        response = self.client.post(path, data={"delta": Vote.UP})

        self.assertEqual(response.status_code, 404)

    def test_voting_on_service_review_redirect_on_public_service(self):
        service = create_service(is_public=True)
        review = ServiceReview.objects.create(service=service, **{
            "title": "Awesome!",
            "score": 5,
            "body": "Wonderful service",
        })
        path = reverse("catalogue:reviews-vote",
                       kwargs={"service_slug": service.slug, "service_pk": service.pk, "pk": review.pk})

        response = self.client.post(path, data={"delta": Vote.UP})

        self.assertRedirects(response, service.get_absolute_url())

    def test_creating_service_review_returns_404_on_non_public_service(self):
        service = create_service(is_public=False)
        path = reverse("catalogue:reviews-add", kwargs={"service_slug": service.slug, "service_pk": service.pk})

        response = self.client.post(path, data={
            "title": "Awesome!",
            "score": 5,
            "body": "Wonderful service",
        })

        self.assertEqual(response.status_code, 404)

    def test_creating_service_review_redirect_on_public_service(self):
        service = create_service(is_public=True)
        path = reverse("catalogue:reviews-add", kwargs={"service_slug": service.slug, "service_pk": service.pk})

        response = self.client.post(path, data={
            "title": "Awesome!",
            "score": 5,
            "body": "Wonderful service",
        })

        self.assertRedirects(response, service.get_absolute_url())


class TestServiceReviewList(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_listing_service_reviews_returns_404_on_non_public_service(self):
        service = create_service(is_public=False)
        path = reverse("catalogue:reviews-list", kwargs={"service_slug": service.slug, "service_pk": service.pk})

        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

    def test_listing_service_reviews_returns_200_on_public_service(self):
        service = create_service(is_public=True)
        path = reverse("catalogue:reviews-list", kwargs={"service_slug": service.slug, "service_pk": service.pk})

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)


class TestServiceReviewDetail(TestCase):
    def setUp(self):
        self.client.force_login(UserFactory())

    def test_retrieving_service_review_returns_404_on_non_public_service(self):
        service = create_service(is_public=False)
        review = ServiceReview.objects.create(service=service, **{
            "title": "Awesome!",
            "score": 5,
            "body": "Wonderful service",
        })
        path = reverse("catalogue:reviews-detail",
                       kwargs={"service_slug": service.slug, "service_pk": service.pk, "pk": review.pk})

        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

    def test_retrieving_service_review_returns_200_on_public_service(self):
        service = create_service(is_public=True)
        review = ServiceReview.objects.create(service=service, **{
            "title": "Awesome!",
            "score": 5,
            "body": "Wonderful service",
        })
        path = reverse("catalogue:reviews-detail",
                       kwargs={"service_slug": service.slug, "service_pk": service.pk, "pk": review.pk})

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
