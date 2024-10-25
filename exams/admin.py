from django.contrib import admin
from .models import (
    ExamCategory,
    GradeLevel,
    Exam,
    Question,
    UserAnswer,
    UserExam,
)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = (
        "question_text",
        "choice_a",
        "choice_b",
        "choice_c",
        "choice_d",
        "correct_key",
    )


class ExamAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]


admin.site.register(Exam, ExamAdmin)

admin.site.register(ExamCategory)
admin.site.register(GradeLevel)
admin.site.register(Question)
admin.site.register(UserAnswer)
admin.site.register(UserExam)
