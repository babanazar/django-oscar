from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django_webtest import WebTest

from oscar.apps.customer.forms import ServiceAlertForm
from oscar.apps.customer.models import ServiceAlert
from oscar.core.loading import get_class
from oscar.test.factories import (
    ServiceAlertFactory, UserFactory, create_service, create_stockrecord)

CustomerDispatcher = get_class('customer.utils', 'CustomerDispatcher')
AlertsDispatcher = get_class('customer.alerts.utils', 'AlertsDispatcher')


class TestServiceAlert(WebTest):

    def setUp(self):
        self.user = UserFactory()
        self.service = create_service(num_in_stock=0)

    def test_can_create_a_stock_alert(self):
        service_page = self.app.get(self.service.get_absolute_url(), user=self.user)
        form = service_page.forms['alert_form']
        form.submit()

        alerts = ServiceAlert.objects.filter(user=self.user)
        assert len(alerts) == 1
        alert = alerts[0]
        assert ServiceAlert.ACTIVE == alert.status
        assert alert.service == self.service

    def test_cannot_create_multiple_alerts_for_one_service(self):
        ServiceAlertFactory(user=self.user, service=self.service,
                            status=ServiceAlert.ACTIVE)
        # Alert form should not allow creation of additional alerts.
        form = ServiceAlertForm(user=self.user, service=self.service, data={})

        assert not form.is_valid()
        assert "You already have an active alert for this service" in form.errors['__all__'][0]


class TestAUserWithAnActiveStockAlert(WebTest):

    def setUp(self):
        self.user = UserFactory()
        self.service = create_service()
        self.stockrecord = create_stockrecord(self.service, num_in_stock=0)
        service_page = self.app.get(self.service.get_absolute_url(),
                                    user=self.user)
        form = service_page.forms['alert_form']
        form.submit()

    def test_can_cancel_it(self):
        alerts = ServiceAlert.objects.filter(user=self.user)
        assert len(alerts) == 1
        alert = alerts[0]
        assert not alert.is_cancelled
        self.app.get(
            reverse('customer:alerts-cancel-by-pk', kwargs={'pk': alert.pk}),
            user=self.user)

        alerts = ServiceAlert.objects.filter(user=self.user)
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.is_cancelled

    def test_gets_notified_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        assert self.user.notifications.all().count() == 1

    def test_gets_emailed_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        assert len(mail.outbox) == 1

    def test_does_not_get_emailed_when_it_is_saved_but_still_zero_stock(self):
        self.stockrecord.num_in_stock = 0
        self.stockrecord.save()
        assert len(mail.outbox) == 0

    @mock.patch('oscar.apps.communication.utils.Dispatcher.notify_user')
    def test_site_notification_sent(self, mock_notify):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        mock_notify.assert_called_once_with(
            self.user,
            '{} is back in stock'.format(self.service.title),
            body='<a href="{}">{}</a> is back in stock'.format(
                self.service.get_absolute_url(), self.service.title)
        )

    @mock.patch('oscar.apps.communication.utils.Dispatcher.notify_user')
    def test_service_title_truncated_in_alert_notification_subject(self, mock_notify):
        self.service.title = ('Aut nihil dignissimos perspiciatis. Beatae sed consequatur odit incidunt. '
                              'Quaerat labore perferendis quasi aut sunt maxime accusamus laborum. '
                              'Ut quam repudiandae occaecati eligendi. Nihil rem vel eos.')
        self.service.save()

        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()

        mock_notify.assert_called_once_with(
            self.user,
            '{} is back in stock'.format(self.service.title[:200]),
            body='<a href="{}">{}</a> is back in stock'.format(
                self.service.get_absolute_url(), self.service.title)
        )


class TestAnAnonymousUser(WebTest):

    def test_can_create_a_stock_alert(self):
        service = create_service(num_in_stock=0)
        service_page = self.app.get(service.get_absolute_url())
        form = service_page.forms['alert_form']
        form['email'] = 'john@smith.com'
        form.submit()

        alerts = ServiceAlert.objects.filter(email='john@smith.com')
        assert len(alerts) == 1
        alert = alerts[0]
        assert ServiceAlert.UNCONFIRMED == alert.status
        assert alert.service == service

    def test_can_cancel_unconfirmed_stock_alert(self):
        alert = ServiceAlertFactory(
            user=None, email='john@smith.com', status=ServiceAlert.UNCONFIRMED)
        self.app.get(
            reverse('customer:alerts-cancel-by-key', kwargs={'key': alert.key}))
        alert.refresh_from_db()
        assert alert.is_cancelled

    def test_cannot_create_multiple_alerts_for_one_service(self):
        service = create_service(num_in_stock=0)
        alert = ServiceAlertFactory(user=None, service=service,
                                    email='john@smith.com')
        alert.status = ServiceAlert.ACTIVE
        alert.save()

        # Alert form should not allow creation of additional alerts.
        form = ServiceAlertForm(user=AnonymousUser(), service=service,
                                data={'email': 'john@smith.com'})

        assert not form.is_valid()
        assert "There is already an active stock alert for john@smith.com" in form.errors['__all__'][0]

    def test_cannot_create_multiple_unconfirmed_alerts(self):
        # Create an unconfirmed alert
        ServiceAlertFactory(
            user=None, email='john@smith.com', status=ServiceAlert.UNCONFIRMED)

        # Alert form should not allow creation of additional alerts.
        form = ServiceAlertForm(
            user=AnonymousUser(),
            service=create_service(num_in_stock=0),
            data={'email': 'john@smith.com'},
        )

        assert not form.is_valid()
        message = "john@smith.com has been sent a confirmation email for another service alert on this site."
        assert message in form.errors['__all__'][0]


class TestHurryMode(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.service = create_service()
        self.dispatcher = AlertsDispatcher()

    def test_hurry_mode_not_set_when_stock_high(self):
        # One alert, 5 items in stock. No need to hurry.
        create_stockrecord(self.service, num_in_stock=5)
        ServiceAlert.objects.create(user=self.user, service=self.service)

        self.dispatcher.send_service_alert_email_for_user(self.service)

        assert len(mail.outbox) == 1
        assert 'Beware that the amount of items in stock is limited' not in mail.outbox[0].body

    def test_hurry_mode_set_when_stock_low(self):
        # Two alerts, 1 item in stock. Hurry mode should be set.
        create_stockrecord(self.service, num_in_stock=1)
        ServiceAlert.objects.create(user=self.user, service=self.service)
        ServiceAlert.objects.create(user=UserFactory(), service=self.service)

        self.dispatcher.send_service_alert_email_for_user(self.service)

        assert len(mail.outbox) == 2
        assert 'Beware that the amount of items in stock is limited' in mail.outbox[0].body

    def test_hurry_mode_not_set_multiple_stockrecords(self):
        # Two stockrecords, 5 items in stock for one. No need to hurry.
        create_stockrecord(self.service, num_in_stock=1)
        create_stockrecord(self.service, num_in_stock=5)
        ServiceAlert.objects.create(user=self.user, service=self.service)

        self.dispatcher.send_service_alert_email_for_user(self.service)

        assert 'Beware that the amount of items in stock is limited' not in mail.outbox[0].body

    def test_hurry_mode_set_multiple_stockrecords(self):
        # Two stockrecords, low stock on both. Hurry mode should be set.
        create_stockrecord(self.service, num_in_stock=1)
        create_stockrecord(self.service, num_in_stock=1)
        ServiceAlert.objects.create(user=self.user, service=self.service)
        ServiceAlert.objects.create(user=UserFactory(), service=self.service)

        self.dispatcher.send_service_alert_email_for_user(self.service)

        assert 'Beware that the amount of items in stock is limited' in mail.outbox[0].body


class TestAlertMessageSending(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.service = create_service()
        create_stockrecord(self.service, num_in_stock=1)
        self.dispatcher = AlertsDispatcher()

    @mock.patch('oscar.apps.communication.utils.Dispatcher.dispatch_direct_messages')
    def test_alert_confirmation_uses_dispatcher(self, mock_dispatch):
        alert = ServiceAlert.objects.create(
            email='test@example.com',
            key='dummykey',
            status=ServiceAlert.UNCONFIRMED,
            service=self.service
        )
        AlertsDispatcher().send_service_alert_confirmation_email_for_user(alert)
        assert mock_dispatch.call_count == 1
        assert mock_dispatch.call_args[0][0] == 'test@example.com'

    @mock.patch('oscar.apps.communication.utils.Dispatcher.dispatch_user_messages')
    def test_alert_uses_dispatcher(self, mock_dispatch):
        ServiceAlert.objects.create(user=self.user, service=self.service)
        self.dispatcher.send_service_alert_email_for_user(self.service)
        assert mock_dispatch.call_count == 1
        assert mock_dispatch.call_args[0][0] == self.user

    def test_alert_creates_email_obj(self):
        ServiceAlert.objects.create(user=self.user, service=self.service)
        self.dispatcher.send_service_alert_email_for_user(self.service)
        assert self.user.emails.count() == 1
