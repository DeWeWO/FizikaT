from django.contrib import admin
from .models import Question, Categories, User, Register

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'first_name', 'last_name', 'username']
    fieldsets = (
        (None, {
            'fields': (
                'telegram_id',
                'first_name',
                'last_name',
                'username',
            )
        }),
    )

@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'fio']
    fieldsets = (
        (None, {
            'fields': (
                'telegram_id',
                'fio',
            )
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['short_question_text', 'category', 'correct_option']

    def short_question_text(self, obj):
        return obj.question_text[:50]  # faqat 50 ta belgigacha ko‘rsatadi
    short_question_text.short_description = "Savol"

    fieldsets = (
        (None, {
            'fields': (
                'question_text',
                'option_a',
                'option_b',
                'option_c',
                'option_d',
                'correct_option',
                'category',
            )
        }),
    )

@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ['title', 'description']
    readonly_fields = ['slug']
    
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'slug',
                'description',
            )
        }),
    )