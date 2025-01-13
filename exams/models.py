from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.conf import settings
from users.models import MDA
import json
import random

User = get_user_model()


# Exam Category class (Confirmation/Promotion)
class ExamCategory(models.Model):
    name = models.CharField(max_length=400)
    mda = models.ForeignKey(
        MDA,
        on_delete=models.CASCADE,
        related_name="exam_categories",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name} - {self.mda.name if self.mda else 'No MDA'}"

    class Meta:
        unique_together = ("name", "mda")


# Grade level class (GL1/GL2/GL3 - GL14)
class GradeLevel(models.Model):
    name = models.CharField(max_length=400, unique=True)

    def __str__(self):
        return self.name


# Exam class (Exam to practice for)
class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ExamCategory, on_delete=models.CASCADE)
    grade_level = models.ManyToManyField(GradeLevel)
    duration = models.IntegerField()
    question_count = models.IntegerField(default=0)
    randomized_question_order = models.JSONField(default=list, blank=True, null=True)

    def save(self, *args, **kwargs):
        # If this is a new instance (no primary key yet)
        if not self.pk:
            self.randomized_question_order = []  # Initialize empty list
            super().save(*args, **kwargs)  # Save first to get primary key

        # Now access the questions and randomize the order
        questions = list(self.questions.all())
        if len(questions) > self.question_count:
            questions = random.sample(questions, self.question_count)
        self.randomized_question_order = [q.id for q in questions]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_randomized_questions(self):
        """
        Get questions in a random order, respecting question count limit
        """
        all_questions = list(self.questions.all())
        total_available = len(all_questions)

        # If question_count is 0 or greater than the available questions, use all questions
        questions_to_show = (
            min(total_available, self.question_count)
            if self.question_count > 0
            else total_available
        )

        # Randomly select questions
        selected_questions = random.sample(all_questions, questions_to_show)
        # Randomly shuffle the order of selected questions
        random.shuffle(selected_questions)
        return selected_questions


# Question class (Linked to the exam)
class Question(models.Model):
    CHOICE_KEYS = ["A", "B", "C", "D", "E"]

    exam = models.ForeignKey(Exam, related_name="questions", on_delete=models.CASCADE)
    question_text = models.TextField()
    choice_a = models.CharField(max_length=255, default="")
    choice_b = models.CharField(max_length=255, default="")
    choice_c = models.CharField(max_length=255, default="")
    choice_d = models.CharField(max_length=255, default="")
    choice_e = models.CharField(max_length=255, default="")
    correct_key = models.CharField(
        max_length=1, choices=[(key, key) for key in CHOICE_KEYS], default="A"
    )

    def __str__(self):
        return self.question_text

    @property
    def choices(self):
        return [
            {"key": "A", "value": self.choice_a},
            {"key": "B", "value": self.choice_b},
            {"key": "C", "value": self.choice_c},
            {"key": "D", "value": self.choice_d},
            {"key": "E", "value": self.choice_e},
        ]

    def clean(self):
        if self.correct_key not in self.CHOICE_KEYS:
            raise ValidationError(
                f"Correct key must be one of {', '.join(self.CHOICE_KEYS)}"
            )


# UserAnswer class to the question
class UserAnswer(models.Model):
    CHOICE_KEYS = ["A", "B", "C", "D", "E"]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_exam = models.ForeignKey(
        "UserExam", related_name="user_answers", on_delete=models.CASCADE, null=True
    )
    selected_key = models.CharField(
        max_length=1, choices=[(key, key) for key in CHOICE_KEYS], default="A"
    )

    def __str__(self):
        return f"{self.user} - {self.question} - {self.selected_key}"

    def clean(self):
        if self.selected_key not in self.CHOICE_KEYS:
            raise ValidationError(
                f"Selected key must be one of {', '.join(self.CHOICE_KEYS)}"
            )

    def is_correct(self):
        return self.selected_key == self.question.correct_key


class Meta:
    unique_together = ("user", "question")


# UserExam class to the exam
class UserExam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0)
    attempt = models.IntegerField(default=1)
    randomized_questions = models.JSONField(default=list, blank=True, null=True)
    selected_questions = models.JSONField(default=list, blank=True, null=True)
    question_order = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.exam} - Attempt {self.attempt}"

    def initialize_questions(self):
        """
        Initialize the questions for this attempt by randomly selecting and ordering them
        """
        all_questions = list(self.exam.questions.all().values_list("id", flat=True))
        questions_to_show = (
            min(len(all_questions), self.exam.question_count)
            if self.exam.question_count > 0
            else len(all_questions)
        )

        # Randomly select questions for this attempt
        self.selected_questions = random.sample(all_questions, questions_to_show)
        # Randomize the order of the selected questions
        self.question_order = self.selected_questions.copy()
        random.shuffle(self.question_order)
        self.save()

    def get_ordered_questions(self):
        """
        Get the questions in their randomized order for this attempt
        """
        if not self.question_order:
            self.initialize_questions()

        return Question.objects.filter(id__in=self.question_order).order_by(
            # Preserve the random order we defined
            models.Case(
                *[
                    models.When(id=id, then=pos)
                    for pos, id in enumerate(self.question_order)
                ],
                output_field=models.IntegerField(),
            )
        )

    class Meta:
        pass
