from django import forms
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    BaseUserCreationForm,
    UserChangeForm,
)

from .models import DUPLICATE_EMAIL_MESSAGE, User


class EmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Неверная электронная почта или пароль.',
    }


class UniqueEmailMixin:
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        duplicates = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError(DUPLICATE_EMAIL_MESSAGE)
        return email


class RegistrationForm(UniqueEmailMixin, BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('full_name', 'email', 'workplace', 'research_interests')
        widgets = {'research_interests': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['workplace'].required = True
        self.fields['research_interests'].required = True
        self.fields['email'].widget.attrs.pop('autofocus', None)
        self.fields['full_name'].widget.attrs['autofocus'] = True


class AdminCreationForm(UniqueEmailMixin, AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'full_name')


class AdminChangeForm(UniqueEmailMixin, UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
