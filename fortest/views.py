from django.shortcuts import render, redirect, get_object_or_404
from .models import Categories, TestResult, Register

def category_questions(request, slug):
    category = get_object_or_404(Categories, slug=slug)
    print("salom", slug)
    questions = category.questions.all()
    print(request)
    print(slug)
    return render(request, 'fortest/test.html', {'category': category, 'questions': questions})

def submit_test(request, slug):
    if request.method == 'POST':
        category = get_object_or_404(Categories, slug=slug)
        questions = category.questions.all()

        correct = 0
        total = questions.count()

        for question in questions:
            selected = request.POST.get(f'q{question.id}')
            if selected == question.correct_option:
                correct += 1
        
        telegram_id = request.GET.get('telegram_id')
        user = get_object_or_404(Register, telegram_id=telegram_id)
                
        TestResult.objects.create(
            user=user,
            category=category,
            total_questions=total,
            correct_answers=correct
        )

        return render(request, 'fortest/result.html', {
            'total': total,
            'correct': correct,
            'category': category,
            'fio': user.fio,
        })
    return redirect('category_questions', slug=slug)
