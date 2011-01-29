import re
import cssutils
from BeautifulSoup import BeautifulSoup, Comment

VALID_TAGS = {'h1': ('align','style'),
              'h2': ('align','style',),
              'h3': ('align','style',),
              'h4': ('align','style',),
              'h5': ('align','style',),
              'h6': ('align','style',),
              'p': ('align','style',),
              'div': ('align','style',),
              'span': ('style',),
              'br': (),
              'strong': (),
              'blockquote': (),
              'i': (),
              'em': (),
              'u': (),
              'strike': (),
              'a': ('href','id','style',),
              'img': ('src','alt','align','title','border','width',
                      'height','hspace','vspace','style'),
              'pre': (),
              'code': (),
              'dl': (),
              'dt': (),
              'dd': (),
              'ul': (),
              'ol': (),
              'li': (),
              'table': ('cellspacing','cellpadding','border','style',),
              'tr': (),
              'td': ('colspan','rowspan','align','valign','style',),
              'th': ('colspan','rowspan','align','valign','style',),
}

VALID_STYLE = (
    'padding',
    'margin',
    'width',
    'height',
    'border',
    'background-color',
    'border-width',
    'border-color',
    'border-style',
    'font',
    'font-family',
    'font-size',
    'font-weight',
    'float',
    'color',
    'text-align',
    'text-decoration',
)

def clean_html(value, allowed_tags=VALID_TAGS, allowed_style=VALID_STYLE):
    """Argument should be in form 'tag2:attr1:attr2 tag2:attr1 tag3', where tags
    are allowed HTML tags, and attrs are the allowed attributes for that tag.
    """
    js_regex = re.compile(r'[\s]*(&#x.{1,7})?'.join(list('javascript')))
    if not isinstance(allowed_tags, dict):
        allowed_tags = [tag.split(':') for tag in allowed_tags.split()]
        allowed_tags = dict((tag[0], tag[1:]) for tag in allowed_tags)

    try:
        soup = BeautifulSoup(value)
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        for tag in soup.findAll(True):
            if tag.name not in allowed_tags:
                tag.hidden = True
            else:
                tag.attrs = [(attr, js_regex.sub('', val)) for attr, val in tag.attrs
                             if attr in allowed_tags[tag.name]]
                if tag.has_key('style'):
                    css_properties = cssutils.css.CSSStyleDeclaration(
                        cssText=tag['style']
                    )
                    for x in css_properties:
                        if not (x.wellformed\
                                and x.name.lower() in VALID_STYLE\
                                and x.valid):
                            css_properties.removeProperty(x.name)
                    tag['style'] = css_properties.cssText
        return soup.renderContents().decode('utf8')
    except:
        return ''

