from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Question


def hello(request):
    return HttpResponse('Hello World!')

def test_view(request):
    questions = Question.objects.all()
    return render(request, 'fortest/test.html', {'questions': questions})

def submit_test(request):
    if request.method == 'POST':
        questions = Question.objects.all()
        correct = 0
        total = questions.count()

        for question in questions:
            selected = request.POST.get(f'q{question.id}')
            if selected == question.correct_option:
                correct += 1

        return render(request, 'fortest/result.html', {
            'total': total,
            'correct': correct,
            'wrong': total - correct,
        })