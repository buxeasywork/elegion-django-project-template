from itertools import chain

from django.forms import widgets
from django.utils.dates import MONTHS
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe

from core.templatetags.media import media
from core.utils import parse_phone


class FilteredSelect(widgets.Select):
    """
    Renders select in the format:
        <select ...>
            <option class="filter_{foreign_key_id}" value="...">...</option>
        </select>
    """
    def __init__(self, attrs=None, choices=()):
        super(FilteredSelect, self).__init__(attrs, choices)

    def render_options(self, choices, selected_choices):
        def render_option(option_value, option_label, filter_key):
            option_value = force_unicode(option_value)
            selected_html = (option_value in selected_choices) \
                and u' selected="selected"' or ''
            return u'<option class="filter_%s" value="%s"%s>%s</option>' % (
                filter_key,
                escape(option_value),
                selected_html,
                conditional_escape(force_unicode(option_label))
            )

        # Normalize to strings.
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []

        for option_value, option_label, filter_key in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' % escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(render_option(*option))
                output.append(u'</optgroup>')
            else:
                output.append(render_option(option_value, option_label,
                                            filter_key))
        return u'\n'.join(output)


class PhoneInput(widgets.TextInput):
    def value_from_datadict(self, data, files, name):
        number = data.get(name, None)
        code = data.get('%s_code' % name, None)
        if not number:
            return ''
        if code:
            number = '(%s) %s' % (code, number)
        return number

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''

        code, number = parse_phone(value)

        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        final_attrs_code = final_attrs.copy()
        final_attrs_code['name'] += '_code'
        final_attrs_code['id'] += '_code'
        final_attrs_code['maxlength'] = '6'
        if 'class' not in final_attrs_code:
            final_attrs_code['class'] = 'PhoneCode'
        else:
            final_attrs_code['class'] += ' PhoneCode'

        code_input = super(PhoneInput, self).render(None, force_unicode(code), final_attrs_code)
        number_input = super(PhoneInput, self).render(None, force_unicode(number), final_attrs)

        return mark_safe(u'<span class="country_code">+7</span><span class="phone_left_parenthesis">(</span>' \
                          '%s' \
                          '<span class="phone_right_parenthesis">)</span>' \
                          '\n%s' % (code_input, number_input))

    @classmethod
    def id_for_label(self, id_):
        return '%s_code' % str(id_)


class AddressWithMapInput(widgets.TextInput):
    def __init__(self, canvas_id, companion_fields, *args, **kwargs):
        super(AddressWithMapInput, self).__init__(*args, **kwargs)
        self.canvas_id = canvas_id
        self.companion_fields = companion_fields

    def render(self, name, value, attrs=None):
        self_id = '#id_%s' % name
        maps_js = media('js/maps.js')
        fields = [self_id, ]
        for field_name in self.companion_fields:
            fields.append('#id_%s' % field_name)
        fields = '[%s]' % ','.join(('\'%s\'' % field_name for field_name in fields))
        my_html = '<script type="text/javascript" src="%(maps_js)s"></script>'\
                  '<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>'\
                  '<script type="text/javascript">'\
                  '$(function() {'\
                      'var addressLocationMap = new CondoSite.MapLocator(\'#%(canvas_id)s\');'\
                      'addressLocationMap.initialBySelector(\'%(id)s\', %(fields)s);'\
                  '});</script>'\
                  '<div id="%(canvas_id)s"></div>' % {'maps_js': maps_js, 'canvas_id': self.canvas_id,
                                                      'id': self_id, 'fields': fields}
        html = super(AddressWithMapInput, self).render(name, value, attrs)
        return mark_safe(''.join((html, '<br />', my_html)))


class SplitDateWidget(widgets.Widget):
    """
    A Widget that splits date input into three inputs:
        select for month and text inputs for day and month.
    """
    none_value = (0, '')
    month_field = '%s_month'
    day_field = '%s_day'
    year_field = '%s_year'

    def __init__(self, *args, **kwargs):
        super(SplitDateWidget, self).__init__(*args, **kwargs)
        self.required = kwargs.get('required', False)

    def render(self, name, value, attrs=None):
        try:
            year_val, month_val, day_val = value.year, value.month, value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, basestring):
                parts = value.split('-', 2)
                count = len(parts)
                if count < 3:
                    parts[count:2] = [None] * 3 - count
                year_val, month_val, day_val = parts

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        def add_class(attrs, className):
            if 'class' in attrs:
                attrs['class'] += ' %s' % className
            else:
                attrs['class'] = className
            return attrs

        # TODO: add fields order customization
        month_choices = MONTHS.items()
        if not (self.required and value):
            month_choices.append(self.none_value)
        month_choices.sort()
        local_attrs = self.build_attrs(id=self.month_field % id_)
        add_class(local_attrs, 'DateMonth')
        s = widgets.Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)

        local_attrs = self.build_attrs(id=self.day_field % id_)
        add_class(local_attrs, 'DateDay')
        s = widgets.TextInput()
        select_html = s.render(self.day_field % name, day_val, local_attrs)
        output.append(select_html)

        local_attrs = self.build_attrs(id=self.year_field % id_)
        add_class(local_attrs, 'DateYear')
        s = widgets.TextInput()
        select_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(select_html)

        return mark_safe(u'\n'.join(output))

    @classmethod
    def id_for_label(self, id_):
        return self.month_field % id_

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == d == '' and m == '0':
            return None
        if y and m and d:
            return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)

