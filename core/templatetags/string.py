from django.template.defaultfilters import stringfilter
from django.template import Library


register = Library()


@register.filter
@stringfilter
def ljust_ex(value, args):
    """
    Left-aligns the value in a field of a given width.

    Argument: field size<space>fill char
    """
    args = args.split(' ')
    if len(args) > 1:
        fillchar = args[1]
    else:
        fillchar = ' '
    return value.ljust(int(args[0]), fillchar)
ljust_ex.is_safe = True

