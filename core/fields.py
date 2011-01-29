import re

from django.utils.translation import ugettext_lazy as _
from django.forms import models, fields, util
from django.utils.encoding import smart_unicode
from django.template.defaultfilters import slugify

from core.models import FilteredModelChoiceIterator
from core.widgets import PhoneInput
from core.utils import parse_phone


def unique_slug(model, slug_field, slug_value, pk=None):
    orig_slug = slug = slugify(slug_value) or u'unknown'

    index = 0

    while True:
        try:
            model.objects.exclude(pk=pk).get(**{slug_field: slug})
            index += 1
            slug = orig_slug + '-' + str(index)
        except model.DoesNotExist:
            return slug


class FilteredSelectField(models.ModelChoiceField):
    def __init__(self, queryset, foreign_key, empty_label=u'---------',
                 cache_choices=False, required=True, widget=None, label=None,
                 initial=None, help_text=None, to_field_name=None,
                 *args, **kwargs):
        super(FilteredSelectField, self).__init__(
            queryset, empty_label=empty_label, cache_choices=cache_choices,
            required=required, widget=widget, label=label,
            initial=initial, help_text=help_text,
            to_field_name=to_field_name
        )
        self.foreign_key = foreign_key

    def _get_choices(self):
        return FilteredModelChoiceIterator(self)

    choices = property(_get_choices, fields.ChoiceField._set_choices)


class NoExecFileField(fields.FileField):
    """
    Blocks uploading of executable files.

    """
    blocked_extensions = ('com', 'exe', 'bat', 'cmd', 'vbs', 'vbe',
                          'js', 'jse', 'wsf', 'wsh')

    def clean(self, data, initial=None):
        super(NoExecFileField, self).clean(initial or data)
        if data != None:
            file_extension = data.name.split('.')[-1].lower()
            if file_extension in self.blocked_extensions:
                raise util.ValidationError(
                    _('You are not allowed to attach executable files.')
                )
        return data


class PhoneField(fields.CharField):
    default_error_messages = {
        'code_length': _('City code must be between 3 and 6 characters in length.'),
        'code_digits': _('City code should contain only digits.'),
        'number_length': _('Ensure you\'ve entered phone number.'),
    }

    def __init__(self, *args, **kwargs):
        if kwargs:
            kwargs.pop('widget', None)
        super(PhoneField, self).__init__(widget=PhoneInput(), *args, **kwargs)

    def clean(self, value):
        # First check if empty
        if value in fields.EMPTY_VALUES:
            if self.required:
                raise util.ValidationError(self.error_messages['required'])
            else:
                return super(PhoneField, self).clean(value)

        code, number = parse_phone(value)

        code_len = len(code)
        if code_len < 3 or code_len > 6:
            raise util.ValidationError(self.error_messages['code_length'])
        if not code.isdigit():
            raise util.ValidationError(self.error_messages['code_digits'])
        if len(number.strip()) == 0:
            raise util.ValidationError(self.error_messages['number_length'])

        return smart_unicode('(%s) %s' % (code, number))


class AdvEmailField(fields.EmailField):
    default_error_messages = {
        'wrong_symbol': _('Invalid symbol "%s" in e-mail address.'),
    }
    invalid_email_chars_re = re.compile(r"[^-!#$%&'*+/=?^_`{}|~0-9A-Z.@]", re.IGNORECASE)

    def clean(self, value):
        if value is None:
            return super(AdvEmailField,self).clean(value)
        value = value.strip()
        match = self.invalid_email_chars_re.search(value)
        if not match is None:
            try:
                message = self.error_messages['wrong_symbol'] % value[match.start()]
            except TypeError:
                message = self.error_messages['wrong_symbol']
            raise util.ValidationError(message)
        return super(AdvEmailField,self).clean(value)


class JabberField(AdvEmailField):
    default_error_messages = {
        'invalid': _(u'Enter a valid jabber id.'),
        'wrong_symbol': _('Invalid symbol "%s" in jabber id.'),
    }


class SkypeField(fields.CharField):
    default_error_messages = {
        'wrong_symbol': _('Invalid symbol "%s" in skype name.'),
    }
    invalid_skype_chars_re = re.compile(r"[^0-9A-Z.]", re.IGNORECASE)

    def clean(self, value):
        if value is None:
            return super(SkypeField, self).clean(value)
        value = value.strip()
        match = self.invalid_skype_chars_re.search(value)
        if not match is None:
            try:
                message = self.error_messages['wrong_symbol'] % value[match.start()]
            except TypeError:
                message = self.error_messages['wrong_symbol']
            raise util.ValidationError(message)
        return super(SkypeField,self).clean(value)

