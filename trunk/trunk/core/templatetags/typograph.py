# -*- coding: UTF-8 -*-
from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

from core.typographus import Typographus


register = Library()


@register.filter(name='typograph')
@stringfilter
def typograph(value):
    """
      Typography the text fro html and mark safe
    """
    return mark_safe(Typographus().process(value))

