from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, BaseUserCreationForm, UserChangeForm

from .models import User


class RegistrationForm(BaseUserCreationForm):
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

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже зарегистрирован.')
        return email


class AdminCreationForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'full_name')


class AdminChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
