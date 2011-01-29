# -*- coding: UTF-8 -*-
import os
import re
import tempfile
import types
import urllib2
import urlparse
from random import randint
from datetime import date, timedelta
from urllib import urlretrieve

from django.core.cache import cache
from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

# inner imports
from transliterator import Transliterator
from urlify import urlify
# /inner imports


def add_field_class_names(form):
    """
    Adds ``class`` attribute to the fields.
    Class names are: name of the field, name of the widget and
        Required or Optional.

    """
    for name, field in form.fields.iteritems():
        new_classes = [type(field).__name__,
                       type(field.widget).__name__,
                       field.required and 'Required' or 'Optional']
        if form[name].errors:
            new_classes = new_classes + ['Error',]

        if 'class' in field.widget.attrs:
            # Preserve existing classes
            new_classes.extend(field.widget.attrs['class'].split())
        field.widget.attrs['class'] = ' '.join(new_classes)


def make_full_url(path, site=None):
    if site is None:
        site = Site.objects.get_current()
    return urlparse.urljoin('http://' + site.name, path)


def referer_is_view(request, view):
    domain = Site.objects.get_current().domain
    url = reverse(view)
    return request.META.has_key('HTTP_REFERER') and \
        (request.META['HTTP_REFERER'].startswith(url) or \
         request.META['HTTP_REFERER'].startswith(urlparse.urljoin('http://' + domain, url)) or \
         request.META['HTTP_REFERER'].startswith(urlparse.urljoin('https://' + domain, url)))


def parse_phone(value):
    """Parses string in format ``(.*) .*``"""
    code = ''
    number = ''
    if value != None and value != '':
        pos = 0
        value.strip()
        if value[0] == '(':
            pos = value.find(')')
            if pos > 1:
                code = value[1:pos]
                # Skip closing bracket and a space
                pos += 1
                if value[pos] == ' ':
                    pos += 1
        # Slice the remaining part (without the code, if it's present)
        number = value[pos:]
    return code, number


def get_cell_value(cell):
    def make_closure_that_returns_value(use_this_value):
        def closure_that_returns_value():
            return use_this_value
        return closure_that_returns_value
    dummy_function = make_closure_that_returns_value(0)
    dummy_function_code = dummy_function.func_code
    our_function = types.FunctionType(dummy_function_code, {}, None, None, (cell,))
    value_from_cell = our_function()
    return value_from_cell


def get_decorated_function(function):
    """ Returns actual decorated function in decorators stack """
    while function.func_closure is not None:
        function = get_cell_value(function.func_closure[0])
    return function


def clear_cache():
    """ Warning not tested """
    if hasattr(cache, '_cache'):
        if hasattr(cache._cache, 'clear'):
            cache._cache.clear()    # in-memory caching
        if hasattr(cache._cache, 'flush_all'):
            cache._cache.flush_all() #memcached
    if hasattr(cache, '_expire_info'):
        cache._expire_info.clear() #loc mem

    if hasattr(cache, '_cache'):
        if hasattr(cache._cache, 'clear'):
            cache._cache.clear()    # in-memory caching
        if hasattr(cache._cache, 'flush_all'):
            cache._cache.flush_all() #memcached
    if hasattr(cache, '_expire_info'):
        cache._expire_info.clear() #loc mem

    try:
        # try filesystem caching next
        old = cache._cull_frequency
        old_max = cache._max_entries
        cache._max_entries = 0
        cache._cull_frequency = 1
        cache._cull()
        cache._cull_frequency = old
        cache._max_entries = old_max
    except:
        pass


def merge_qs(*args):
    results = set()
    for qs in args:
        qs_set = set()
        for obj in qs:
            qs_set.add(obj)
        results = results.union(qs_set)
    return list(results)


def tdelta2seconds(td):
    return td.days * 24 * 60 * 60 + td.seconds


def download_file(url, path):
    parsed = urlparse.urlparse(url)
    filename = parsed[2].split("/")[-1]

    outpath = os.path.join(path, filename)
    urlretrieve(url, outpath)
    return filename


def download_file_tmp(url):
    """
    Download file to temporaly storage.
    Returns name and open django wrapper.
    So you can save image fields like this img_field.save(name, file)
    """
    urlfile = urllib2.urlopen(url)
    tmpfile = tempfile.NamedTemporaryFile()
    tmpfile.write(urlfile.read())

    parsed = urlparse.urlparse(url)
    name = parsed[2].split("/")[-1]
    return (name, File(tmpfile))


NUM_RE = re.compile('([0-9]+)')
def human_sort(list, key=None):
    if key is None:
        def human_sort_key(s):
            return [int(c) if c.isdigit() else c.lower() for c in NUM_RE.split(s[0] if isinstance(s, list) else s)]
        return sorted(list, key=human_sort_key)
    else:
        def human_sort_key(s):
            return [int(c) if c.isdigit() else c.lower() for c in NUM_RE.split(s[0])]
        decorated = [(getattr(item, key), item) for item in list]
        return [item for (value, item) in sorted(decorated, key=human_sort_key)]


def cut_date_segment(victim, cut):
    """
    Takes two date intervals in the form of two tuples: (start, end).
    Returns new interval, which is the complement of those (victim \ cut) if applicable.
    If cut is a subset of victim return None.
    If victim is a subset of cut return tuple of tuples.
    """
    # substract 1 day from cut start
    cut[0] -= timedelta(days=1)
    # add 1 day to cut end
    cut[1] += timedelta(days=1)

    victim[0] = victim[0]
    victim[1] = victim[1]

    # v--c---c--v
    if victim[0] > cut[0] and victim[1] < cut[1]:
        return None

    # c--v---v--c
    if victim[0] <= cut[0] and victim[1] >= cut[1]:
        return ((victim[0], cut[0]), (cut[1], victim[1]))

    # c--v--c--v
    if victim[0] > cut[0]:
        return (max(victim[0], cut[1]), victim[1])

    # v--c--v--c
    if (victim[1] < cut[1]):
        return (victim[0], min(victim[1], cut[0]))

    # shouldn't happen )
    return (victim[0], victim[1])
    

def random_sequence(length):
    return '%.5x' % randint(0, 16**length)