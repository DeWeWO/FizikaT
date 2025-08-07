from rest_framework import generics
from fortest.models import Question, Categories
from .serializers import QuestionSerializer, CategorySerializer
from django.shortcuts import get_object_or_404

class QuestionsByCategorySlugView(generics.ListAPIView):
    serializer_class = QuestionSerializer

    def get_queryset(self):
        slug = self.kwargs['slug']
        category = get_object_or_404(Categories, slug=slug)
        return Question.objects.filter(category=category)


class CategoryListView(generics.ListAPIView):
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
