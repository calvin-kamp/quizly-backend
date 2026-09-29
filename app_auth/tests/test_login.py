"""Tests for the registration endpoint ``POST /api/login/``."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LoginTests(APITestCase):
    """Login with valid and invalid data."""

    def setUp(self):
        self.url = reverse("login")
        self.user_data = {
            "username": "demo",
            "email": "demo@example.com",
            "password": "S3cure-Passw0rd!",
        }

        self.login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"],
        }

        self.user = User.objects.create_user(
            self.user_data["username"],
            self.user_data["email"],
            self.user_data["password"],
        )

    def test_login_with_valid_data_returns_200(self):
        response = self.client.post(self.url, self.login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "detail": "Login successfully!",
                "user": {
                    "id": self.user.id,
                    "username": "demo",
                    "email": "demo@example.com",
                },
            },
        )

    def test_login_response_does_not_contain_tokens(self):
        response = self.client.post(self.url, self.login_data, format="json")

        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_sets_auth_cookies(self):
        response = self.client.post(self.url, self.login_data, format="json")

        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_cookies_are_httponly(self):
        response = self.client.post(self.url, self.login_data, format="json")

        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_login_cookies_have_correct_max_age(self):
        response = self.client.post(self.url, self.login_data, format="json")

        self.assertEqual(
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
            response.cookies["access_token"]["max-age"],
        )
        self.assertEqual(
            settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
            response.cookies["refresh_token"]["max-age"],
        )

    def test_login_with_wrong_password_returns_401(self):
        invalid_login_data = self.login_data.copy()
        invalid_login_data["password"] = "wr0ng_pa$$w0rd"

        response = self.client.post(self.url, invalid_login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_login_with_wrong_username_returns_401(self):
        invalid_login_data = self.login_data.copy()
        invalid_login_data["username"] = "username"

        response = self.client.post(self.url, invalid_login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

    def test_login_with_inactive_user_returns_401(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(self.url, self.login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)
