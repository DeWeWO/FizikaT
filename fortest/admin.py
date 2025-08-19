# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import *

CustomUser = get_user_model()

# CustomUser admin sozlamalari
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'telegram_id', 'telegram_username', 'first_name', 'last_name', 
                   'is_staff', 'is_active', 'created_via_telegram', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'created_via_telegram', 'date_joined')
    search_fields = ('username', 'telegram_username', 'first_name', 'last_name', 'telegram_id')
    ordering = ('-date_joined',)
    
    # Telegram orqali yaratilgan foydalanuvchilar uchun fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Telegram Ma\'lumotlari', {
            'fields': ('telegram_id', 'telegram_username', 'created_via_telegram'),
        }),
    )
    
    # Yangi foydalanuvchi qo'shishda ko'rsatiladigan fieldlar
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Telegram Ma\'lumotlari', {
            'fields': ('telegram_id', 'telegram_username', 'created_via_telegram'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'created_via_telegram')

# Categories admin
@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created', 'updated')
    list_filter = ('created', 'updated')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created', 'updated')

# Question admin
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'category', 'correct_option', 'created')
    list_filter = ('category', 'correct_option', 'created')
    search_fields = ('question_text', 'option_a', 'option_b', 'option_c', 'option_d')
    list_editable = ('correct_option',)
    readonly_fields = ('created', 'updated')
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = "Savol matni"


# Register admin
@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ('fio', 'telegram_id')
    search_fields = ('fio', 'telegram_id')

@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'group_name', 'added_at', 'is_active')
    search_fields = ('group_name',)

# TestResult admin
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user_fio', 'user_telegram_id', 'category', 'total_questions', 'correct_answers', 'completed_at')
    list_filter = ('category', 'completed_at')
    search_fields = ('user__fio', 'user__telegram_id')
    readonly_fields = ('completed_at',)
    
    def user_fio(self, obj):
        return obj.user.fio
    user_fio.short_description = "FIO"

    def user_telegram_id(self, obj):
        return obj.user.telegram_id
    user_telegram_id.short_description = "Telegram ID"
    
# Admin panel sozlamalari
admin.site.site_header = "Test Bot Admin Panel"
admin.site.site_title = "Test Bot Admin"
admin.site.index_title = "Bosh sahifa"