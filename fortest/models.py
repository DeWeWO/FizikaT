from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField

ANSWER_CHOICES = [
    ('a', 'A'),
    ('b', 'B'),
    ('c', 'C'),
    ('d', 'D'),
]

class Question(models.Model):
    question_text = RichTextUploadingField("Savol")
    option_a = RichTextUploadingField("Variant A")
    option_b = RichTextUploadingField("Variant B")
    option_c = RichTextUploadingField("Variant C")
    option_d = RichTextUploadingField("Variant D")
    correct_answer = models.CharField("To'g'ri javob", choices=ANSWER_CHOICES, max_length=1)

    def __str__(self):
        return self.question_text[:60]
