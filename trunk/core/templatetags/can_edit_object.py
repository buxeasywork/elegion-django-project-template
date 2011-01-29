from django import template


register = template.Library()
class CanEditNode(template.Node):
    def __init__(self, user, note, asvar):
        self.note = note
        self.user = user
        self.asvar = asvar

    def render(self, context):
        self.note = self.note.resolve(context)
        self.user = self.user.resolve(context)
        context[self.asvar] = self.note.can_edit(self.user)
        return ''


@register.tag
def can_edit(parser, token):
    """
    Tag used to all object, whitch have can_edit property with params user
    Result save in asvar

    Ex. use: {% can_edit user offer as can_admin %}
    """
    bits = token.split_contents()
    if len(bits) != 5 or bits[3] != 'as':
        raise template.TemplateSyntaxError("'%s' takes exactly three arguments:"
                                           " \%user \%note as \%varname" % bits[0])
    user = parser.compile_filter(bits[1])
    note = parser.compile_filter(bits[2])
    asvar = bits[4]
    return CanEditNode(user, note, asvar)

