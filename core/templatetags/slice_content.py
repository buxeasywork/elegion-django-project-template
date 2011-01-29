from django.template.defaultfilters import stringfilter
from django.template import Library
from django.utils.html import escape


register = Library()


@register.filter(name='wrapcontent')
@stringfilter
def wrap_contentplain(value, arg):
    """
    "Boxing text"
    
    Split text on lines by <br /> when letters per line count reached
    and reject lines after max lines count reached.
    
    Args: 0 = max lines count, 1 = letters per line.
    
    ATTENTION. Not html-friendly. Escapes html.
    """
    args = arg.split(u' ')
    try:
        lines_count = int(args[0])
        letter_in_line = int(args[1])
    except ValueError:
        return value

    value = escape(value)
    words = (value.replace('<br />',' ')).split()

    result = ''
    current_lines_count = 0
    current_string = ''
    for word in words:
        if len(word) == 0:
            continue
        if len(current_string) + len(word) + 1 > letter_in_line:
            if len(result) > 0:
                result += '<br />'
            result += current_string
            current_string = word
            current_lines_count += 1
        else:
            current_string += ' ' + word

        if current_lines_count == lines_count:
            result += '...'
            break

    if current_lines_count < lines_count:
        result += ' ' + current_string

    return result

wrap_contentplain.is_safe = True


@register.filter(name='urlwrap')
def url_wrap(value, arg):
    args = arg.split(u' ')
    try:
        str_length = int(args[0])
    except ValueError:
        return str
    str = value.replace('http://','')
    if str.endswith('/'):
        str = str[:len(str)-1]
    if len(str) > str_length:
        str = str[:str_length-4] + '...' # 3 for ...
    return str

