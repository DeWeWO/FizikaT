from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import slugify
from ckeditor.fields import RichTextField
from django.utils import timezone


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Categories(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs) -> None:
        self.slug = slugify(self.title)
        return super().save( *args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Categories"
        db_table = 'categories'

class Question(BaseModel):
    question_text = RichTextField(verbose_name="📝 Savol matni (LaTeX, rasm, matn)")
    option_a = RichTextField(verbose_name="A varianti")
    option_b = RichTextField(verbose_name="B varianti")
    option_c = RichTextField(verbose_name="C varianti")
    option_d = RichTextField(verbose_name="D varianti")

    CORRECT_OPTION_CHOICES = [
        ('a', "A"),
        ('b', "B"),
        ('c', "C"),
        ('d', "D"),
    ]
    
    category = models.ForeignKey(to=Categories, on_delete=models.CASCADE, related_name="questions")
    correct_option = models.CharField(max_length=1, choices=CORRECT_OPTION_CHOICES, verbose_name="To'g'ri javob")

    def __str__(self):
        return f"Savol: {self.question_text[:30]}"

    class Meta:
        ordering = ['-id']
        db_table = 'questions'


class Register(models.Model):
    fio = models.CharField(max_length=255)
    telegram_id = models.BigIntegerField(unique=True)

    def __str__(self):
        return self.fio
    
    class Meta:
        db_table = 'register'

class TestResult(models.Model):
    telegram_id = models.BigIntegerField()
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    wrong_answers = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'test_results'
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"User {self.telegram_id} - {self.category.title} - {self.percentage}%"

class CustomUser(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    created_via_telegram = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (@{self.telegram_username or self.username})"

class TelegramGroup(models.Model):
    group_id = models.BigIntegerField(unique=True, db_index=True)
    group_name = models.CharField(max_length=255)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'telegram_groups'
        verbose_name = 'Telegram Group'
        verbose_name_plural = 'Telegram Groups'

    def __str__(self):
        return f"{self.group_name} ({self.group_id})"