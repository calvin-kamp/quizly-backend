"""Tests for the token refresh endpoint ``POST /api/token/refresh/``."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class TokenRefreshTests(APITestCase):
    """Refresh the access token with the refresh cookie."""

    def setUp(self):
        self.url = reverse("token_refresh")
        self.login_data = {"username": "demo", "password": "S3cure-Passw0rd!"}

        User.objects.create_user(
            self.login_data["username"],
            "demo@example.com",
            self.login_data["password"],
        )

    def test_refresh_with_valid_cookie_returns_200(self):
        self.client.post(reverse("login"), self.login_data, format="json")

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token refreshed"})

    def test_refresh_sets_new_access_cookie(self):
        self.client.post(reverse("login"), self.login_data, format="json")

        response = self.client.post(self.url)

        self.assertIn("access_token", response.cookies)
        self.assertTrue(response.cookies["access_token"].value)
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_refresh_without_cookie_returns_401(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)

    def test_refresh_with_invalid_cookie_returns_401(self):
        self.client.cookies["refresh_token"] = "invalid"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)
