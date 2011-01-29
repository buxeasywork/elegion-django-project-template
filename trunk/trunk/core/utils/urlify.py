# from cicero code http://softwaremaniacs.org/soft/cicero/
import re

from django.utils.html import escape
from BeautifulSoup import BeautifulSoup


WWW_PATTERN = re.compile(r'(^|\s|\(|\[|\<|\:)www\.', re.UNICODE)
FTP_PATTERN = re.compile(r'(^|\s|\(|\[|\<|\:)ftp\.', re.UNICODE)

PROTOCOL_PATTERN =\
    re.compile(ur"""(
        (?:https?|ftp)://.*?
        #(?P<brackets>\(((?>[^()]+)|(?P>brackets))*\))?
        )
        (?=
            \s |
            [-,.;\'"!\$\^\*\(\)\[\]{}`\~\\:<>\+=]+(?=\s|$) |
            &nbsp; |
            &\#039; |
            &quot; |
            &gt; |
            &lt; |$)""", re.X + re.U + re.I)

WOPROTOCOL_PATTERN =\
    re.compile(ur"""
        (?<!http://)(?<!https://)(?<!ftp://)
        (www\.[\d\w.-]+(?:\.\w{2,}(?P<slash>/?))
            (?(slash).*?
            #(?P<brackets>\(((?>[^()]+)|(?P>brackets))*\))?
            )
        )
        (?=
            \s |
            [-,.;\'"!\$\^\*\(\)\[\]{}`\~\\:<>\+=]+(?=\s|$) |
            &nbsp; |
            &\#039; |
            &quot; |
            &gt; |
            &lt; |$)""", re.X + re.U + re.I)


def urlify(value):
    soup = BeautifulSoup(value)

    def urlify(s):
        s = escape(s)
        s = re.sub(PROTOCOL_PATTERN, r'<a href="\1">\1</a>', s)
        s = re.sub(WOPROTOCOL_PATTERN, r'<a href="http://\1">\1</a>', s)
        return BeautifulSoup(s)

    def has_parents(node, tags):
        if node is None:
            return False
        return node.name in tags or has_parents(node.parent, tags)

    text_chunks = (c for c in soup.recursiveChildGenerator() if isinstance(c, unicode))
    for chunk in text_chunks:
        s = chunk
        if not has_parents(chunk.parent, ['a', 'code']):
            s = urlify(s)
        chunk.replaceWith(s)

    for link in soup.findAll('a'):
        if 'rel' in link:
            link['rel'] += ' '
        else:
            link['rel'] = ''
        link['rel'] += 'nofollow'

    return unicode(soup)

