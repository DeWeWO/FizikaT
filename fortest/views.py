from django.shortcuts import render, redirect, get_object_or_404
from .models import Question, Categories, TestResult

def category_questions(request, slug):
    category = get_object_or_404(Categories, slug=slug)
    print("salom", slug)
    questions = category.questions.all()
    # telegram_id = request.GET.get('telegram_id')
    print(request)
    print(slug)
    # print(telegram_id)
    return render(request, 'fortest/test.html', {'category': category, 'questions': questions})

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
        
        from decimal import Decimal, ROUND_HALF_UP
        percentage = Decimal(correct * 100) / Decimal(total)
        percentage = percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
        TestResult.objects.create(
            telegram_id=123456789,
            category=category,
            total_questions=total,
            correct_answers=correct,
            wrong_answers=total - correct,
            percentage=percentage
        )

        return render(request, 'fortest/result.html', {
            'total': total,
            'correct': correct,
            'wrong': total - correct,
            'category': category,
        })
    # POST bo'lmagan holatda foydalanuvchini test sahifasiga qaytarish mumkin
    return redirect('category_questions', slug=slug)
