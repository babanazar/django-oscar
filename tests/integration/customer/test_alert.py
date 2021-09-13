from django.test import TestCase

from oscar.apps.customer.models import ServiceAlert
from oscar.core.compat import get_user_model
from oscar.test.factories import UserFactory, create_service

User = get_user_model()


class TestAnAlertForARegisteredUser(TestCase):

    def setUp(self):
        user = UserFactory()
        service = create_service()
        self.alert = ServiceAlert.objects.create(user=user, service=service)

    def test_defaults_to_active(self):
        assert self.alert.is_active
