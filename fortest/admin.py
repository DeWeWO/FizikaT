from django.contrib import admin
from .models import Question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'correct_option']
    fieldsets = (
        (None, {
            'fields': (
                'question_text',
                'option_a',
                'option_b',
                'option_c',
                'option_d',
                'correct_option',
            )
        }),
    )
