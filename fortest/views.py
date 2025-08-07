from django.shortcuts import render, redirect, get_object_or_404
from .models import Question, Categories

def category_questions(request, category_id):
    category = get_object_or_404(Categories, id=category_id)
    questions = category.questions.all()
    return render(request, 'fortest/test.html', {'category': category, 'questions': questions})

# def test_view(request):
#     questions = Question.objects.all()
#     return render(request, 'fortest/test.html', {'questions': questions})

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