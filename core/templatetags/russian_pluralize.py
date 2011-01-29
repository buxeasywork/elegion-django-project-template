# -*- coding: UTF-8 -*-
from django.template import Library
from django.template.defaultfilters import stringfilter


register = Library()


@register.filter(name='russian_pluralize')
@stringfilter
def russian_pluralize(value, forms):
    """
    ATTENTION: Use get_text instead.

    Simple pluralizer for russian language

    value is count
    forms is space separated form1, form2 and form5
    """
    forms = forms.split()
    form1 = forms[0]
    form2 = forms[1]
    form5 = forms[2]
    n = int(value)

    n = abs(n) % 100;
    n1 = n % 10;

    if (n > 10 and n < 20):
       return form5
    if (n1 > 1 and n1 < 5):
       return form2
    if (n1 == 1):
       return form1
    return form5

