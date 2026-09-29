"""Tests for ``create_quiz_from_url`` in ``app_quiz.services.quiz_creator``."""

import os
import tempfile
from unittest.mock import patch

import yt_dlp
from django.contrib.auth import get_user_model
from django.test import TestCase

from app_quiz.models import Quiz
from app_quiz.services.quiz_creator import create_quiz_from_url

User = get_user_model()

CREATOR = "app_quiz.services.quiz_creator"


class CreateQuizFromUrlTests(TestCase):
    """The quiz pipeline with the download, Whisper and Gemini replaced."""

    def setUp(self):
        self.url = "https://www.youtube.com/watch?v=abc123"
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
        self.tmp_dir = tempfile.mkdtemp()
        self.audio_path = os.path.join(self.tmp_dir, "audio.m4a")

        self.user = User.objects.create_user(
            "demo", "demo@example.com", "S3cure-Passw0rd!"
        )

        patchers = {
            "download": patch(f"{CREATOR}.download_audio", return_value=self.audio_path),
            "transcribe": patch(f"{CREATOR}.transcribe", return_value="Transcript"),
            "generate": patch(f"{CREATOR}.generate_quiz", return_value=self.generated_quiz),
        }
        self.mocks = {name: patcher.start() for name, patcher in patchers.items()}
        for patcher in patchers.values():
            self.addCleanup(patcher.stop)

    def test_create_saves_quiz_with_questions(self):
        quiz = create_quiz_from_url(self.user, self.url)

        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(quiz.owner, self.user)
        self.assertEqual(quiz.video_url, self.url)
        self.assertEqual(quiz.questions.count(), 10)

    def test_create_passes_transcript_to_gemini(self):
        create_quiz_from_url(self.user, self.url)

        self.mocks["transcribe"].assert_called_once_with(self.audio_path)
        self.mocks["generate"].assert_called_once_with("Transcript")

    def test_create_deletes_temporary_audio_folder(self):
        create_quiz_from_url(self.user, self.url)

        self.assertFalse(os.path.exists(self.tmp_dir))

    def test_create_with_failed_transcription_deletes_audio_folder(self):
        self.mocks["transcribe"].side_effect = RuntimeError("failed")

        with self.assertRaises(RuntimeError):
            create_quiz_from_url(self.user, self.url)

        self.assertFalse(os.path.exists(self.tmp_dir))
        self.assertFalse(Quiz.objects.exists())

    def test_create_with_failed_download_saves_nothing(self):
        self.mocks["download"].side_effect = yt_dlp.utils.DownloadError("failed")

        with self.assertRaises(yt_dlp.utils.DownloadError):
            create_quiz_from_url(self.user, self.url)

        self.assertFalse(Quiz.objects.exists())

    def test_create_with_incomplete_gemini_answer_saves_nothing(self):
        self.mocks["generate"].return_value = {"title": "Only a title"}

        with self.assertRaises(KeyError):
            create_quiz_from_url(self.user, self.url)

        self.assertFalse(Quiz.objects.exists())
