"""Tests for dashboard app views."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from dashboard.views import agreement_status_view, retry_signature

User = get_user_model()


class DashboardViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="dash_user",
            email="dash@test.com",
            password="testpass123",
            full_name="Dash User",
            phone="+919999999999",
        )
        self.user.is_staff = True
        self.user.save()

    def _get_request(self, user=None):
        request = self.factory.get("/dashboard/agreements/")
        if user is not None:
            request.user = user
        else:
            request.user = self.user
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        request.session.save()
        return request

    @patch("dashboard.views.render")
    def test_agreement_status_view_returns_200(self, mock_render):
        mock_render.return_value = MagicMock(status_code=200)
        request = self._get_request(self.user)
        response = agreement_status_view(request)
        self.assertEqual(response.status_code, 200)

    @patch("dashboard.views.RentRecord")
    @patch("dashboard.views.send_agreement_for_signature")
    def test_retry_signature_redirects(self, mock_send, mock_rent):
        mock_rent.objects.get.return_value = MagicMock(renter=MagicMock(name="Test"))
        mock_send.return_value = "Sent"
        request = self.factory.post("/dashboard/retry-signature/1/")
        request.user = self.user
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        request.session.save()
        with patch("dashboard.views.redirect") as mock_redirect:
            mock_redirect.return_value = MagicMock(status_code=302)
            response = retry_signature(request, rent_id=1)
            self.assertEqual(response.status_code, 302)
