"""Serializers for quizzes and questions."""

from rest_framework import serializers

from app_quiz.models import Question, Quiz
from app_quiz.utils import normalize_youtube_url


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
    """A quiz as returned after creation, with question timestamps."""

    questions = QuestionCreatedSerializer(many=True, read_only=True)


class QuizCreateSerializer(serializers.Serializer):
    """Input for creating a quiz: the URL of a YouTube video."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Accept only YouTube video URLs, stored in the standard form.

        Returns:
            The URL in the form ``https://www.youtube.com/watch?v=<id>``.

        Raises:
            ValidationError: If the URL is not the URL of a YouTube video.
        """
        video_url = normalize_youtube_url(value)

        if video_url is None:
            raise serializers.ValidationError(
                "Only URLs of YouTube videos are allowed."
            )

        return video_url
