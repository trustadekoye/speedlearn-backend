from rest_framework import serializers
from .models import (
    ExamCategory,
    GradeLevel,
    Exam,
    Question,
    UserAnswer,
    UserExam,
)
from django.contrib.auth import get_user_model
from users.models import MDA
import random

User = get_user_model()


# Serializer for MDA
class MDASerializer(serializers.ModelSerializer):
    class Meta:
        model = MDA
        fields = ["id", "name"]


# Serializer for ExamCategory
class ExamCategorySerializer(serializers.ModelSerializer):
    mda = MDASerializer(read_only=True)

    class Meta:
        model = ExamCategory
        fields = ["id", "name", "mda"]


# Serializer for GradeLevel
class GradeLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeLevel
        fields = ["id", "name"]


# Serializer for Question
class QuestionSerializer(serializers.ModelSerializer):
    choices = serializers.ReadOnlyField()

    class Meta:
        model = Question
        fields = ["id", "question_text", "choices", "correct_key"]


# Serializer for Exam
class ExamSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    category = ExamCategorySerializer(read_only=True)
    grade_level = GradeLevelSerializer(many=True, read_only=True)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "description",
            "category",
            "grade_level",
            "duration",
            "questions",
            "total_questions",
        ]

    def get_total_questions(self, obj):
        return (
            obj.questions.count() if obj.question_count > 0 else obj.questions.count()
        )

    def get_questions(self, obj):
        # Get the current user exam if it exists
        request = self.context.get("request")
        if request and request.user:
            user_exam = UserExam.objects.filter(
                user=request.user, exam=obj, end_time__isnull=True
            ).first()

            if user_exam:
                questions = user_exam.get_ordered_questions()
            else:
                questions = obj.get_randomized_questions()

            return QuestionSerializer(questions, many=True).data
        return []


# Serlaizeer for UserAnswer (user's selected answer)
class UserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(
        source="question.question_text", read_only=True
    )
    correct_key = serializers.CharField(source="question.correct_key", read_only=True)

    class Meta:
        model = UserAnswer
        fields = ["id", "question", "question_text", "selected_key", "correct_key"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# Serializer for UserExam
class UserExamSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(read_only=True)
    user_answers = UserAnswerSerializer(many=True, read_only=True)
    total_questions = serializers.IntegerField(
        source="exam.questions.count", read_only=True
    )
    correct_answers = serializers.SerializerMethodField()

    class Meta:
        model = UserExam
        fields = [
            "id",
            "user",
            "exam",
            "start_time",
            "end_time",
            "score",
            "total_questions",
            "correct_answers",
            "user_answers",
            "attempt",
        ]
        read_only_fields = ["user", "start_time", "score"]

    def get_correct_answers(self, obj):
        return sum(1 for answer in obj.user_answers.all() if answer.is_correct())

    def create(self, validated_data):
        # Ensure user is set from context
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        # Check if the user already has an active exam
        user = self.context["request"].user
        active_exam = UserExam.objects.filter(user=user, end_time__isnull=True).first()

        if active_exam and not self.instance:
            raise serializers.ValidationError(
                "You have an active exam. Please finish it before starting a new one."
            )
        return data
