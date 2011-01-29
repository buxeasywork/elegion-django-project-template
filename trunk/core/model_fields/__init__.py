# encoding: utf-8
import mimetypes

from django.db import models
from django.db.models import fields, OneToOneField
from django.db.models.fields import files
from django.db.models.fields.related import SingleRelatedObjectDescriptor 
from django.conf import settings
from django.utils.encoding import smart_unicode

from core import fields as core_fields

# import from inner files
# usage example: from core.model_fields import ImageWithThumbsCode
from core.model_fields.imagewiththumbs import ImageWithThumbsField


class FieldFileMimetype(files.FieldFile):
    mimetypes.init()
    mimetypes.add_type('application/msword', '.docx')
    mimetypes.add_type('application/vnd.ms-excel', '.xlsx')

    def mimetype(self):
        type = mimetypes.guess_type(self.path)[0]
        if type == None:
            return 'generic'
        return type.replace('/', '-')

    def _get_size(self):
        try:
            return super(FieldFileMimetype, self)._get_size()
        except:
            return 0
    size = property(_get_size)


class MimetypeFileField(files.FileField):
    attr_class = FieldFileMimetype


class NoExecFileField(MimetypeFileField):
    def formfield(self, **kwargs):
        defaults = {'form_class': core_fields.NoExecFileField}
        # If a file has been provided previously, then the form doesn't require
        # that a new file is provided this time.
        # The code to mark the form field as not required is used by
        # form_for_instance, but can probably be removed once form_for_instance
        # is gone. ModelForm uses a different method to check for an existing file.
        if 'initial' in kwargs:
            defaults['required'] = False
        defaults.update(kwargs)
        return super(NoExecFileField, self).formfield(**defaults)


class PhoneField(fields.CharField):
    def formfield(self, **kwargs):
        defaults = {'form_class': core_fields.PhoneField}
        defaults.update(kwargs)
        return super(fields.CharField, self).formfield(**defaults)


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^core\.model_fields\.PhoneField"])
add_introspection_rules([], ["^core\.model_fields\.MimetypeFileField"])


class BinValueField(models.Field):
    """ @brief stores raw binary data """
    
    def db_type(self):        
        return "VARBINARY(%s)" % self.max_length
    
    def get_db_prep_value(self, value):
        #print ['\\%03o' % ord(c) for c in value]
        return value and ''.join(['%02x' % ord(c) for c in value])+"" or None
        #return unicode(value)

    def get_placeholder(self, value):
        return value and r'x%s' or '%s'


class CryptedFieldBase(BinValueField):
    """ @brief stores AES-encoded data in DB """
    prefix = 'AES$'

    def db_type(self):
        return "BLOB"
#        if self.max_length:
#            # 16 - AES block length
#            return "VARBINARY(%s)" % (self.max_length + 16 + len(self.prefix) )
#        else:
#            return "BLOB"

    def to_python(self, value):
        if value.startswith(self.prefix):
            # We can get exception if user tryes save string like
            # 'AES$' + 'NOT AES-crypted data'
            # (who the f**k will do this?!)
            # Anyway user will not be able to save valid crypted string -
            # it'll be decrypted and saved
            try:
                from core.crypt import mysql_AES_decrypt
                val = mysql_AES_decrypt(
                        value[len(self.prefix):],
                        settings.SECRET_KEY[:16])
                return smart_unicode(val) # exception UnicodeDecodeError
            except UnicodeDecodeError:
                pass
        return smart_unicode(value)

    def get_db_prep_value(self, value):
        from core.crypt import mysql_AES_encrypt

        if isinstance(value, unicode):
            value = value.encode('utf-8')
        value = mysql_AES_encrypt(
            value,
            settings.SECRET_KEY[:16]
        )
        value = ''.join((self.prefix,value))
        return super(CryptedFieldBase,self).get_db_prep_value(value)

class CryptedField(CryptedFieldBase):
    __metaclass__ = models.SubfieldBase

class BigCryptedField(CryptedFieldBase, fields.TextField):
    __metaclass__ = models.SubfieldBase
    
class CryptedPhoneField(CryptedFieldBase, PhoneField):
    __metaclass__ = models.SubfieldBase

#    def formfield(self, **kwargs):
#        defaults = {'form_class': core_fields.PhoneField}
#        defaults.update(kwargs)
#        return super(CryptedPhoneField, self).formfield(**defaults)


class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor): # this line just can't be too long, right?
  def __get__(self, instance, instance_type=None):
    try:
      return super(AutoSingleRelatedObjectDescriptor, self).__get__(instance, instance_type)
    except self.related.model.DoesNotExist:
      obj = self.related.model(**{self.related.field.name: instance})
      obj.save()
      return obj


class AutoOneToOneField(OneToOneField):
  '''
  OneToOneField, которое создает зависимый объект при первом обращении
  из родительского, если он еще не создан.
  
  http://softwaremaniacs.org/blog/2007/03/07/auto-one-to-one-field/
  '''
  def contribute_to_related_class(self, cls, related):
    setattr(cls, related.get_accessor_name(), AutoSingleRelatedObjectDescriptor(related))
    # AL, I dont know goal of below lines
    if not hasattr(cls, "_meta.one_to_one_field"):
        cls._meta.one_to_one_field = self

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^core\.model_fields\.AutoOneToOneField"])