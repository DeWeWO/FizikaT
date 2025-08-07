import re
from django import template

register = template.Library()

LATEX_PATTERN = re.compile(r"^[\s\S]*?\\[a-zA-Z]+[\s\S]*?$")

@register.filter
def auto_mathjax_only_if_latex(value):
    """
    Faqat LaTeX kodi bor bo‘lsa, MathJax uchun <span> bilan o‘raydi.
    Oddiy matnga teginmaydi.
    """
    if value and LATEX_PATTERN.search(value):
        return f"<span class='mathjax-latex'>\\({value}\\)</span>"
    return value
