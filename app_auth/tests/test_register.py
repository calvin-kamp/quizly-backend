"""Tests for the registration endpoint ``POST /api/register/``."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterTests(APITestCase):
    """Registration with valid and invalid data."""

    def setUp(self):
        self.url = reverse("register")
        self.valid_data = {
            "username": "demo",
            "email": "demo@example.com",
            "password": "S3cure-Passw0rd!",
            "confirmed_password": "S3cure-Passw0rd!",
        }

    def test_register_with_valid_data_returns_201(self):
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"detail": "User created successfully!"})
        self.assertTrue(User.objects.filter(username="demo").exists())

    def test_register_stores_hashed_password(self):
        self.client.post(self.url, self.valid_data, format="json")

        user = User.objects.get(username="demo")
        self.assertNotEqual(user.password, "S3cure-Passw0rd!")
        self.assertTrue(user.check_password("S3cure-Passw0rd!"))

    def test_register_response_does_not_contain_password(self):
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertNotIn("password", response.data)
        self.assertNotIn("confirmed_password", response.data)

    def test_register_with_different_passwords_returns_400(self):
        data = {**self.valid_data, "confirmed_password": "Other-Passw0rd!"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirmed_password", response.data)
        self.assertFalse(User.objects.filter(username="demo").exists())

    def test_register_with_existing_email_returns_400(self):
        User.objects.create_user("other", "demo@example.com", "S3cure-Passw0rd!")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertFalse(User.objects.filter(username="demo").exists())

    def test_register_with_existing_email_in_other_case_returns_400(self):
        User.objects.create_user("other", "DEMO@example.com", "S3cure-Passw0rd!")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_with_existing_username_returns_400(self):
        User.objects.create_user("demo", "other@example.com", "S3cure-Passw0rd!")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_with_weak_password_returns_400(self):
        data = {**self.valid_data, "password": "123", "confirmed_password": "123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="demo").exists())

    def test_register_with_missing_field_returns_400(self):
        for field in self.valid_data:
            with self.subTest(field=field):
                data = {k: v for k, v in self.valid_data.items() if k != field}

                response = self.client.post(self.url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertFalse(User.objects.filter(username="demo").exists())
