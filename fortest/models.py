from django.db import models
from django.template.defaultfilters import slugify
from ckeditor.fields import RichTextField

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
        