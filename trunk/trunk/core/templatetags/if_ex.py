from django.template import Node, NodeList, Library, TemplateSyntaxError


register = Library()


class IfStartsWithNode(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false):
        self.var1 = var1
        self.var2 = var2
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def __repr__(self):
        return '<IfStartsWithNode>'

    def render(self, context):
        val1 = self.var1.resolve(context, True)
        val2 = self.var2.resolve(context, True)
        if val1.startswith(val2):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


@register.tag('ifstartswith')
def do_ifstartswith(parser, token):
    """
    Outputs the contents of the block if the two arguments equal each other.

    Examples::

        {% ifstartswith haystack needle %}
            ...
        {% endifstartswith %}

        {% ifstartswith haystack needle %}
            ...
        {% else %}
            ...
        {% endifstartswith %}
    """
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    val1 = parser.compile_filter(bits[1])
    val2 = parser.compile_filter(bits[2])
    return IfStartsWithNode(val1, val2, nodelist_true, nodelist_false)

