from urllib.parse import urlparse

from rest_framework import serializers

from app_quiz.models import Question, Quiz

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("id", "question_title", "question_options", "answer")


class QuestionCreatedSerializer(QuestionSerializer):
    class Meta(QuestionSerializer.Meta):
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
            "created_at",
            "updated_at",
        )


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        )
        read_only_fields = ("id", "created_at", "updated_at", "video_url")


class QuizCreatedSerializer(QuizSerializer):
    questions = QuestionCreatedSerializer(many=True, read_only=True)


class QuizCreateSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate_url(self, value):
        if urlparse(value).hostname not in YOUTUBE_HOSTS:
            raise serializers.ValidationError("Only YouTube URLs are allowed.")

        return value
