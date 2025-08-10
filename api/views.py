import json
import secrets
import asyncio
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.db import IntegrityError, transaction
from fortest.models import Categories, Question, TelegramUser, Register, TestResult, Admin
from .serializers import (
    CategorySerializer, QuestionSerializer, UserSerializer,
    RegisterSerializer, TestResultSerializer, TestResultModelSerializer
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect
from fortest.models import TelegramSession
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from datetime import datetime, timedelta



@csrf_exempt
@require_http_methods(["POST"])
def simple_test_register(request):
    """Test uchun admin yaratish"""
    try:
        # Request ma'lumotlarini olish
        data = json.loads(request.body)
        print(f"Received data: {data}")  # Debug
        
        telegram_id = data.get('telegram_id')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        username = data.get('username')
        
        if not all([telegram_id, first_name, last_name]):
            return JsonResponse({
                'success': False,
                'message': 'Telegram ID, ism va familiya majburiy'
            })
        
        # Database ga yozish
        with transaction.atomic():
            # User yaratish yoki yangilash
            user, user_created = CustomUser.objects.update_or_create(
                telegram_id=telegram_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': username
                }
            )
            print(f"User created: {user_created}, User: {user}")  # Debug
            
            # Admin profil yaratish
            admin_profile, admin_created = Admin.objects.get_or_create(
                user=user,
                defaults={
                    'is_active': True,
                    'is_superuser': False,
                    'created_via_telegram': True
                }
            )
            print(f"Admin created: {admin_created}, Admin: {admin_profile}")  # Debug
            
            return JsonResponse({
                'success': True,
                'message': 'Admin muvaffaqiyatli yaratildi!',
                'data': {
                    'user_created': user_created,
                    'admin_created': admin_created,
                    'telegram_id': telegram_id,
                    'name': f"{first_name} {last_name}"
                }
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON format xato'
        })
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug
        return JsonResponse({
            'success': False,
            'message': f'Xatolik: {str(e)}'
        })
        
@csrf_exempt
@require_http_methods(["GET"])
def check_admin_simple(request, telegram_id):
    """Oddiy admin tekshirish funksiyasi"""
    try:
        user = CustomUser.objects.get(telegram_id=telegram_id)
        
        # Admin profil borligini tekshirish
        has_admin = hasattr(user, 'admin_profile')
        is_active = has_admin and user.admin_profile.is_active if has_admin else False
        
        return JsonResponse({
            'success': True,
            'is_admin': is_active,
            'user_exists': True,
            'has_admin_profile': has_admin,
            'message': 'Admin' if is_active else 'Oddiy foydalanuvchi'
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'success': True,
            'is_admin': False,
            'user_exists': False,
            'message': 'Foydalanuvchi topilmadi'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

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


class UserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
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
            user, created = CustomUser.objects.get_or_create(
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


CustomUser = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class CheckTelegramAdminView(View):
    """Telegram ID orqali admin ekanligini tekshirish"""
    
    def get(self, request, telegram_id):
        try:
            user = CustomUser.objects.get(
                telegram_id=telegram_id,
                is_staff=True,
                is_active=True
            )
            return JsonResponse({
                'success': True,
                'is_admin': True,
                'username': user.username,
                'is_superuser': user.is_superuser
            })
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': True,
                'is_admin': False
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CheckUsernameAvailabilityView(View):
    """Username mavjudligini tekshirish"""
    
    def get(self, request, username):
        try:
            exists = CustomUser.objects.filter(username=username).exists()
            return JsonResponse({
                'success': True,
                'available': not exists,
                'username': username
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramAdminRegisterView(View):
    """Telegram orqali admin ro'yxatdan o'tkazish"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Zaruriy fieldlarni tekshirish
            required_fields = ['telegram_id', 'first_name', 'last_name', 'username', 'password']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'message': f'{field} maydoni bo\'sh bo\'lishi mumkin emas!'
                    }, status=400)
            
            # Mavjudligini tekshirish
            if CustomUser.objects.filter(telegram_id=data['telegram_id']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Bu Telegram ID allaqachon ro\'yxatdan o\'tgan!'
                }, status=400)
            
            if CustomUser.objects.filter(username=data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Bu username allaqachon mavjud!'
                }, status=400)
            
            # Yangi admin user yaratish
            user = CustomUser.objects.create(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=make_password(data['password']),
                telegram_id=data['telegram_id'],
                telegram_username=data.get('telegram_username'),
                created_via_telegram=True,
                is_staff=data.get('is_staff', True),
                is_active=True,
                is_superuser=data.get('is_superuser', False),
                email=f"{data['username']}@telegram.local"
            )
            
            # Telegram session yaratish
            session_token = secrets.token_urlsafe(32)
            TelegramSession.objects.create(
                user=user,
                session_token=session_token
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Admin muvaffaqiyatli yaratildi!',
                'user_id': user.id,
                'username': user.username
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Yaroqsiz JSON format!'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Server xatoligi: {str(e)}'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GetAdminTokenView(View):
    """Admin uchun session token olish"""
    
    def get(self, request, telegram_id):
        try:
            user = CustomUser.objects.get(
                telegram_id=telegram_id,
                is_staff=True,
                is_active=True
            )
            
            # Eski tokenni o'chirish yoki yangilash
            session, created = TelegramSession.objects.get_or_create(
                user=user,
                defaults={'session_token': secrets.token_urlsafe(32)}
            )
            
            if not created:
                # Eski token ni yangilash
                session.session_token = secrets.token_urlsafe(32)
                session.save()
            
            return JsonResponse({
                'success': True,
                'session_token': session.session_token,
                'username': user.username,
                'is_superuser': user.is_superuser,
                'expires_in': '10 minutes'
            })
            
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Admin topilmadi yoki huquqlar yo\'q!'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramLoginView(View):
    """Token orqali Django admin panelga kirish"""
    
    def get(self, request, token):
        try:
            # Token validatsiyasi
            session = TelegramSession.objects.select_related('user').get(
                session_token=token
            )
            
            # Token vaqti tekshirish (10 daqiqa)
            if session.created_at < timezone.now() - timedelta(minutes=10):
                session.delete()
                return JsonResponse({
                    'success': False,
                    'message': 'Token vaqti tugagan!'
                }, status=400)
            
            user = session.user
            
            # User faol va admin ekanligini tekshirish
            if not (user.is_active and user.is_staff):
                return JsonResponse({
                    'success': False,
                    'message': 'Foydalanuvchi faol emas yoki admin huquqlari yo\'q!'
                }, status=403)
            
            # Django session yaratish
            from django.contrib.auth import login
            
            # Backend bilan login qilish
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Tokenni o'chirish (bir marta ishlatish uchun)
            session.delete()
            
            # Admin panelga yo'naltirish
            from django.shortcuts import redirect
            return redirect('/admin/')
            
        except TelegramSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Yaroqsiz yoki eskirgan token!'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Kirish xatoligi: {str(e)}'
            }, status=500)
