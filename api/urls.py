from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, QuestionViewSet, RegisterViewSet,
    TestResultViewSet, CheckTelegramAdminView, CheckUsernameAvailabilityView,
    TelegramAdminRegisterView, CustomUsersListView, RegisterUsersListView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'register', RegisterViewSet)
router.register(r'test-results', TestResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check-telegram-admin/<int:telegram_id>/', CheckTelegramAdminView.as_view(), name='check_telegram_admin'),
    path('check-username/<str:username>/', CheckUsernameAvailabilityView.as_view(), name='check_username'),
    path('telegram-admin-register/', TelegramAdminRegisterView.as_view(), name='telegram_admin_register'),
    path('custom-users/', CustomUsersListView.as_view(), name='custom_users_list'),
    path('register-users/', RegisterUsersListView.as_view(), name='register_users_list'),
]