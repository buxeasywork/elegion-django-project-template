from django.template import Library
from django.utils.safestring import mark_safe

register = Library()


@register.filter(name='sign')
def add_sign_and_class(value, add_sign=False):
    """
    Wraps a number with a <span class="positive|zero|negative">%d</span>.
    And optionaly prints a positive sign (+) in front of value.
    """
    n = int(value)
    class_name = 'negative'
    sign = ''
    if n == 0:
        class_name = 'zero'
    elif n > 0:
        class_name = 'positive'
        if add_sign:
            sign = '+'
    return mark_safe('<span class="%s">%s%d</span>' % (class_name, sign, n))

@register.filter(name='multiply')
def multiply(value, multiplier=1):
    """
    Return value*multiplier
    """
    return int(value)*int(multiplier)

