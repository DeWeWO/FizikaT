from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.db import IntegrityError
from django.db.models import Avg
import asyncio
import aiohttp
from fortest.models import Categories, Question, User, Register, TestResult
from .serializers import (
    CategorySerializer, QuestionSerializer, QuestionListSerializer,
    UserSerializer, RegisterSerializer, TestResultSerializer, TestResultModelSerializer
)
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")  # Bu yerga bot tokeningizni qo'ying
BOT_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def questions(self, request, slug=None):
        """Kategoriya bo'yicha savollarni HTML sifatida olish"""
        category = self.get_object()
        questions = category.questions.all()
        telegram_id = request.GET.get('telegram_id')
        
        return render(request, 'fortest/test.html', {
            'category': category,
            'questions': questions,
            'telegram_id': telegram_id
        })

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        queryset = Question.objects.all()
        category_slug = self.request.query_params.get('category', None)
        if category_slug is not None:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset
    
    @action(detail=False, methods=['post'])
    def check_answers(self, request):
        """Javoblarni tekshirish va HTML natijani qaytarish"""
        serializer = TestResultSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            category_id = data['category_id']
            telegram_id = data['telegram_id']
            answers = data['answers']
            
            try:
                category = Categories.objects.get(id=category_id)
            except Categories.DoesNotExist:
                return Response(
                    {'error': 'Kategoriya topilmadi'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            questions = Question.objects.filter(category_id=category_id)
            
            correct_count = 0
            total_count = questions.count()
            
            for question in questions:
                question_id = str(question.id)
                user_answer = answers.get(question_id, '')
                is_correct = user_answer == question.correct_option
                
                if is_correct:
                    correct_count += 1
            
            # Natijani bazaga saqlash
            test_result = TestResult.objects.create(
                telegram_id=telegram_id,
                category=category,
                total_questions=total_count,
                correct_answers=correct_count,
                wrong_answers=total_count - correct_count,
                percentage=round((correct_count / total_count) * 100, 2) if total_count > 0 else 0
            )
            
            # Telegram orqali xabar yuborish
            asyncio.create_task(self.send_telegram_notification(
                telegram_id, category.title, correct_count, total_count, test_result.percentage
            ))
            
            return render(request, 'fortest/result.html', {
                'total': total_count,
                'correct': correct_count,
                'wrong': total_count - correct_count,
                'category': category,
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    async def send_telegram_notification(self, telegram_id, category_title, correct, total, percentage):
        """Foydalanuvchiga telegram orqali natijani yuborish"""
        message = f"""
📊 Test natijalari:

🎯 Kategoriya: {category_title}
✅ To'g'ri javoblar: {correct}/{total}
❌ Noto'g'ri javoblar: {total - correct}
📈 Foiz: {percentage}%

🎉 Tabriklaymiz!
        """
        
        payload = {
            'chat_id': telegram_id,
            'text': message.strip(),
            'parse_mode': 'HTML'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BOT_API_URL, json=payload) as resp:
                    if resp.status == 200:
                        print(f"Telegram xabar yuborildi: {telegram_id}")
                    else:
                        print(f"Telegram xabar yuborishda xatolik: {resp.status}")
        except Exception as e:
            print(f"Telegram API xatolik: {e}")

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'telegram_id'
    
    @action(detail=False, methods=['post'])
    def get_or_create_user(self, request):
        """Foydalanuvchini olish yoki yaratish"""
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response(
                {'error': 'telegram_id majburiy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'first_name': request.data.get('first_name', ''),
                    'last_name': request.data.get('last_name', ''),
                    'username': request.data.get('username', ''),
                }
            )
            
            if not created:
                user.first_name = request.data.get('first_name', user.first_name)
                user.last_name = request.data.get('last_name', user.last_name)
                user.username = request.data.get('username', user.username)
                user.save()
            
            return Response({
                'user': UserSerializer(user).data,
                'created': created
            })
            
        except IntegrityError:
            return Response(
                {'error': 'Ma\'lumotlar bazasida xatolik'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RegisterViewSet(viewsets.ModelViewSet):
    queryset = Register.objects.all()
    serializer_class = RegisterSerializer
    lookup_field = 'telegram_id'
    
    @action(detail=False, methods=['post'])
    def register_user(self, request):
        """Foydalanuvchini ro'yxatga olish"""
        telegram_id = request.data.get('telegram_id')
        fio = request.data.get('fio')
        
        if not telegram_id or not fio:
            return Response(
                {'error': 'telegram_id va fio majburiy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            register, created = Register.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={'fio': fio}
            )
            
            if not created:
                register.fio = fio
                register.save()
            
            return Response({
                'register': RegisterSerializer(register).data,
                'created': created,
                'message': 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!' if created else 'Ma\'lumotlaringiz yangilandi!'
            })
            
        except IntegrityError:
            return Response(
                {'error': 'Bu telegram_id avval ro\'yxatdan o\'tgan'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def check_registration(self, request):
        """Foydalanuvchi ro'yxatdan o'tganligini tekshirish"""
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            return Response(
                {'error': 'telegram_id majburiy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            register = Register.objects.get(telegram_id=telegram_id)
            return Response({
                'registered': True,
                'fio': register.fio
            })
        except Register.DoesNotExist:
            return Response({
                'registered': False
            })


# views.py ga qo'shish kerak

class TestResultViewSet(viewsets.ModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultModelSerializer
    
    def get_queryset(self):
        queryset = TestResult.objects.all()
        telegram_id = self.request.query_params.get('telegram_id', None)
        category_id = self.request.query_params.get('category_id', None)
        
        if telegram_id is not None:
            queryset = queryset.filter(telegram_id=telegram_id)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def user_stats(self, request):
        """Foydalanuvchi statistikasi"""
        telegram_id = request.query_params.get('telegram_id')
        if not telegram_id:
            return Response(
                {'error': 'telegram_id majburiy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = TestResult.objects.filter(telegram_id=telegram_id)
        total_tests = results.count()
        
        if total_tests == 0:
            return Response({'message': 'Hech qanday test natijalari topilmadi'})
        
        from django.db.models import Avg
        avg_percentage = results.aggregate(
            avg_percentage=Avg('percentage')
        )['avg_percentage']
        
        return Response({
            'telegram_id': telegram_id,
            'total_tests': total_tests,
            'average_percentage': round(avg_percentage, 2) if avg_percentage else 0,
            'results': TestResultModelSerializer(results, many=True).data
        })