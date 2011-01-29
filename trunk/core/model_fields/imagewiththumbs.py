# -*- encoding: utf-8 -*-
"""
django-thumbs by Antonio Melé
http://code.google.com/p/django-thumbs/
http://django.es
"""
import cStringIO
import os
import types

from django.core.files.base import ContentFile
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
#from PIL import Image


def generate_thumb(img, thumb_size, format):
    """
    Generates a thumbnail image and returns a ContentFile object with the thumbnail

    Parameters:
    ===========
    img         File object

    thumb_size  desired thumbnail size, ie: (200,120)

    format      format of the original image ('jpeg','gif','png',...)
                (this format will be used for the generated thumbnail, too)
    """

    img.seek(0) # see http://code.djangoproject.com/ticket/8222 for details
    image = Image.open(img)

    # Convert to RGB if necessary
    if image.mode not in ('L', 'RGBA'):
        image = image.convert('RGBA')

    # get size
    thumb_w, thumb_h = thumb_size
    # If you want to generate a square thumbnail
    if thumb_w == thumb_h:
        xsize, ysize = image.size
        if xsize < ysize:
            # Vertical crop: cut from top to size.
            size = (0, 0, xsize, xsize)
        else:
            # Horisontal crop: cut the edges on the left and right.
            middle = xsize >> 1
            half = ysize >> 1
            size = (middle - half, 0, middle + half, ysize)
        # crop it
        image2 = image.crop(size)
        # load is necessary after crop
        image2.load()
        # thumbnail of the cropped image (with ANTIALIAS to make it look better)
        image2.thumbnail(thumb_size, Image.ANTIALIAS)
    else:
        image2 = image
        image2.thumbnail(thumb_size, Image.ANTIALIAS)

    io = cStringIO.StringIO()
    # PNG and GIF are the same, JPG is JPEG
    if format.upper()=='JPG':
        format = 'JPEG'

    if format == 'JPEG':
        image2.save(io, format, quality=90, optimize=True)
    else:
        image2.save(io, format)

    return ContentFile(io.getvalue())


class ImageWithThumbsFieldFile(ImageFieldFile):
    """
    See ImageWithThumbsField for usage example
    """
    def __init__(self, *args, **kwargs):
        super(ImageWithThumbsFieldFile, self).__init__(*args, **kwargs)
        self.sizes = self.field.sizes

        if self.sizes:
            def get_size(self, size_name):
                if not self:
                    return ''
                else:
                    split = self.url.rsplit('.',1)
                    thumb_url = '%s.%s.%s' % (split[0], size_name, split[1])
                    return thumb_url

            for size_name in self.sizes:
                setattr(self, 'url_%s' % size_name, get_size(self, size_name))

    def save(self, name, content, save=True):
        super(ImageWithThumbsFieldFile, self).save(name, content, save)

        if self.field.sizes:
            for size_name in self.field.sizes:
                size = self.field.sizes[size_name]
                try:
                    split = self._name.rsplit('.',1)
                except AttributeError:
                    split = self.name.rsplit('.', 1)
                thumb_name = '%s.%s.%s' % (split[0], size_name, split[1])

                # you can use another thumbnailing function if you like
                thumb_content = generate_thumb(content, size, split[1])

                thumb_name_ = self.storage.save(thumb_name, thumb_content)

                if not thumb_name == thumb_name_:
                    raise ValueError('There is already a file named %s' % thumb_name)

    def delete(self, save=True):
        name=self.name
        super(ImageWithThumbsFieldFile, self).delete(save)
        if self.sizes:
            for size_name in self.field.sizes:
                size = self.field.sizes[size_name]
                split = name.rsplit('.',1)
                thumb_name = '%s.%s.%s' % (split[0], size_name, split[1])
                try:
                    self.storage.delete(thumb_name)
                except:
                    pass

    def regenerate_thumbnails(self, force=False):
        if not os.path.isfile(self.path):
            raise ValueError('Original image not found.')
        parts = self.path.rpartition('.')
        count = 0
        for size_name in self.sizes.keys():
            path = parts[1].join((parts[0], size_name, parts[2]))
            if not os.path.exists(path) or force:
                image = open(self.path)
                thumb_content = generate_thumb(image, self.sizes[size_name], parts[2])
                # FIXME: is this the right way? I don't think so.
                self.storage.location = os.path.join(self.storage.location, self.field.upload_to)
                self.storage.save(os.path.basename(path), thumb_content)
                count += 1
        return count


class ImageWithThumbsField(ImageField):
    attr_class = ImageWithThumbsFieldFile
    """
    Usage example:
    ==============
    photo = ImageWithThumbsField(upload_to='images', sizes=((125,125),(300,200),)

    Ho-ho new cool feature: named sizes like:
        photo = ImageWithThumbsField(upload_to='images', sizes={'live': (125,125), 'profile': (300,200),})

    To retrieve image URL, exactly the same way as with ImageField:
        my_object.photo.url
    To retrieve thumbnails URL's just add the size to it:
        my_object.photo.url_125x125
        my_object.photo.url_300x200
        my_object.photo.url_profile

    Note: The 'sizes' attribute is not required. If you don't provide it,
    ImageWithThumbsField will act as a normal ImageField

    How it works:
    =============
    For each size in the 'sizes' atribute of the field it generates a
    thumbnail with that size and stores it following this format:

    available_filename.[width]x[height].extension

    Where 'available_filename' is the available filename returned by the storage
    backend for saving the original file.

    Following the usage example above: For storing a file called "photo.jpg" it saves:
    photo.jpg          (original file)
    photo.125x125.jpg  (first thumbnail)
    photo.300x200.jpg  (second thumbnail)

    With the default storage backend if photo.jpg already exists it will use these filenames:
    photo_.jpg
    photo_.125x125.jpg
    photo_.300x200.jpg

    Note: django-thumbs assumes that if filename "any_filename.jpg" is available
    filenames with this format "any_filename.[widht]x[height].jpg" will be available, too.

    """
    _size_format = '%sx%s'

    def set_sizes(self, sizes):
        """
        To unification, if sizes is not dict translate it to dict
        """
        if type(sizes) != types.DictType:
            sizes = dict([(self._size_format % size, size) for size in sizes])

        self.sizes = sizes

    def __init__(self, verbose_name=None, name=None, width_field=None, height_field=None, sizes=None, **kwargs):
        self.verbose_name=verbose_name
        self.name=name
        self.width_field=width_field
        self.height_field=height_field
        self.set_sizes(sizes)
        super(ImageField, self).__init__(**kwargs)

