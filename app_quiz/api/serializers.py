"""Serializers for quizzes and questions."""

from urllib.parse import urlparse

from rest_framework import serializers

from app_quiz.models import Question, Quiz

# Hostnames that are accepted as YouTube URLs.
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


class QuestionSerializer(serializers.ModelSerializer):
    """A question as returned when a quiz is read."""

    class Meta:
        model = Question
        fields = ("id", "question_title", "question_options", "answer")


class QuestionCreatedSerializer(QuestionSerializer):
    """A question as returned after creation, including its timestamps."""

    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ("updated_at", "created_at")


class QuizSerializer(serializers.ModelSerializer):
    """A quiz with its questions, used to list, read and update quizzes.

    Only ``title`` and ``description`` can be changed, all other fields are
    read-only.
    """

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "description",
            "video_url",
            "questions",
            "updated_at",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "video_url")


class QuizCreatedSerializer(QuizSerializer):
    """A quiz as returned after creation, with the timestamps of its questions."""

    questions = QuestionCreatedSerializer(many=True, read_only=True)


class QuizCreateSerializer(serializers.Serializer):
    """Input for creating a quiz: the URL of a YouTube video."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Accept only URLs whose host is a YouTube domain.

        Raises:
            ValidationError: If the host is not one of ``YOUTUBE_HOSTS``.
        """
        if urlparse(value).hostname not in YOUTUBE_HOSTS:
            raise serializers.ValidationError("Only YouTube URLs are allowed.")

        return value
