"""Tests for the quiz list endpoint ``GET /api/quizzes/``."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app_quiz.models import Quiz

User = get_user_model()


class QuizListTests(APITestCase):
    """Listing the quizzes of the logged-in user."""

    def setUp(self):
        self.url = reverse("quiz-list")
        self.user = User.objects.create_user(
            "demo", "demo@example.com", "S3cure-Passw0rd!"
        )
        self.other_user = User.objects.create_user(
            "other", "other@example.com", "S3cure-Passw0rd!"
        )
        self.quiz = Quiz.objects.create(
            owner=self.user,
            title="Own quiz",
            description="Description",
            video_url="https://www.youtube.com/watch?v=abc123",
        )
        self.other_quiz = Quiz.objects.create(
            owner=self.other_user,
            title="Foreign quiz",
            description="Description",
            video_url="https://www.youtube.com/watch?v=def456",
        )
        self.client.force_authenticate(self.user)

    def test_list_returns_200_with_own_quizzes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([quiz["id"] for quiz in response.data], [self.quiz.id])

    def test_list_does_not_contain_foreign_quizzes(self):
        response = self.client.get(self.url)

        titles = [quiz["title"] for quiz in response.data]
        self.assertNotIn(self.other_quiz.title, titles)

    def test_list_without_quizzes_returns_empty_list(self):
        self.client.force_authenticate(User.objects.create_user(
            "empty", "empty@example.com", "S3cure-Passw0rd!"
        ))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_without_login_returns_401(self):
        self.client.force_authenticate(None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
