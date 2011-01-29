from django.utils.translation import ugettext as _
from django.forms import util
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User

from core.fields import AdvEmailField


class BlockedPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        """
        Validates that a user exists with the given e-mail address
            and is not blocked.
        """
        email = self.cleaned_data['email']
        self.users_cache = User.objects.filter(email__iexact=email)
        if len(self.users_cache) == 0:
            raise util.ValidationError(_('That e-mail address doesn\'t have an associated user account. Are you sure you\'ve registered?'))
        elif self.users_cache[0].is_active == False:
            try:
                last_admin = User.objects.filter(
                    groups__permissions__codename='change_user'
                ).order_by('-date_joined')[0]
            except:
                admin_email = ''
            else:
                admin_email = last_admin.email
            from core.templatetags.email import email_encode
            admin_email = email_encode(admin_email)

            raise util.ValidationError(mark_safe(_(
                'Your account is blocked. Please, contact <a href="%s">administrator</a>.'
                    ) % (admin_email)
            ))


class AdvEmailPasswordResetForm(PasswordResetForm):
    email = AdvEmailField(label=_('E-mail'), max_length=75)


class SimpleFormSet(object):
    """
    allow_all_empty means that you allow don't fill all field, otherwise check that one field at least
    must be fill

    To render this form factory (formset in ex.):
    {% if formset|length %}
        {% for form in formset.get_forms %}
            {% render form%}
        {% endfor %}
    {% endif %}

    To save all forms, use formset.save(commit)

    To check valid use formset.is_valid()

    To get not form error, use formset.errors():
    {% if contact_forms.errors %}
        <div class="f_row">
            <ul class="errorlist">
            {% for error in contact_forms.errors %}
            <li>{{ error }}</li>
            {% endfor %}
            </ul>
        </div>
    {% endif %}
    """

    allow_classform = {}

    def __init__(self, formsclass_array=None, \
                        initial=None, allow_all_empty=False, *args, **kwargs):
        self._formset = []
        self._errors = []
        self.allow_all_empty = allow_all_empty
        self.formclass_array = formsclass_array
        self.initial = initial
        self._construct_forms(*args, **kwargs)

    def _construct_forms(self, *args, **kwargs):
        for form in self.allow_classform:
            if not self.formclass_array.has_key(form):
                continue
            for i in range(self.formclass_array[form]):
                cur_form = self.allow_classform[form]
                initial = None
                if self.initial and self.initial.has_key(form) and len(self.initial[form]) > i:
                    initial = self._get_initial_for_form(self.initial[form][i])
                self._formset.append(cur_form(initial=initial, prefix='%s%d' % (form, i), \
                                              *args, **kwargs))

    def _get_initial_for_form(self, initial):
        init = {}
        for field, value in initial:
            init.append({field: value})
        return init

    def _clean_not_empty_field(self, form):
        return True

    def _check_duplicate(self, form, have_duplicate):
        False

    def is_valid(self):
        have_not_empty = False
        have_duplicate = False
        failed = False
        for form in self._formset:
            if not form.is_valid():
                failed = True
            elif self._clean_not_empty_field(form):
                have_not_empty = True
                if not have_duplicate:
                    have_duplicate = self._check_duplicate(form, have_duplicate)
        if not failed and not self.allow_all_empty and not have_not_empty:
            self._errors.append(_('Please, fill in at least one of fields.'))
        if have_duplicate:
            self._errors.append(_('Some of fields are duplicated.'))
        return not failed and len(self._errors) == 0

    def _get_forms(self):
        return self._formset
    forms = property(_get_forms)

    def _get_errors(self):
        return self._errors if len(self._errors) else None
    errors = property(_get_errors)

    def save(self, commit=True):
        for form in self._formset:
            form.save(commit)

    def __len__(self):
        return len(self._formset)

