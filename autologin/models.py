import re
from random import randint
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _


EXPIRES_INT = {'weeks':1} #timedelta dict

AUTOLOGIN_LENGTH = 20


class AutologinTokenManager(models.Manager):
    def get_user(self, token):
        token_obj = self.filter(token=token)
        if token_obj:
            if token_obj[0].expires > datetime.datetime.now():
                return token_obj[0].user
            else:
                token_obj[0].delete()
        return None
        
    def generate(self, user):
        token_obj = self.create(\
            token=random_sequence(AUTOLOGIN_LENGTH), user=user,
            expires=datetime.datetime.now() + datetime.timedelta(**EXPIRES_INT))
        return token_obj.token


class AutologinToken(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    token = models.CharField(max_length=50, blank=True)
    expires = models.DateTimeField()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = AutologinTokenManager()

    def __unicode__(self):
        return '%s till %s' % (self.user, self.expires)


def random_sequence(length):
    return '%.5x' % randint(0, 16**length)