"""Tests for the admin panel of quizzes and questions."""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app_quiz.models import Question, Quiz

User = get_user_model()


class QuizAdminTests(TestCase):
    """Quizzes and questions can be viewed and edited in the admin panel."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@example.com", "S3cure-Passw0rd!"
        )
        self.quiz = Quiz.objects.create(
            owner=self.admin_user,
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
        self.client.force_login(self.admin_user)

    def test_quiz_list_is_available_in_admin(self):
        response = self.client.get(reverse("admin:app_quiz_quiz_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Own quiz")

    def test_question_list_is_available_in_admin(self):
        response = self.client.get(reverse("admin:app_quiz_question_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Question?")

    def test_quiz_page_shows_its_questions(self):
        url = reverse("admin:app_quiz_quiz_change", args=[self.quiz.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Question?")

    def test_quiz_can_be_changed_in_admin(self):
        url = reverse("admin:app_quiz_quiz_change", args=[self.quiz.id])
        data = {
            "owner": self.admin_user.id,
            "title": "New title",
            "description": "Description",
            "video_url": self.quiz.video_url,
            "questions-TOTAL_FORMS": 1,
            "questions-INITIAL_FORMS": 1,
            "questions-MIN_NUM_FORMS": 0,
            "questions-MAX_NUM_FORMS": 1000,
            "questions-0-id": self.question.id,
            "questions-0-quiz": self.quiz.id,
            "questions-0-question_title": "New question?",
            "questions-0-question_options": json.dumps(["A", "B", "C", "D"]),
            "questions-0-answer": "B",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.quiz.refresh_from_db()
        self.question.refresh_from_db()
        self.assertEqual(self.quiz.title, "New title")
        self.assertEqual(self.question.question_title, "New question?")
        self.assertEqual(self.question.answer, "B")

    def test_question_can_be_changed_in_admin(self):
        url = reverse("admin:app_quiz_question_change", args=[self.question.id])
        data = {
            "quiz": self.quiz.id,
            "question_title": "Changed question?",
            "question_options": json.dumps(["A", "B", "C", "D"]),
            "answer": "C",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.question_title, "Changed question?")
        self.assertEqual(self.question.answer, "C")
