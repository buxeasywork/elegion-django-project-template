from django.core.cache.backends.base import InvalidCacheBackendError
from django.core.cache.backends.memcached import CacheClass as MemcachedCacheClass
from django.utils.encoding import smart_str


class CacheClass(MemcachedCacheClass):
    """
    Memcached cache backend with key prefixing
    core.cache.memcached_key_prefix:///127.0.0.1:11211/?key_prefix=bla_

    @todo make as wrapper to any backend
    """
    def __init__(self, server, params):
        try:
            self._key_prefix = smart_str(params['key_prefix'])
        except KeyError:
            raise InvalidCacheBackendError('key_prefix not specified')

        super(CacheClass, self).__init__(server, params)

    def _get_key(self, key):
        return self._key_prefix + smart_str(key)

    def add(self, key, value, timeout=0):
        return super(CacheClass, self).add(self._get_key(key), value, timeout)

    def get(self, key, default=None):
        return super(CacheClass, self).get(self._get_key(key), default)

    def set(self, key, value, timeout=0):
        return super(CacheClass, self).set(self._get_key(key), value, timeout)

    def delete(self, key):
        return super(CacheClass, self).delete(self._get_key(key))

    def get_many(self, keys):
        keys = [self._get_key(key) for key in keys]
        return super(CacheClass, self).get_many(keys)

    def incr(self, key, delta=1):
        return super(CacheClass, self).incr(self._get_key(key), delta)

    def decr(self, key, delta=1):
        return super(CacheClass, self).decr(self._get_key(key), delta)

