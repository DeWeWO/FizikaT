from django.urls import path
from .views import QuestionsByCategorySlugView, CategoryListView

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('category/<slug:slug>', QuestionsByCategorySlugView.as_view(), name='questions-by-category'),
]
