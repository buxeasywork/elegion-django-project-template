from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import get_callable

from core.exceptions import EForbidden


class EmbeddedAdminSite(admin.AdminSite):
    """
    Customized (embedded) admin site. Supports different login and logout.
    Throws EForbidden for non staff users.

    Settings:
        EMBEDDED_ADMIN_LOGIN_VIEW
        EMBEDDED_ADMIN_LOGOUT_VIEW
    """
    def login(self, request):
        try:
            return get_callable(settings.EMBEDDED_ADMIN_LOGIN_VIEW)(request)
        except:
            return super(EmbeddedAdminSite, self).login(request)

    def logout(self, request):
        try:
            return get_callable(settings.EMBEDDED_ADMIN_LOGOUT_VIEW)(request)
        except:
            return super(EmbeddedAdminSite, self).logout(request)

    def has_permission(self, request):
        """ Generate our beautiful EForbidden if user haven't staff status """
        if not request.user.is_staff:
            raise EForbidden()
        return super(EmbeddedAdminSite, self).has_permission(request)

