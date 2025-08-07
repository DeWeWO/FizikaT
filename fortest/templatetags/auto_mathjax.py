from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def auto_mathjax(text):
    """
    Matn ichida toza LaTeX formulalarni aniqlab, ularni MathJax formatiga o'raydi: \(...\)
    Faqat formulalargagina tegadi, qolgan matnga tegmaydi.
    """
    # Faqat LaTeX formulalarga mos keladigan patternlar (asosiylari)
    pattern = re.compile(r'(\\(?:frac|sqrt|int|sum|log|lim|vec|overline|underline|begin|end|alpha|beta|gamma|delta|pi|theta|cdot|pm|times|div|leq|geq|neq|approx|infty|dots)[^ \n<]*)', re.IGNORECASE)

    def replacer(match):
        formula = match.group(0)
        return f'\\({formula}\\)'

    # Formulani \(...\) bilan o'rab chiqamiz
    result = re.sub(pattern, replacer, text)
    return mark_safe(result)
