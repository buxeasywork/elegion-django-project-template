from django.template import Library


register = Library()

CODE = r"""
<script>
var mb_random = Math.round(Math.random() * 100000);
<!-- TODO replace with addChild -->
document.write("<iframe scrolling='no' frameborder='0' marginheight='0' marginwidth='0' width='%(width)s' height='%(height)s' src='%(url)s?project=%(project)s&place=%(place)s&" + mb_random + "'></iframe>");
</script>
<noscript>
<iframe width='%(width)s' height='%(height)s' src='%(url)s?project=%(project)s&place=%(place)s'></iframe>
</noscript>
"""

@register.simple_tag
def banner(project, place, width, height):
    url = 'http://test.ebn1.ru/get'
    return CODE % {'url': url, 'project': project, 'place': place, 'width': width, 'height': height}

