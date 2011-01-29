# -*- coding: UTF-8 -*-
from functools import wraps
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from django.core.cache import cache
from django.conf import settings

from core.http import HttpResponseServiceUnavailable
from core.utils import get_decorated_function


def permission_required(perm, login_url=None, redirect_field_name=None):
    if not login_url:
        login_url = settings.LOGIN_URL
    if not redirect_field_name:
        from django.contrib.auth import REDIRECT_FIELD_NAME
        redirect_field_name = REDIRECT_FIELD_NAME

    def decorate(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            if request.user.is_anonymous():
                path = urlquote(request.get_full_path())
                tup = login_url, redirect_field_name, path
                return HttpResponseRedirect('%s?%s=%s' % tup)
            from core.exceptions import EForbidden
            raise EForbidden('Permissions \'%s\' required' % perm)
#            return HttpResponseForbidden()
#            raise Http403('Permissions \'%s\' required' % perm)

        return wrapper
    return decorate


class limit_request_rate(object):
    """
    Decorator for view that limit request rate for view for concrete user.
    Anonymous users not limited.

    Note: memcached expiration precision depends on the platform, but usually it is 1 second.

    @TODO: differentiate anonymous users by IP
    """
    CACHE_VAR_PREFIX = "limit_request_rate_"

    def __init__(self, timeout = None, object_id = None):
        self.timeout = timeout or settings.DEFAULT_REQUEST_TIMEOUT
        self.object_id = object_id

    def __call__(self, function):
        def actual_decorator(request, *args, **kwargs):
            if request.user.is_authenticated():
                if self.object_id is None:
                    dec_func = get_decorated_function(function)
                    self.object_id = dec_func.func_name + dec_func.func_code.co_filename
                cache_key = '%s_%s_%s' % (self.CACHE_VAR_PREFIX,
                                          str(request.user.id),
                                          self.object_id)
                if not cache.get(cache_key):
                    cache.set(cache_key, 1, self.timeout)
                    return function(request, *args, **kwargs)
                else:
                    return HttpResponseServiceUnavailable()
            return function(request, *args, **kwargs)
        return actual_decorator

