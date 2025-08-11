import json
import asyncio
import logging
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from fortest.models import Categories, Question, Register, TestResult
from .serializers import (
    CategorySerializer, QuestionSerializer,
    RegisterSerializer, TestResultSerializer, TestResultModelSerializer
)


class CustomUsersListView(View):
    def get(self, request):
        try:
            users = CustomUser.objects.all().values(
                'id', 'username', 'first_name', 'last_name', 
                'telegram_id', 'telegram_username', 'is_staff', 
                'is_active', 'created_via_telegram', 'date_joined'
            )
            return JsonResponse({
                'success': True,
                'results': list(users),
                'count': users.count()
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

# views.py ga qo'shing
@method_decorator(csrf_exempt, name='dispatch')
class RegisterUsersListView(View):
    """Register jadvalidagi barcha foydalanuvchilarni olish"""
    
    def get(self, request):
        try:
            
            register_users = Register.objects.all().values(
                'id', 'fio', 'telegram_id'
            )
            
            return JsonResponse({
                'success': True,
                'results': list(register_users),
                'count': register_users.count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


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
            
            return JsonResponse({
                'success': True,
                'message': 'Admin muvaffaqiyatli yaratildi!',
                'data': {
                    'user_created': user_created,
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

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramAdminRegisterView(View):
    """Telegram orqali admin ro'yxatdan o'tkazish"""
    
    def post(self, request):
        # So'rov haqida to'liq ma'lumot
        logger.info("=== YANGI SO'ROV ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Content-Type: {request.META.get('CONTENT_TYPE', 'N/A')}")
        logger.info(f"Request body (raw): {request.body}")
        
        try:
            # 1. JSON ni parse qilish
            try:
                data = json.loads(request.body)
                logger.info(f"Parsed JSON data: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode xatoligi: {e}")
                return JsonResponse({
                    'success': False,
                    'message': 'Yaroqsiz JSON format!'
                }, status=400)
            
            # 2. Zaruriy fieldlarni tekshirish
            required_fields = ['telegram_id', 'first_name', 'last_name', 'username', 'password']
            missing_fields = []
            
            for field in required_fields:
                value = data.get(field)
                logger.info(f"Field '{field}': {value} (type: {type(value)})")
                
                if not value:  # None, empty string, 0, False
                    missing_fields.append(field)
                    
                # String bo'lishi kerak bo'lgan fieldlar uchun
                if field in ['first_name', 'last_name', 'username', 'password']:
                    if not isinstance(value, str) or not value.strip():
                        missing_fields.append(f"{field} (bo'sh string)")
                        
                # telegram_id integer bo'lishi kerak
                if field == 'telegram_id':
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        missing_fields.append(f"{field} (integer emas)")
            
            if missing_fields:
                error_msg = f"Quyidagi maydonlar noto'g'ri: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                }, status=400)
            
            # 3. Ma'lumotlarni tozalash va tayyorlash
            try:
                cleaned_data = {
                    'telegram_id': int(data['telegram_id']),
                    'first_name': str(data['first_name']).strip(),
                    'last_name': str(data['last_name']).strip(), 
                    'username': str(data['username']).strip().lower(),
                    'password': str(data['password']),
                    'telegram_username': data.get('telegram_username', ''),
                    'is_staff': data.get('is_staff', True),
                    'is_superuser': data.get('is_superuser', False)
                }
                logger.info(f"Tozalangan ma'lumotlar: {cleaned_data}")
                
            except (ValueError, TypeError) as e:
                logger.error(f"Ma'lumot tozalashda xatolik: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'Ma\'lumot formati noto\'g\'ri: {str(e)}'
                }, status=400)
            
            # 4. Mavjudligini tekshirish
            logger.info("Mavjudlik tekshiruvi...")
            
            # Telegram ID tekshirish
            existing_telegram = CustomUser.objects.filter(telegram_id=cleaned_data['telegram_id']).first()
            if existing_telegram:
                logger.warning(f"Telegram ID {cleaned_data['telegram_id']} allaqachon mavjud (User ID: {existing_telegram.id})")
                return JsonResponse({
                    'success': False,
                    'message': f'Bu Telegram ID allaqachon ro\'yxatdan o\'tgan! (User: {existing_telegram.username})'
                }, status=400)
            
            # Username tekshirish
            existing_username = CustomUser.objects.filter(username=cleaned_data['username']).first()
            if existing_username:
                logger.warning(f"Username '{cleaned_data['username']}' allaqachon mavjud (User ID: {existing_username.id})")
                return JsonResponse({
                    'success': False,
                    'message': f'Bu username allaqachon mavjud! (User ID: {existing_username.id})'
                }, status=400)
            
            # 5. Yangi admin user yaratish
            logger.info("Yangi user yaratish...")
            try:
                user = CustomUser.objects.create(
                    username=cleaned_data['username'],
                    first_name=cleaned_data['first_name'],
                    last_name=cleaned_data['last_name'],
                    password=make_password(cleaned_data['password']),
                    telegram_id=cleaned_data['telegram_id'],
                    telegram_username=cleaned_data['telegram_username'],
                    created_via_telegram=True,
                    is_staff=cleaned_data['is_staff'],
                    is_active=True,
                    is_superuser=cleaned_data['is_superuser'],
                    email=f"{cleaned_data['username']}@telegram.local"
                )
                
                logger.info(f"User muvaffaqiyatli yaratildi: ID={user.id}, username={user.username}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Admin muvaffaqiyatli yaratildi!',
                    'user_id': user.id,
                    'username': user.username
                })
                
            except ValidationError as e:
                logger.error(f"Validation xatoligi: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'Ma\'lumot validatsiya xatoligi: {str(e)}'
                }, status=400)
                
            except Exception as e:
                logger.error(f"User yaratishda xatolik: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'User yaratishda xatolik: {str(e)}'
                }, status=500)
            
        except Exception as e:
            logger.error(f"Kutilmagan xatolik: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Server xatoligi: {str(e)}'
            }, status=500)
    
    def get(self, request):
        """GET so'rov uchun test method"""
        logger.info("GET so'rov keldi")
        return JsonResponse({
            'message': 'Telegram Admin Register API ishlayapti',
            'method': 'POST kerak',
            'endpoint': '/api/telegram-admin-register/'
        })