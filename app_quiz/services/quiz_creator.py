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
    audio_path = download_audio(url)

    try:
        transcript = transcribe(audio_path)
    finally:
        shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)

    data = generate_quiz(transcript)

    with transaction.atomic():
        quiz = Quiz.objects.create(
            owner=owner,
            title=data["title"],
            description=data["description"],
            video_url=url,
        )
        Question.objects.bulk_create(
            [
                Question(
                    quiz=quiz,
                    question_title=question["question_title"],
                    question_options=question["question_options"],
                    answer=question["answer"],
                )
                for question in data["questions"]
            ]
        )

    return quiz
