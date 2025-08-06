from django.contrib import admin
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Question

class QuestionAdminForm(forms.ModelForm):
    question_text = forms.CharField(label="📝 Savol matni (LaTeX, rasm, matn)", widget=CKEditorUploadingWidget())
    option_a = forms.CharField(label="A Variant", widget=CKEditorUploadingWidget())
    option_b = forms.CharField(label="B Variant", widget=CKEditorUploadingWidget())
    option_c = forms.CharField(label="C Variant", widget=CKEditorUploadingWidget())
    option_d = forms.CharField(label="D Variant", widget=CKEditorUploadingWidget())

    class Meta:
        model = Question
        fields = '__all__'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    list_display = ['id', 'short_question', 'correct_answer']

    def short_question(self, obj):
        return obj.question_text[:50]
