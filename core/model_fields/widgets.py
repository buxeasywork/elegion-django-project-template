import os

from django.conf import settings
from django.forms import widgets
#from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
#from PIL import Image


try:
    from sorl.thumbnail.main import DjangoThumbnail
    def thumbnail(image_path):
        t = DjangoThumbnail(relative_source=image_path, requested_size=(200,200))
        return u'<img src="%s" alt="%s" />' % (t.absolute_url, image_path)
except ImportError:
    def thumbnail(image_path):
        absolute_url = os.path.join(settings.MEDIA_ROOT, image_path)
        return u'<img src="%s" alt="%s" />' % (absolute_url, image_path)

class ThumbnailImageWidget(widgets.FileInput):
    """
    A FileField Widget that display an image instead of a file path
    if the current file in an image
    Url_attr_name is name of attr, witch value is url to image
    For example, OfferImage.img have attr url_list for small image
    """
    def __init__(self, url_attr_name=None, *args, **kwargs):
        self.url_attr_name = url_attr_name
        super(ThumbnailImageWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        output = []
        file_name = str(value)
        if self.url_attr_name and value and getattr(value, self.url_attr_name, None):
            output.append('<img src=%s />' \
                % (getattr(value, self.url_attr_name)))
        #elif value and file_name:
        #    file_path = '%s%s' % (settings.MEDIA_URL, file_name)
        #    try: # is image
        #        Image.open(os.path.join(settings.MEDIA_ROOT, file_name))
        #        output.append('%s %s<br /> ' % \
        #            (_('Currently:'), thumbnail(file_name)))
        #    except IOError: # not image
        #        output.append('%s <a target="_blank" href="%s">%s</a> <br />%s ' % \
        #            (_('Currently:'), file_path, file_name, _('Change:')))
        output.append(super(ThumbnailImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))

