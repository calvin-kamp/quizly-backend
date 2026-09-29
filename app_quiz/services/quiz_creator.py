"""Creation of a quiz from a YouTube URL."""

import os
import shutil

from django.db import transaction

from app_quiz.models import Question, Quiz

from .gemini import generate_quiz
from .whisper import transcribe
from .youtube import download_audio


def create_quiz_from_url(owner, url: str) -> Quiz:
    """Create and save a quiz for a YouTube video.

    Downloads the audio, transcribes it and deletes the temporary audio file.
    Gemini then generates the questions, and the quiz is saved together with
    them in one transaction.

    Args:
        owner: The user who owns the new quiz.
        url: URL of the YouTube video.

    Returns:
        The saved quiz.

    Raises:
        yt_dlp.utils.DownloadError: If the video cannot be downloaded.
        json.JSONDecodeError: If Gemini does not return valid JSON.
        KeyError: If the answer of Gemini misses a required field.
    """
    transcript = _get_transcript(url)
    data = generate_quiz(transcript)

    return _save_quiz(owner, url, data)


def _get_transcript(url: str) -> str:
    """Download the audio of the video and return its transcript.

    The temporary folder of the audio file is deleted afterwards, also when the
    transcription fails.
    """
    audio_path = download_audio(url)

    try:
        return transcribe(audio_path)
    finally:
        shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)


def _save_quiz(owner, url: str, data: dict) -> Quiz:
    """Save the quiz and its questions in one transaction."""
    with transaction.atomic():
        quiz = Quiz.objects.create(
            owner=owner,
            title=data["title"],
            description=data["description"],
            video_url=url,
        )
        Question.objects.bulk_create(_build_questions(quiz, data["questions"]))

    return quiz


def _build_questions(quiz: Quiz, questions: list) -> list:
    """Create the unsaved ``Question`` objects of a quiz."""
    return [
        Question(
            quiz=quiz,
            question_title=question["question_title"],
            question_options=question["question_options"],
            answer=question["answer"],
        )
        for question in questions
    ]
