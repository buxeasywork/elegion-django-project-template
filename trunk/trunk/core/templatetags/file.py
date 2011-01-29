# -*- coding: UTF-8 -*-
import os

from django.template import Library
from django.template.defaultfilters import stringfilter


register = Library()

@register.filter(name='file_basename')
@stringfilter
def file_basename(value):
    """
    Returns filename component of path

    """
    return os.path.basename(value)
