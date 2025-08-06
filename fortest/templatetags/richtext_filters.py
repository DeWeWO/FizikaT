from django import template
import re
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

@register.filter
def render_richtext(content):
    if not content:
        return ""

    # LaTeX formulalarni ajratib olamiz (ularni vaqtincha o'zgartirmaslik uchun)
    latex_blocks = []

    def store_latex(m):
        latex_blocks.append(m.group(0))
        return f"__LATEX_{len(latex_blocks)-1}__"

    content = re.sub(r'\\\[(.*?)\\\]', store_latex, content, flags=re.DOTALL)
    content = re.sub(r'\\\((.*?)\\\)', store_latex, content, flags=re.DOTALL)

    # HTML teglarni tozalaymiz
    content = re.sub(r'<[^>]+>', '', content)

    # HTML entitilarni oddiy belgiga aylantiramiz
    content = content.replace('&nbsp;', ' ')

    # Yangi qatordan <br> qilish (ixtiyoriy)
    content = content.replace('\n', '<br>')

    # LaTeX formulalarni joyiga qaytaramiz
    for i, block in enumerate(latex_blocks):
        content = content.replace(f"__LATEX_{i}__", block)

    return mark_safe(content)
