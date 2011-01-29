from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core.validators import email_re
from django.template import Context, loader
from django.utils.http import int_to_base36
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

from core.auth.models import LoginAttempt


class BasicBackend:
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailBackend(BasicBackend):
    def authenticate(self, username=None, password=None):
        # If username is an email address, then try to pull it up
        if email_re.search(username):
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        else:
            # We have a non-email address username we should try username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        if user.check_password(password):
            return user


class BlockerBackend(ModelBackend):
    """
    This backend actually doesn't authenticate users, it only logs wrong login
    attempts. And then they reach some limit, it blocks user.
    """
    def __init__(self):
        if hasattr(settings, 'LOGIN_BLOCK_TIME_SPAN'):
            self.interval = settings.LOGIN_BLOCK_TIME_SPAN
        else:
            self.interval = timedelta(days=1)
        if hasattr(settings, 'LOGIN_BLOCK_COUNT'):
            self.attempts_limit = settings.LOGIN_BLOCK_COUNT
        else:
            self.attempts_limit = 3
        self.email_template = settings.LOGIN_BLOCK_EMAIL_TEMPLATE
        current_site = Site.objects.get_current()
        self.site_name = current_site.name
        self.domain = current_site.domain

    def authenticate(self, username=None, password=None):
        # FIXME: I'm copy-paste
        if email_re.search(username):
            argname = 'email'
        else:
            argname = 'username'
        try:
            user = User.objects.get(**{argname: username})
        except User.DoesNotExist:
            return None

        # If user's already blocked, do nothing
        if not user.is_active:
            return user

        attempt = LoginAttempt.objects.create(user=user)
        attempts_count = attempt.get_count(user=user, interval=self.interval)
        if attempts_count >= self.attempts_limit:
            # Block user
            user.is_active = False
            user.save()
            # Send e-mail
            t = loader.get_template(self.email_template)
            c = {
                'user': user,
                'domain': self.domain,
                'uid': int_to_base36(user.id),
                'token': default_token_generator.make_token(user),
            }
            send_mail(
                _('Account blocked on site %s') % self.site_name,
                t.render(Context(c)),
                settings.EMAIL_FROM,
                [user.email]
            )
            return user

