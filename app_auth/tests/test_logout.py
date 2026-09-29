"""Tests for the logout endpoint ``POST /api/logout/``."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class LogoutTests(APITestCase):
    """Logout with and without a logged-in user."""

    def setUp(self):
        self.url = reverse("logout")
        self.login_data = {"username": "demo", "password": "S3cure-Passw0rd!"}

        User.objects.create_user(
            self.login_data["username"],
            "demo@example.com",
            self.login_data["password"],
        )

    def login(self):
        self.client.post(reverse("login"), self.login_data, format="json")

    def test_logout_returns_200(self):
        self.login()

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_logout_deletes_auth_cookies(self):
        self.login()

        response = self.client.post(self.url)

        for cookie_name in ("access_token", "refresh_token"):
            with self.subTest(cookie=cookie_name):
                self.assertEqual(response.cookies[cookie_name].value, "")
                self.assertEqual(response.cookies[cookie_name]["max-age"], 0)

    def test_logout_blacklists_refresh_token(self):
        self.login()
        refresh_token = self.client.cookies["refresh_token"].value

        self.client.post(self.url)

        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(reverse("token_refresh"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_cookies_returns_200(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_with_invalid_refresh_cookie_returns_200(self):
        self.client.cookies["refresh_token"] = "invalid"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
