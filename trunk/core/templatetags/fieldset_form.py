from django.template import Library
from django.forms import widgets

from core.utils import add_field_class_names


register = Library()


def get_dl_fields_html(fields, f, show_notes=True):
    fields_html = ['<dl class="form">']
    for field_name in fields:
        field = f[field_name]
        help_text = ''
        errors = ''
        if field.is_hidden:
            fields_html.append(unicode(field))
        else:
            if show_notes and field.help_text:
                help_text = u'\n\t\t<div class="notes">%s</div>' % field.help_text

            if f[field_name].errors:
                errors = '<div class="error">%s</div>' % f[field_name].errors.as_ul()
            css_class_name = '%s%s' % (field_name, ' error_field' if errors else '')

            if issubclass(f[field_name].field.widget.__class__, widgets.CheckboxInput):
                fields_html.append('<dt class="%s"></dt><dd class="%s"><div class="f_row">%s %s %s</div>%s</dd>'
                    % (css_class_name, css_class_name, unicode(field), unicode(field.label_tag()), errors, help_text))
            elif getattr(f[field_name].field.widget, "input_type", None) or \
            issubclass(f[field_name].field.widget.__class__, widgets.Select):
                fields_html.append('<dt class="%s">%s</dt><dd class="%s"><div class="f_row">%s%s</div>%s</dd>'
                    % (css_class_name, unicode(field.label_tag()), css_class_name, unicode(field), errors, help_text))
            else:
                fields_html.append('<dt class="%s">%s</dt><dd class="%s"><div class="f_row">%s%s</div>%s</dd>'
                    % (css_class_name, unicode(field.label_tag()), css_class_name, unicode(field), errors, help_text))
    fields_html.append('</dl>')
    return ''.join(fields_html)


def get_fields_html(fields, f, show_notes=True):
    fields_html = []
    for field_name in fields:
        field = f[field_name]
        help_text = ''
        errors = ''

        if show_notes and field.help_text:
            help_text = u'\n\t\t<div class="notes">%s</div>' % field.help_text

        if f[field_name].errors:
            errors = unicode(f[field_name].errors)

        fields_html.append(u'<div class="f_row %s">\n\t%s\n\t<label for="id_%s">' \
                           '%s</label>\n\t<div class="f_input">' \
                           '\n\t\t%s%s\n\t</div>\n</div>\n'
                           % (field_name, errors, field.html_name, field.label, unicode(field), help_text))
    return ''.join(fields_html)


@register.simple_tag
def render_form(form, show_notes='True', form_type='simple', fieldsets=''):
    """
    Renders a form.

    If show_notes is 'False': notes for field is not show in

    If form_type is 'custom' form will render such as:
    <dl class="form">
        <div class="input_container FIELD_NAME">
            <dt>label</dt>
            <dd>field</dt>
        </div>
    </dl>

    Usage:
        {% render_form form %}
        {% render_form form 'False' %}
        {% render_form form 'False' 'custom' %}

    Note: Tag library must be loaded. Do this by writing
        {% load fieldset_form %}
    in your template.

    """

    add_field_class_names(form)

    show_notes = show_notes == 'True'
    fieldsets = fieldsets.split()
    
    if hasattr(form, 'fieldsets'):        
        fieldset_template_legend = u'<fieldset class="%(fieldset_class)s">' \
                                    '<legend>%(legend)s</legend>\n' \
                                    '%(fields)s\n</fieldset>\n'
        fieldset_template = u'<fieldset class="%(fieldset_class)s">\n' \
                             '%(fields)s\n</fieldset>\n'

        form_html = []
        for fieldset in form.fieldsets:
            if fieldsets and fieldset[1].get('class', None) and not fieldset[1].get('class', None) in fieldsets:
                continue
            context = {}
            context['legend'] = fieldset[0]
            if form_type == 'custom':
                context['fields'] = get_dl_fields_html(fieldset[1]['fields'], form, show_notes)
            else:
                context['fields'] = get_fields_html(fieldset[1]['fields'], form, show_notes)
            context['fieldset_class'] = fieldset[1]['class'] if 'class' in fieldset[1] else ''
            html = fieldset[0] and fieldset_template_legend or fieldset_template
            form_html.append(html % context)
        return ''.join(form_html)
    else:
        fields = form.fields.keys()
        if form_type == 'custom':
            return get_dl_fields_html(fields, form, show_notes)
        return get_fields_html(fields, form, show_notes)

