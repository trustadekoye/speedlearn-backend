from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ExamCategory,
    GradeLevel,
    Exam,
    Question,
    UserAnswer,
    UserExam,
)


@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "mda", "exam_count")
    list_filter = ("mda",)
    search_fields = ("name", "mda__name")

    def exam_count(self, obj):
        return obj.exams_set.count()

    exam_count.short_description = "Number of Exams"


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = (
        "question_text",
        "choice_a",
        "choice_b",
        "choice_c",
        "choice_d",
        "choice_e",
        "correct_key",
    )


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "duration",
        "question_count",
        "display_grade_levels",
    )
    list_filter = ("category", "grade_level")
    search_fields = ("title", "description")
    filter_horizontal = ("grade_level",)
    inlines = [QuestionInline]
    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "category")}),
        ("Exam Settings", {"fields": ("grade_level", "duration", "question_count")}),
    )

    def display_grade_levels(self, obj):
        return ", ".join([grade.name for grade in obj.grade_level.all()])

    display_grade_levels.short_description = "Grade Levels"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("truncated_question", "exam", "correct_key")
    list_filter = ("exam", "correct_key")
    search_fields = ("question_text", "exam__title")

    def truncated_question(self, obj):
        return (
            obj.question_text[:50] + "..."
            if len(obj.question_text) > 50
            else obj.question_text
        )

    truncated_question.short_description = "Question"


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "selected_key", "is_correct", "user_exam")
    list_filter = ("user", "selected_key", "user_exam__exam")
    search_fields = ("user__username", "question__question_text")
    readonly_fields = ("is_correct",)

    def is_correct(self, obj):
        is_correct = obj.selected_key == obj.question.correct_key
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if is_correct else "red",
            "✓" if is_correct else "✗",
        )

    is_correct.short_description = "Correct?"


@admin.register(UserExam)
class UserExamAdmin(admin.ModelAdmin):
    list_display = ("user", "exam", "start_time", "end_time", "score", "attempt")
    list_filter = ("user", "exam", "start_time")
    search_fields = ("user__username", "exam__title")
    readonly_fields = ("score", "start_time", "end_time")

    def completion_status(self, obj):
        if obj.end_time:
            return format_html('<span style="color: green;">Completed</span>')
        return format_html('<span style="color: orange;">In Progress</span>')

    completion_status.short_description = "Status"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user", "exam", "attempt")
        return self.readonly_fields
