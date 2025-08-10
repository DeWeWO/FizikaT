from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, QuestionViewSet, UserViewSet, RegisterViewSet,
    TestResultViewSet, CheckTelegramAdminView, CheckUsernameAvailabilityView,
    TelegramAdminRegisterView, GetAdminTokenView, TelegramLoginView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'users', UserViewSet)
router.register(r'register', RegisterViewSet)
router.register(r'test-results', TestResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check-telegram-admin/<int:telegram_id>/', CheckTelegramAdminView.as_view(), name='check_telegram_admin'),
    path('check-username/<str:username>/', CheckUsernameAvailabilityView.as_view(), name='check_username'),
    path('telegram-admin-register/', TelegramAdminRegisterView.as_view(), name='telegram_admin_register'),
    path('get-admin-token/<int:telegram_id>/', GetAdminTokenView.as_view(), name='get_admin_token'),
    path('telegram-login/<str:token>/', TelegramLoginView.as_view(), name='telegram_login'),
]
