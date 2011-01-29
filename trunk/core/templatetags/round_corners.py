from django import template

register = template.Library()


def simple_corner():
    return """
        <div class="%s">
            <div class="tl"></div><div class="tr"></div>
            %s
            <div class="bl"></div><div class="br"></div>
        </div>
    """

def shadow_corner():
    return """
            <div class="%s">
                <div class="top">
                    <div class="c"></div>
                </div>
                <div class="centre">
                    <div class="c">
                        <div class="content">
                        %s
                        </div>
                    </div>
                </div>
                <div class="bottom">
                    <div class="c"></div>
                </div>
            </div>
        """

def delete_qoute(string):
    if string and string[0] == string[-1] and string[0] in ('"', "'"):
        return string[1:-1]
    return string

class RoundCornerNode(template.Node):
    def __init__(self, nodelist, bordertype=None, classname=None):
        self.nodelist = nodelist
        self.bordertype = bordertype
        self.classname = classname or ""
    def render(self, context):
        block = self.nodelist.render(context)
        if self.bordertype == "simple":
            return simple_corner() % (self.classname, block)
        elif self.bordertype == "shadow":
            return shadow_corner() % (self.classname, block)
        return block

@register.tag(name="roundcorner")
def do_roundcorner(parser, token):
    """
    This block tag wrap content by rounded corners. For this, tag wrap content by div.
    Tag support 2 type of corner:
        1) "simple" - 4 round corner
        2) "shadow" - round corner along the perimeter of block
    Syntax:
    {% roundcorner "TYPE" %}
    {% endroundcorner %}
    OR
    {% roundcorner "TYPE" withclass "CLASSNAME" %}
    {% endroundcorner %}
    Where TYPE is "simple" or "shadow"
    CLASSNAME is a div class name for upper div.
    To set image to corner you'll need write in css:
    for SIMPLE:
        .CLASSNAME {
            background: #color;
            position: relative;
        }
            .CLASSNAME .tl {
                background-image: url("image to top left corner");
            }
            .CLASSNAME .tr {
                background-image: url("image to top right");
            }
            .CLASSNAME .bl {
                background-image: url("image to bottom left");
            }
            .CLASSNAME .br {
                background-image: url("image to bottom right");
            }
    for SHADOW:
        .CLASSNAME div.top {
            background-image: url("image to top with left corner");
        }
        .CLASSNAME div.top .c {
            background-image: url("image to top center");
        }
        .CLASSNAME div.centre {
            background-image: url("image to left center part");
        }
        .CLASSNAME div.centre .c {
            background-image: transparent url("image to right center part");
        }
        .CLASSNAME div.centre .c .content {
            background: #color;
        }
        .CLASSNAME div.bottom {
            background-image: url("image to bottom with left corner");
        }
        .CLASSNAME div.bottom .c{
            background-image: url("image to right bottom corner");
        }
    Ex. of use:
    1.
    {% roundcorner "simple" %}
        some div, span, or other tags here
    {% endroundcorner %}
    2.
    {% roundcorner "simple" withclass "rc_inner" %}
        some div, span, or other tags here
    {% endroundcorner %}
    """
    nodelist = parser.parse(('endroundcorner',))
    parser.delete_first_token()

    _split = token.split_contents()
    bordertype = None
    classname = None
    if len(_split) == 2:
        tag_name, bordertype = _split
    elif len(_split) == 4:
        tag_name, bordertype, param_name, classname = _split
    else:
        raise template.TemplateSyntaxError, "%r tag must be of format {%% %r 'TYPE' %%} or of format {%% %r 'TYPE' withclass 'CLASSNAME' %%}" % (tag_name, tag_name, tag_name)
    bordertype = delete_qoute(bordertype)
    classname = delete_qoute(classname)

    return RoundCornerNode(nodelist, bordertype, classname)

