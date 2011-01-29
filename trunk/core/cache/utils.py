from django.core.cache import cache
from django.utils.hashcompat import md5_constructor
from django.conf import settings


def get_cache_key(request):
    url = md5_constructor(request.path_info).hexdigest()
    query_string = md5_constructor(request.META.get('QUERY_STRING', ''))\
        .hexdigest()
    keyprefix = getattr(settings, 'CACHE_PAGE_KEY_PREFIX', '')
    if request.user.is_authenticated():
        return '_'.join([keyprefix, str(request.user.pk), url, query_string])
    else:
        return '_'.join([keyprefix, url, query_string])


def cache_page(timeout=None):
    if timeout is None:
        timeout = settings.CACHE_PAGE_TIMEOUT
    def _wrapper(func):
        def _inner(request, *args, **kwargs):
            key = get_cache_key(request)
            if timeout:
                resp = cache.get(key, None)
            else:
                resp = None

            if not resp:
                resp = func(request, *args, **kwargs)
                cache.set(key, resp, timeout)

            return resp
        return _inner
    return _wrapper
