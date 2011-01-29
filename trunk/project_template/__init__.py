import sys
import os
import logging, logging.handlers

from django.conf import settings


workdir = os.path.dirname(__file__)
path = os.path.join(workdir, 'lib', 'python')
sys.path.insert(0, path)

logger = logging.getLogger('prname')
if settings.DEBUG:
    level = logging.DEBUG
    handler = logging.StreamHandler()
else:
    level = logging.CRITICAL
    handler = logging.handlers.SMTPHandler((settings.EMAIL_HOST, getattr(settings, 'EMAIL_PORT', 25)),
                                           settings.DEFAULT_FROM_EMAIL,
                                           [a[1] for a in settings.ADMINS], 'Logging')
logger.setLevel(level)
handler.setLevel(level)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

