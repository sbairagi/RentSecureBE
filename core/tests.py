import time
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from core.models import User, App  # import your models

class UserFlowTests(APITestCase):
    def setUp(self):
        # URLs (make sure your urls.py has these names)
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.token_refresh_url = reverse('token_refresh')
        self.change_password_url = reverse('change-password')
        self.reset_password_url = reverse('reset-password')
        self.apps_url = reverse('apps-list')
        self.logs_url = reverse('ai-logs')

        # # User data
        ts = str(int(time.time()))
        self.user_data = {
            "username": f"shubh_{ts}",
            "email": f"shubh_{ts}@example.com",
            "password": "Start2025@1234",
            "full_name": "Shubham Bairagi",
            "phone": f"9876543{ts[-4:]}"
        }
        self.new_password = f"Changed_{ts}_2025@1234"
        self.reset_password_new = f"ResetNow_{ts}_2025@1234"

        # Create an app for logs to refer to
        self.app = App.objects.create(name="Test App", slug="test-app")

    def test_user_register_login_and_flow(self):
        # 1. Register user
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg="User registration failed")

        # 2. Login user to get tokens
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg="Login failed")
        access = response.data.get('access')
        refresh = response.data.get('refresh')
        self.assertIsNotNone(access, "Access token missing")
        self.assertIsNotNone(refresh, "Refresh token missing")

        # 3. Refresh token
        response = self.client.post(self.token_refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg="Token refresh failed")
        new_access = response.data.get('access')
        self.assertIsNotNone(new_access, "New access token missing")

        # Use new_access token for authenticated requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')

        # 4. Change password
        change_pass_data = {
            "old_password": self.user_data["password"],
            "new_password": self.new_password
        }
        response = self.client.put(self.change_password_url, change_pass_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT], msg="Change password failed")

        # 5. Get apps list (should succeed and contain at least our test app)
        response = self.client.get(self.apps_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg="Fetching apps failed")
        self.assertTrue(any(app['id'] == self.app.id for app in response.data), "Test app not found in apps list")

        # 6. Post logs
        log_data = {
            "app": self.app.id,
            "prompt": "What's the weather today?",
            "response": "It's sunny and warm."
        }
        response = self.client.post(self.logs_url, log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg="Posting logs failed")
        log_id = response.data.get('id')
        self.assertIsNotNone(log_id, "Log ID missing after creation")

        # 7. Get logs (should return the log we just posted)
        response = self.client.get(self.logs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg="Fetching logs failed")
        self.assertTrue(any(log['id'] == log_id for log in response.data), "Posted log not found in logs list")

        # 8. Reset password (no auth required)
        reset_pass_data = {
            "username": self.user_data["username"],
            "new_password": self.reset_password_new
        }
        self.client.credentials()  # Remove auth header
        response = self.client.post(self.reset_password_url, reset_pass_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT], msg="Reset password failed")

        # Bonus: Try login with reset password to confirm
        login_data = {
            "username": self.user_data["username"],
            "password": self.reset_password_new
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg="Login with reset password failed")


# You can add more test classes for other parts of your app similarly.
