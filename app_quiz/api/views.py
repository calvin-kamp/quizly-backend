import yt_dlp
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app_quiz.models import Quiz
from app_quiz.services.quiz_creator import create_quiz_from_url

from .permissions import IsQuizOwner
from .serializers import (
    QuizCreatedSerializer,
    QuizCreateSerializer,
    QuizSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsQuizOwner)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        queryset = Quiz.objects.prefetch_related("questions")

        if self.action == "list":
            return queryset.filter(owner=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return QuizCreateSerializer

        return QuizSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            quiz = create_quiz_from_url(request.user, serializer.validated_data["url"])
        except yt_dlp.utils.DownloadError:
            raise ValidationError({"url": "Video could not be downloaded."})

        return Response(
            QuizCreatedSerializer(quiz).data,
            status=status.HTTP_201_CREATED,
        )
