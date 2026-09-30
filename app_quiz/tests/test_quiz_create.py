"""Tests for the quiz creation endpoint ``POST /api/quizzes/``."""

import tempfile
from unittest.mock import patch

import yt_dlp
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app_quiz.models import Quiz

User = get_user_model()

CREATOR = "app_quiz.services.quiz_creator"


class QuizCreateTests(APITestCase):
    """Quiz creation with valid and invalid data.

    The download, Whisper and Gemini are replaced, so no network is needed.
    """

    def setUp(self):
        self.url = reverse("quiz-list")
        self.valid_data = {"url": "https://www.youtube.com/watch?v=vu3xGr-lNVI"}
        self.generated_quiz = {
            "title": "Test quiz",
            "description": "A short summary.",
            "questions": [
                {
                    "question_title": f"Question {number}?",
                    "question_options": ["A", "B", "C", "D"],
                    "answer": "A",
                }
                for number in range(10)
            ],
        }

        self.user = User.objects.create_user(
            "demo", "demo@example.com", "S3cure-Passw0rd!"
        )
        self.client.force_authenticate(self.user)

        audio_path = f"{tempfile.mkdtemp()}/audio.m4a"
        patchers = {
            "download": patch(f"{CREATOR}.download_audio", return_value=audio_path),
            "transcribe": patch(f"{CREATOR}.transcribe", return_value="Transcript"),
            "generate": patch(f"{CREATOR}.generate_quiz", return_value=self.generated_quiz),
        }
        self.mocks = {name: patcher.start() for name, patcher in patchers.items()}
        for patcher in patchers.values():
            self.addCleanup(patcher.stop)

    def test_create_quiz_with_valid_data_returns_201(self):
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test quiz")
        self.assertEqual(response.data["video_url"], self.valid_data["url"])
        self.assertEqual(len(response.data["questions"]), 10)

    def test_create_quiz_saves_quiz_for_the_user(self):
        self.client.post(self.url, self.valid_data, format="json")

        quiz = Quiz.objects.get()
        self.assertEqual(quiz.owner, self.user)
        self.assertEqual(quiz.questions.count(), 10)

    def test_create_quiz_response_contains_question_timestamps(self):
        response = self.client.post(self.url, self.valid_data, format="json")

        question = response.data["questions"][0]
        self.assertIn("created_at", question)
        self.assertIn("updated_at", question)

    def test_create_quiz_saves_standard_video_url(self):
        video_urls = (
            "https://youtu.be/vu3xGr-lNVI?si=abc",
            "https://m.youtube.com/watch?v=vu3xGr-lNVI",
            "https://youtube.com/watch?v=vu3xGr-lNVI&t=42s&list=PL123",
            "https://www.youtube.com/shorts/vu3xGr-lNVI",
        )

        for video_url in video_urls:
            with self.subTest(video_url=video_url):
                response = self.client.post(
                    self.url, {"url": video_url}, format="json"
                )

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(
                    response.data["video_url"],
                    "https://www.youtube.com/watch?v=vu3xGr-lNVI",
                )
                self.mocks["download"].assert_called_with(
                    "https://www.youtube.com/watch?v=vu3xGr-lNVI"
                )

    def test_create_quiz_without_login_returns_401(self):
        self.client.force_authenticate(None)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Quiz.objects.exists())

    def test_create_quiz_with_invalid_url_returns_400(self):
        invalid_urls = (
            "https://example.com/video",
            "https://www.youtube.com/",
            "https://www.youtube.com/watch?v=short",
            "not-a-url",
            "",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                response = self.client.post(self.url, {"url": url}, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("url", response.data)

        self.mocks["download"].assert_not_called()

    def test_create_quiz_without_url_returns_400(self):
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)

    def test_create_quiz_with_failed_download_returns_400(self):
        self.mocks["download"].side_effect = yt_dlp.utils.DownloadError("failed")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("url", response.data)
        self.assertFalse(Quiz.objects.exists())
