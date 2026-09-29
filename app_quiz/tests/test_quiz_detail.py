"""Tests for the quiz detail endpoint ``/api/quizzes/<id>/``."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app_quiz.models import Question, Quiz

User = get_user_model()


class QuizDetailTests(APITestCase):
    """Reading, changing and deleting a single quiz."""

    def setUp(self):
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
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_title="Question?",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )
        self.other_quiz = Quiz.objects.create(
            owner=self.other_user,
            title="Foreign quiz",
            description="Description",
            video_url="https://www.youtube.com/watch?v=def456",
        )
        self.url = reverse("quiz-detail", args=[self.quiz.id])
        self.other_url = reverse("quiz-detail", args=[self.other_quiz.id])
        self.client.force_authenticate(self.user)

    def test_retrieve_own_quiz_returns_200_with_questions(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Own quiz")
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(response.data["questions"][0]["answer"], "A")

    def test_retrieve_questions_do_not_contain_timestamps(self):
        response = self.client.get(self.url)

        question = response.data["questions"][0]
        self.assertNotIn("created_at", question)
        self.assertNotIn("updated_at", question)

    def test_retrieve_foreign_quiz_returns_403(self):
        response = self.client.get(self.other_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_unknown_quiz_returns_404(self):
        response = self.client.get(reverse("quiz-detail", args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_without_login_returns_401(self):
        self.client.force_authenticate(None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_own_quiz_updates_title(self):
        response = self.client.patch(self.url, {"title": "New title"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, "New title")

    def test_patch_does_not_change_read_only_fields(self):
        data = {"video_url": "https://youtu.be/other", "id": 9999}

        self.client.patch(self.url, data, format="json")

        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.video_url, "https://www.youtube.com/watch?v=abc123")
        self.assertNotEqual(self.quiz.id, 9999)

    def test_patch_foreign_quiz_returns_403(self):
        response = self.client.patch(self.other_url, {"title": "Hacked"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.other_quiz.refresh_from_db()
        self.assertEqual(self.other_quiz.title, "Foreign quiz")

    def test_put_returns_405(self):
        response = self.client.put(self.url, {"title": "New title"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_own_quiz_returns_204(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())

    def test_delete_quiz_deletes_its_questions(self):
        self.client.delete(self.url)

        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_delete_foreign_quiz_returns_403(self):
        response = self.client.delete(self.other_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Quiz.objects.filter(id=self.other_quiz.id).exists())
