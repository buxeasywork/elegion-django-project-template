# -*- coding: UTF-8 -*-
import os
import urlparse

from django.contrib.sites.models import Site
from django.conf import settings
from django.template import Library


register = Library()


def _absolute_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        return url
    domain = Site.objects.get_current().domain
    return 'http://%s%s' % (domain, url)


def compress_auto_update(filename):
    """
    default tags from compressed is better

    support for django-compress auto update
    COMPRESS_VERSION isn't supported
    """
    if 'compress' in settings.INSTALLED_APPS:
        from compress.conf import settings as csettings
        from compress.utils import needs_update, filter_css, filter_js, filter_common
        from compress.signals import css_filtered, js_filtered
        if csettings.COMPRESS_AUTO:
            # determine files where COMPRESS settings defined
            # to include them in version check
            try:
                import inspect
                settings_file = (inspect.getsourcefile(csettings.COMPRESS_AUTO),)
            except:
                settings_file = ()

            # try to find target file in compress settings
            for obj in csettings.COMPRESS_CSS.values() + csettings.COMPRESS_JS.values():
                if obj['output_filename'] == filename:

                    u, version = needs_update(obj['output_filename'],
                                              tuple(obj['source_filenames']) + settings_file)
                    if u:
                        if csettings.COMPRESS:
                            if filename.endswith('.css'):
                                filter_css(obj)

                            if filename.endswith('.js'):
                                filter_js(obj)
                        else:
                            # simple join
                            return filter_common(obj, 0, filters=[], attr='', separator='', signal=js_filtered)
                    break


@register.simple_tag
def media(filename, flags=''):
    flags = set(f.strip() for f in flags.split(','))
    url = urlparse.urljoin(settings.MEDIA_URL, filename)
    if 'absolute' in flags:
        url = _absolute_url(url)
    if (filename.endswith('.css') or filename.endswith('.js')) and 'no-timestamp' not in flags or \
       'timestamp' in flags:
        compress_auto_update(filename)
        fullname = os.path.join(settings.MEDIA_ROOT, filename)
        if os.path.exists(fullname):
            url += '?%d' % os.path.getmtime(fullname)
    return url

