from django.db import models
from ckeditor.fields import RichTextField

class Question(models.Model):
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
    correct_option = models.CharField(max_length=1, choices=CORRECT_OPTION_CHOICES, verbose_name="To'g'ri javob")

    def __str__(self):
        return f"Savol: {self.question_text[:30]}"
