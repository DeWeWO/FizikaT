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

# TelegramSession admin
@admin.register(TelegramSession)
class TelegramSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_token', 'created_at', 'last_used')
    list_filter = ('created_at', 'last_used')
    search_fields = ('user__username', 'session_token')
    readonly_fields = ('session_token', 'created_at', 'last_used')

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

# TelegramUser admin
@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'username', 'telegram_id', 'is_admin')
    list_filter = ('first_name', 'last_name')
    search_fields = ('first_name', 'last_name', 'username', 'telegram_id')
    readonly_fields = ('telegram_id',)

# Admin model admin
@admin.register(Admin)
class AdminModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_active', 'is_superuser', 'created_via_telegram', 'created_at')
    list_filter = ('is_active', 'is_superuser', 'created_via_telegram', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'email')
    readonly_fields = ('created_at', 'last_login')

# Register admin
@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ('fio', 'telegram_id')
    search_fields = ('fio', 'telegram_id')

# TestResult admin
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'category', 'total_questions', 'correct_answers', 'percentage', 'completed_at')
    list_filter = ('category', 'completed_at', 'percentage')
    search_fields = ('telegram_id',)
    readonly_fields = ('completed_at',)
    
    # Statistika uchun
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
            
            # Statistika hisoblash
            stats = {
                'total_tests': qs.count(),
                'average_percentage': qs.aggregate(avg=models.Avg('percentage'))['avg'] or 0,
                'total_users': qs.values('telegram_id').distinct().count(),
            }
            
            response.context_data['summary'] = stats
        except (AttributeError, KeyError):
            pass
            
        return response

# Admin panel sozlamalari
admin.site.site_header = "Test Bot Admin Panel"
admin.site.site_title = "Test Bot Admin"
admin.site.index_title = "Bosh sahifa"