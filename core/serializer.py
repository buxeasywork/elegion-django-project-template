from copy import deepcopy
import codecs
from StringIO import StringIO
from django.db.models.query import QuerySet
from django.conf import settings
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.test.signals import template_rendered
from django.utils import simplejson


class WrongFormatException(Exception):
    pass


class Serializer(object):
    possible_formats = ['json']
    format = None

    def __init__(self, format):
        if format in self.possible_formats:
            self.format = format
            # Should be False for json.
            self.ensure_ascii = format != 'json'
            self.serializer = serializers.get_serializer(format)()
        else:
            raise WrongFormatException

    def def_sensitive_data_provider(self, object):
        return ()

    sensitive_data_provider = def_sensitive_data_provider

    def serialize_qs(self, qs, *args, **kwargs):
        str = StringIO()
        res = codecs.getwriter('utf8')(str)

        kwargs['excludes'] = ()
        if isinstance(qs, list) and len(qs):
            for item in qs:
                kwargs['excludes'] += self.sensitive_data_provider(item)
        else:
            kwargs['excludes'] = self.sensitive_data_provider(qs)

        self.serializer.serialize(qs,
                ensure_ascii=self.ensure_ascii,
                stream=res,
                **kwargs)
        return self.serializer.objects

    def render_to_response(self, data, response, jsoncallback=None, *args, **kwargs):
        # for successfull testing with django test client
        plain_data = deepcopy(data)

        if type(data) == dict:
            for key in data:
                if isinstance(data[key], QuerySet) \
                    or (isinstance(data[key], list)
                        and len(data[key]) != 0
                        and isinstance(data[key][0], models.Model)):
                    data[key] = self.serialize_qs(data[key], *args, **kwargs)
        else:
            data = self.serialize_qs(data, *args, **kwargs)
        if 'extras' in kwargs: del kwargs['extras']
        if 'relations' in kwargs: del kwargs['relations']
        if settings.DEBUG:
            kwargs['indent'] = 4
        response.content = simplejson.dumps(data, cls=DjangoJSONEncoder, *args, **kwargs)

        template_rendered.send(sender=self, template=self, context={'data':plain_data, 'sdata': data})

        if self.format == 'json':
            response['Content-Type'] = 'application/x-javascript; charset=utf-8'
            if jsoncallback:
                response.content = ''.join([jsoncallback, '(', force_unicode(response.content), ')'])

        return response

