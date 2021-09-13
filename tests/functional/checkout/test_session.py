from django.urls import reverse

from oscar.test import testcases

from . import CheckoutMixin


class TestCheckoutOfDigitalGoods(CheckoutMixin, testcases.WebTestCase):

    def setUp(self):
        super().setUp()
        service = self.create_digital_service()
        self.add_service_to_basket(service)

    def test_buying_a_digital_good_doesnt_error(self):
        payment_details_page = self.get(
            reverse('checkout:index')).maybe_follow()
        preview_page = payment_details_page.click(linkid="view_preview")
        response = preview_page.forms['place_order_form'].submit().follow()
        self.assertIsOk(response)
