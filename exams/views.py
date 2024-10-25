from rest_framework import viewsets, permissions
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db import IntegrityError
from django.utils import timezone
import logging
from django.db.models import Prefetch
from .models import (
    ExamCategory,
    GradeLevel,
    Exam,
    Question,
    UserAnswer,
    UserExam,
)
from .serializers import (
    ExamCategorySerializer,
    GradeLevelSerializer,
    ExamSerializer,
    QuestionSerializer,
    UserAnswerSerializer,
    UserExamSerializer,
)

logger = logging.getLogger(__name__)


# Exam Category ViewSet
class ExamCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExamCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Retrieve the MDA of the currenty logged-in user
        user_mda = self.request.user.mda

        if user_mda:
            return ExamCategory.objects.filter(mda=user_mda)
        return ExamCategory.objects.none()


# Grade Level ViewSet
class GradeLevelViewSet(viewsets.ModelViewSet):
    queryset = GradeLevel.objects.all()
    serializer_class = GradeLevelSerializer
    permission_classes = [permissions.IsAuthenticated]


# Exam ViewSet
class ExamListView(generics.ListAPIView):
    serializer_class = ExamSerializer

    def get_queryset(self):
        category = self.request.query_params.get("category")
        grade_level = self.request.query_params.get("grade_level")

        if category and grade_level:
            return Exam.objects.filter(category=category, grade_level__id=grade_level)
        return Exam.objects.none()


# Question ViewSet
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        exam_id = self.request.query_params.get("exam")
        if exam_id:
            return Question.objects.filter(exam_id=exam_id)
        return Question.objects.none()


# SubmitUserAnswer ViewSet
class SubmitAnswerView(APIView):
    def post(self, request):
        question_id = request.data.get("question")
        selected_key = request.data.get("selected_key")
        exam_id = request.data.get("exam")

        try:
            question = Question.objects.get(id=question_id, exam_id=exam_id)
            user_exam = UserExam.objects.get(
                user=request.user, exam_id=exam_id, end_time__isnull=True
            )

            # Create or updatte users answer
            user_answer, created = UserAnswer.objects.update_or_create(
                user=request.user,
                question=question,
                user_exam=user_exam,
                defaults={"selected_key": selected_key},
            )

            # Check if the answer is correct
            is_correct = user_answer.is_correct()

            # Update the exam score
            user_exam, created = UserExam.objects.get_or_create(
                user=request.user, exam_id=exam_id
            )
            if is_correct:
                user_exam.score += 1
                user_exam.save()

            return Response(
                {
                    "user_answer": UserAnswerSerializer(user_answer).data,
                    "user_exam": UserExamSerializer(user_exam).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Question.DoesNotExist:
            return Response(
                {"error": "Invalid question."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except UserExam.DoesNotExist:
            return Response(
                {"error": "No active exam found for this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# UserExam ViewSet
class UserExamViewSet(viewsets.ModelViewSet):
    queryset = UserExam.objects.all()
    serializer_class = UserExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            UserExam.objects.filter(user=self.request.user)
            .select_related("exam")
            .prefetch_related(
                Prefetch(
                    "user_answers",
                    queryset=UserAnswer.objects.select_related("question"),
                )
            )
        )

    @action(detail=False, methods=["post"])
    def start_exam(self, request):
        try:
            exam_id = request.data.get("exam_id")
            if not exam_id:
                return Response(
                    {"error": "exam_id is required"}, status=status.HTTP_400_BAD_REQUEST
                )
            exam = Exam.objects.filter(id=exam_id).first()
            if not exam:
                return Response(
                    {"error": "Invalid exam_id"}, status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(
                data={"exam": exam_id}, context={"request": request}
            )

            if serializer.is_valid():
                user_exam = serializer.save(exam=exam)
                return Response(
                    self.get_serializer(user_exam).data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in start_exam: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def finish_exam(self, request, pk=None):
        user_exam = self.get_object()
        if not user_exam.end_time:
            user_exam.end_time = timezone.now()
            user_exam.save()
        serializer = self.get_serializer(user_exam)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def current_exam(self, request):
        user_exam = UserExam.objects.filter(
            user=request.user, end_time__isnull=True
        ).first()
        if user_exam:
            serializer = self.get_serializer(user_exam)
            return Response(serializer.data)
        return Response(
            {"detail": "No active exam found"}, status=status.HTTP_404_NOT_FOUND
        )
