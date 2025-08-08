from django.urls import path
from .views import QuestionsByCategorySlugView, CategoryListView, category_questions

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('category/<slug:slug>', QuestionsByCategorySlugView.as_view(), name='questions-by-category'),
    path("test/<slug:slug>/", category_questions, name="category_questions"),
]
