import datetime

from django.template import Library
from django.utils.safestring import mark_safe


register = Library()



@register.simple_tag
def copyright_years(start_year):
    """
    Prints start_year - current_year if they differ, otherwise only start_year.
    """
    try:
        start_year = int(start_year)
    except TypeError:
        raise Exception('copyright_years should take integer argument')
    current_year = datetime.date.today().year

    if current_year == start_year:
        return start_year
    elif current_year > start_year:
        return mark_safe('%d&ndash;%d' % (start_year, current_year))
    return mark_safe('%d&ndash;%d' % (current_year, start_year))

