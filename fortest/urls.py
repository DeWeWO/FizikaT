from django.urls import path
from .views import submit_test, category_questions  # , test_view

urlpatterns = [
    # path('', test_view, name='test_view'),
    path('submit/', submit_test, name='submit_test'),
    path('category/<int:category_id>/', category_questions, name='category_questions'),
]