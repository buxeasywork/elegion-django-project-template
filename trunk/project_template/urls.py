from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^a/', include('a.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^adminko/doc/', include('django.contrib.admindocs.urls')),

    # Serve static media
    (r'^(?P<path>.*\.(js|css|xls|ico|png|gif|jpg|doc))$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^(?P<path>.*writable/.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
