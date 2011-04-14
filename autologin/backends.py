from django.conf import settings
from django.contrib.auth.models import User, check_password

from autologin.models import AutologinToken


class AutologinTokenBackend:
    def authenticate(self, token):
        return AutologinToken.objects.get_user(token)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None