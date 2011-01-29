from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse, NoReverseMatch
from django.forms import forms, fields, widgets, models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from core.auth.utils import get_unique_username
from core.fields import AdvEmailField


class SimpleRegistrationForm(models.ModelForm):
    """
    Registration by email and password without confirm password
    """
    class Meta:
        fields = ('email', 'password')
        model= User

    def __init__(self, *args, **kwargs):
        super(SimpleRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the site.

        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).count():
            raise forms.ValidationError(_('User with this e-mail already exists.'))
        return self.cleaned_data['email']

    def save(self):
        # Create new user with unique email and encoded password.
        username = get_unique_username(self.cleaned_data['email'].partition('@')[0])
        new_user = User.objects.create_user(username,
                                            self.cleaned_data['email'],
                                            self.cleaned_data['password'])
        # Save additional fields in User
        new_user.save()


        return authenticate(username=self.cleaned_data['email'], password=self.cleaned_data['password'])


class RegistrationForm(SimpleRegistrationForm):
    """
    Registration by email and password WITH confirm password
    """
    confirmpassword = fields.CharField(
        max_length=30,
        label=_('Confirm password'),
        widget=widgets.PasswordInput(render_value=True),
        help_text=_('Repeat password.'))

    def clean(self):
        password = self.cleaned_data['password'] if 'password' in self.cleaned_data else None
        confirm = self.cleaned_data['confirmpassword'] if 'confirmpassword' in self.cleaned_data else None
        if password != confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        return self.cleaned_data


class AuthForm(forms.Form):
    email = AdvEmailField(max_length=75, label=_('Email'))
    password = fields.CharField(max_length=30, label=_('Password'),
            widget=widgets.PasswordInput(render_value=True))

    change_password_link = getattr(settings, 'CHANGE_PASSWORD_LINK_ON_WRONG_LOGIN', False)

    def get_user(self):
        return self.user
        
    def clean(self):
        if 'email' in self.cleaned_data and 'password' in self.cleaned_data:
            self.user = authenticate(username=self.cleaned_data['email'], password=self.cleaned_data['password'])
            if self.user is None:
                change_url = None
                if self.change_password_link:
                    try:
                        change_url = reverse('change_password')
                    except NoReverseMatch:
                        pass
                if change_url:
                    raise forms.ValidationError(mark_safe(
                        _('Wrong email or password. If you think you\'ve forgotten your credentials, you can <a href="%(url)s">change your password</a>.')
                            % {'url': change_url}
                    ))
                else:
                    raise forms.ValidationError(_('Wrong email or password.'))
            elif not self.user.is_active:
                    raise forms.ValidationError(_('Your account is blocked.'))
            else:
                return self.cleaned_data

