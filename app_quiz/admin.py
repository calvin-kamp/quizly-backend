"""Admin configuration for quizzes and their questions."""

from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.StackedInline):
    """Edit the questions of a quiz on the page of the quiz."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Quizzes with their questions."""

    list_display = ("title", "owner", "video_url", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "description", "owner__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Single questions."""

    list_display = ("question_title", "quiz", "answer")
    list_filter = ("quiz",)
    search_fields = ("question_title", "quiz__title")
    readonly_fields = ("created_at", "updated_at")
