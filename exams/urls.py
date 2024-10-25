from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ExamCategoryViewSet,
    GradeLevelViewSet,
    ExamListView,
    QuestionViewSet,
    UserExamViewSet,
    SubmitAnswerView,
)

router = DefaultRouter()
router.register(r"exam-categories", ExamCategoryViewSet, basename="exam-categories")
router.register(r"grade-levels", GradeLevelViewSet)
router.register(r"questions", QuestionViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("submit-answer/", SubmitAnswerView.as_view(), name="submit-answer"),
    path("practice-exams/", ExamListView.as_view(), name="practice-exams"),
    path(
        "questions/<int:exam_id>/",
        QuestionViewSet.as_view({"get": "list"}),
        name="exam-questions",
    ),
    path(
        "user-exams/start/",
        UserExamViewSet.as_view({"post": "start_exam"}),
        name="start-exam",
    ),
    path(
        "user-exams/<int:pk>/finish/",
        UserExamViewSet.as_view({"post": "finish_exam"}),
        name="finish-exam",
    ),
    path(
        "user-exams/current/",
        UserExamViewSet.as_view({"get": "current_exam"}),
        name="current-exam",
    ),
]
