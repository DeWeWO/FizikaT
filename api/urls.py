from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, QuestionViewSet, UserViewSet, RegisterViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'users', UserViewSet)
router.register(r'register', RegisterViewSet)

urlpatterns = [
    path('', include(router.urls)),
]