from django.shortcuts import render, redirect, get_object_or_404
from .models import Question, Categories

def category_questions(request, slug):
    category = get_object_or_404(Categories, slug=slug)
    questions = category.questions.all()
    return render(request, 'fortest/test.html', {'category': category, 'questions': questions})

# def test_view(request):
#     questions = Question.objects.all()
#     return render(request, 'fortest/test.html', {'questions': questions})

from django.shortcuts import get_object_or_404

def submit_test(request, slug):
    if request.method == 'POST':
        category = get_object_or_404(Categories, slug=slug)
        questions = category.questions.all()  # faqat shu kategoriyaga tegishli savollar

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
            'category': category,
        })
    # POST bo'lmagan holatda foydalanuvchini test sahifasiga qaytarish mumkin
    return redirect('category_questions', slug=slug)
