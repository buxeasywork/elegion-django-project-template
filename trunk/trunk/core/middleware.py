import re

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseForbidden
from django.template import loader, RequestContext

from core.exceptions import EForbidden

try:
    import tidy
except ImportError:
    tidy = False


class LogoutInactiveMiddleware:
    def process_request(self, request):
        if request.user.is_authenticated() and request.user.is_active == 0:
            logout(request)


class ForbiddenMiddleware:
    """
    Wraps EForbidden exception in a 403 template
    and returns HttpResponseForbidden

    """
    def process_exception(self, request, exception):
        if not isinstance(exception, EForbidden):
            return
        try:
            template = loader.get_template('403.html')
            context = RequestContext(request, {'message': str(exception)})
            return HttpResponseForbidden(template.render(context))
        except:
            pass # Let Django show the exception


class RemoveEmptyLinesFromResponse:
    """
    TODO profile, optimize (maybe rewrite django template engine or use other)
    """
    def __init__(self):
        self.whitespace = re.compile('\s*\n')

    def process_response(self, request, response):
        if "text/html" in response['Content-Type']:
            response.content = self.whitespace.sub('\n', response.content)
        return response


class HTMLBeautifyMiddleware:
    """
    ATTENTION! Corrupts JSON response, need improvements

    Makes HTML output beautiful. If setting.DEBUG == False it user uTidyLib, if
    it's present. Otherwise it only strips empty lines.
    """
    def __init__(self):
        self.tidy = False
        if not settings.DEBUG:
            self.do_tidy = tidy
        if not self.tidy:
            self.whitespace = re.compile('\s*\n')

    def process_response(self, request, response):
        if "text/html" in response['Content-Type']:
            if self.do_tidy and tidy:
                options = {
                    'doctype': 'auto',
                    'drop-empty-paras': 0,
                    'fix-backslash': 0,
                    'fix-bad_comments': 0,
                    'fix-uri': 0,
                    'hide-comments': 0,
                    'join-classes': 1,
                    'join-styles': 1,
                    'lower-literals': 1,
                    'merge-divs': 0,
                    'merge-spans': 0,
                    'output-html': 1,
                    'preserve-entities': 1,

                    'show-errors': 0,
                    'show-warnings': 0,

                    'break-before-br': 1,
                    'indent': 'auto',
                    'indent-attributes': 0,
                    'indent-spaces': 2,
                    'vertical-space': 0,
                    'wrap': 80,
                    'wrap-script-literals': 0,

                    'char-encoding': 'utf8',
                    'input-encoding': 'utf8',
                    'newline': 'lf',
                    'output-bom': 0,
                    'output-encoding': 'utf8',

                    'force-output': 1,
                    'quiet': 1,
                    'tidy-mark': 0
                }
                response.content = tidy.parseString(response.content, **options)
            else:
                response.content = self.whitespace.sub('\n', response.content)
            return response
        else:
            return response


class OidXRDSHeader:
    """
    Adds X-XRDS-Location header to all requests, which path starts with
    OpenID realm (trust root).

    Yadis protocol uses it to get the xrds document.
    See http://openid.net/specs/openid-authentication-2_0.html#rp_discovery
        and core.auth.oidconsumer do_xrds method.

    """
    def process_response(self, request, response):
        if request.path.startswith('/login'):
            try:
                uri = '%(proto)s://%(domain)s%(path)s' % {'proto': 'https' if request.is_secure() else 'http',
                                                          'domain': Site.objects.get_current().domain,
                                                          'path': reverse('openid-xrds')}
                response['X-XRDS-Location'] = uri
            except NoReverseMatch:
                pass
        return response


from core.auth.form import AuthForm

class LoginFormMiddleware(object):
    def process_request(self, request):
        # if the top login form has been posted
        if request.method == 'POST' and 'is_top_login_form' in request.POST:
            # validate the form
            form = AuthForm(data=request.POST)
            if form.is_valid():
                # log the user in
                from django.contrib.auth import login
                login(request, form.get_user())

                # if this is the logout page, then redirect to /
                # so we don't get logged out just after logging in
                if '/account/logout/' in request.get_full_path():
                    return HttpResponseRedirect('/')
        else:
            form = AuthForm()

        # attach the form to the request so it can be accessed within the templates
        request.login_form = form
