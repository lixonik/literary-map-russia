from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import AdminChangeForm, AdminCreationForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AdminChangeForm
    add_form = AdminCreationForm
    ordering = ('email',)
    list_display = ('email', 'full_name', 'workplace', 'is_staff', 'date_joined')
    search_fields = ('email', 'full_name', 'workplace', 'research_interests')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Профиль', {'fields': ('full_name', 'workplace', 'research_interests')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'usable_password', 'password1', 'password2'),
        }),
    )
