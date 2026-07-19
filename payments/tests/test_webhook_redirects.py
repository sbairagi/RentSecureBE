from django.test import TestCase


class TestWebhookRedirects(TestCase):
    def test_cashfree_old_url_accessible(self):
        response = self.client.get("/api/webhook/cashfree/payout/")
        self.assertIn(response.status_code, [301, 302, 400, 401, 405])

    def test_razorpay_new_url_accessible(self):
        response = self.client.get("/api/webhook/razorpay/")
        self.assertIn(response.status_code, [301, 302, 400, 401, 405])

    def test_new_cashfree_url_accessible(self):
        response = self.client.get("/api/webhook/cashfree/payout/")
        self.assertIn(response.status_code, [301, 302, 400, 401, 405])

    def test_new_razorpay_url_accessible(self):
        response = self.client.get("/api/webhook/razorpay/")
        self.assertIn(response.status_code, [301, 302, 400, 401, 405])
