from django.urls import path
from .views import submit_test, category_questions

urlpatterns = [
    path('submit/<slug:slug>/', submit_test, name='submit_test'),
    path('<slug:slug>/', category_questions, name='category_questions'),
]