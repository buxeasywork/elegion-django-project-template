import datetime

from django.contrib.auth.models import User
from django.db import models


class LoginAttempt(models.Model):
    user = models.ForeignKey(User)
    ts = models.DateTimeField(auto_now_add=True)

    def get_count(self, user, interval):
        return LoginAttempt.objects.filter(user=user,
            ts__range=(datetime.now() - interval, datetime.now())).count()

    def clean_up(self, user):
        LoginAttempt.objects.filter(user=user).delete()

