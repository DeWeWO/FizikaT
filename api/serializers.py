from rest_framework import serializers
from fortest.models import Question, Categories, Register, TestResult

class CategorySerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categories
        fields = ['id', 'title', 'slug', 'description', 'questions_count', 'created', 'updated']
    
    def get_questions_count(self, obj):
        return obj.questions.count()

class QuestionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.title', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'category', 'category_name', 'created', 'updated'
        ]

# Telegram bot uchun soddalashtirilgan serializer
class QuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Register
        fields = ['id', 'fio', 'telegram_id']

# Test natijasi uchun serializer
class TestResultSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    telegram_id = serializers.IntegerField()
    answers = serializers.DictField(child=serializers.CharField())
    
    def validate_answers(self, value):
        # Javoblar to'g'ri formatda ekanligini tekshirish
        for question_id, answer in value.items():
            if answer not in ['a', 'b', 'c', 'd']:
                raise serializers.ValidationError(f"Javob '{answer}' noto'g'ri format")
        return value


class TestResultModelSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(source='category.title', read_only=True)
    
    class Meta:
        model = TestResult
        fields = ['id', 'telegram_id', 'category', 'category_title', 'total_questions', 
                 'correct_answers', 'wrong_answers', 'percentage', 'completed_at']
        read_only_fields = ['id', 'completed_at']
