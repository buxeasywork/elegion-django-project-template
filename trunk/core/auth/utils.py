import re

from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import get_resolver

from core.utils import Transliterator


RE_INVALID_USERNAME = re.compile(r'[^\w]+')

def conflicts_url(slug):
    """
    Determines if given slug conficts with first part of any project's url.

    Useful for links like host.domain/<username>
    """
    for func, pattern in get_resolver(settings.ROOT_URLCONF).reverse_dict.items():
        urlpart = pattern[0][0][0].rstrip('/').split('/')
        if len(urlpart) == 1:
            if urlpart[0] == slug:
                return True
    return False


def get_username_diff_from_url(username):
    suffix = 0
    while conflicts_url(username + str(suffix or '')):
        suffix += 1
    return username + str(suffix or '')


WRONG_PLACEHOLDER = '_'

def get_unique_username(username):
    """
    From source in any language, returns correct unique username.
    """
    assert len(username) > 0, 'username should not be empty'

    username = Transliterator().process(username)
    # First remove all bad symbols.
    username = RE_INVALID_USERNAME.sub(WRONG_PLACEHOLDER, username)
    username = username.strip(WRONG_PLACEHOLDER)

    username = get_username_diff_from_url(username)
    # Append number to end of username if user with such username exists.
    suffix = 0
    while User.objects.filter(username=username + str(suffix or '')).count():
        suffix += 1
    return username + str(suffix or '')
