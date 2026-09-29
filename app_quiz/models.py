"""Database models for quizzes and their questions."""

from django.conf import settings
from django.db import models


class Quiz(models.Model):
    """A quiz that was generated from a YouTube video.

    Attributes:
        owner: The user who created the quiz.
        title: Title generated from the transcript.
        description: Short summary of the video (up to 150 characters).
        video_url: URL of the YouTube video.
        created_at: Time of creation.
        updated_at: Time of the last change.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return the title of the quiz."""
        return self.title


class Question(models.Model):
    """A multiple-choice question that belongs to a quiz.

    Attributes:
        quiz: The quiz the question belongs to.
        question_title: The text of the question.
        question_options: List with the answer options.
        answer: The correct answer, one of the options.
        created_at: Time of creation.
        updated_at: Time of the last change.
    """

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_title = models.CharField(max_length=500)
    question_options = models.JSONField()
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        """Return the text of the question."""
        return self.question_title
