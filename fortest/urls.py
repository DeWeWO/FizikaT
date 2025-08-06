from django.urls import path
from .views import submit_test, test_view, hello

urlpatterns = [
    path('', hello, name='hello'),
    path('test/', test_view, name='test_view'),
    path('submit/', submit_test, name='submit_test'),
]