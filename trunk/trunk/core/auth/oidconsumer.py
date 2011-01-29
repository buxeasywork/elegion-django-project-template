from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from django_openid.auth import AuthConsumer


class UserFriendlyConsumer(AuthConsumer):
    """
    Special OpenID consumer based on django_openid
    Realizes user-friendly OpenId login with list of most popular providers
    """

    login_plus_password_template = 'core/openid/login_plus_password.html'

    def do_login(self, request, extra_message=None):
        request.POST = request.POST.copy()
        if request.method == 'POST':
            provider = request.POST.get('provider', '')
            oid = request.POST.get('oid', '').strip()
            expiry = 0
            if provider == 'google':
                oid = 'https://www.google.com/accounts/o8/id'
            elif provider == 'yandex':
                oid = 'http://openid.yandex.ru/'
            elif provider == 'yahoo':
                oid = 'http://yahoo.com/'
            elif provider == 'openid':
                pass
            else:
                oid = None

            if request.POST.get('remember', ''):
                expiry = None

            request.POST.update({'openid_url': oid})
            request.session.set_expiry(expiry)

        return super(UserFriendlyConsumer, self).do_login(request, extra_message)

    def extract_extension_params(self, openid_response):
        all_params = {}
        for ns in self.extension_namespaces:
            ext_params = openid_response.extensionResponse(self.extension_namespaces[ns], False)
            if ns == 'sreg':
                all_params.update(ext_params)
                continue
            for pn in ext_params:
                parts = pn.partition('.')
                if parts[0] == 'value' and parts[2]:
                    all_params[parts[2]] = ext_params[pn]
        return all_params

    def show_unknown_openid(self, request, openid, openid_response):
        # This can be over-ridden to show a registration form
        ext_params = self.extract_extension_params(openid_response)
        return self.show_register(request, openid, ext_params)

    def show_register(self, request, openid, ext_params):
        """
        Override in subclasses
        """
        return self.show_message(request,
                                 'Unknown OpenID',
                                 '%s is an unknown OpenID, params %s' % (openid, ext_params))

    def do_xrds(self, request):
        uri = '%(proto)s://%(domain)s%(path)s' % {'proto': 'https' if request.is_secure() else 'http',
                                                  'domain': Site.objects.get_current().domain,
                                                  'path': reverse('openid-complete')}
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n' \
              '<xrds:XRDS\n' \
              ' xmlns:xrds="xri://$xrds"\n' \
              ' xmlns:openid="http://openid.net/xmlns/1.0"\n' \
              ' xmlns="xri://$xrd*($v*2.0)">\n' \
              '    <XRD>\n' \
              '        <Service priority="1">\n' \
              '            <Type>http://specs.openid.net/auth/2.0/return_to</Type>\n' \
              '            <URI>%(uri)s</URI>\n' \
              '        </Service>\n' \
              '    </XRD>\n' \
              '</xrds:XRDS>' % {'uri': uri}
        return HttpResponse(xml, mimetype='application/xrds+xml')

