from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.db import IntegrityError
from fortest.models import Categories, Question, User, Register
from .serializers import (
    CategorySerializer, QuestionSerializer, QuestionListSerializer,
    UserSerializer, RegisterSerializer, TestResultSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def questions(self, request, slug=None):
        """Kategoriya bo'yicha savollarni HTML sifatida olish"""
        category = self.get_object()
        questions = category.questions.all()
        
        return render(request, 'fortest/test.html', {
            'category': category, 
            'questions': questions
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
            
            return render(request, 'fortest/result.html', {
                'total': total_count,
                'correct': correct_count,
                'wrong': total_count - correct_count,
                'category': category,
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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