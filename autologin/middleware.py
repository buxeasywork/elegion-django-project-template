from django.contrib.auth import login, authenticate

from autologin.models import AutologinToken


class AutologinTokenMiddleware(object):
    """
    AutoLogin user is we have login token in url
    """
    def process_request(self, request):
        autologin_token = request.GET.get('autologin_token', None)
        if autologin_token:        
            user = authenticate(token=autologin_token)
            if user:
                login(request, user)
