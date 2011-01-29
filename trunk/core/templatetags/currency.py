# encoding: utf-8
from django import template
from django.utils.translation import ugettext as _


register = template.Library()


@register.simple_tag
def rur():
    return _(u'<span class="rur">p<s>уб.</s></span>')


@register.filter
def for_ounce(price):
    return int(round(28.3495231 / 50 * float(price)))

