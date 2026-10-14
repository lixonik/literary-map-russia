from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse

from .models import Author, Material, Work, Worksheet

admin.site.site_header = 'Литературная карта народов России'
admin.site.site_title = 'Литературная карта'
admin.site.index_title = 'Содержимое сайта'


class StreamLink:
    def __init__(self, field_file):
        self.name = field_file.name
        self.url = reverse('material-stream', kwargs={'pk': field_file.instance.pk})

    def __str__(self):
        return self.name


class ProtectedFileInput(forms.ClearableFileInput):
    def is_initial(self, value):
        return bool(value and getattr(value, 'name', '') and getattr(value.instance, 'pk', None))

    def format_value(self, value):
        if self.is_initial(value):
            return StreamLink(value)
        return None


PROTECTED_FILE_WIDGET = {models.FileField: {'widget': ProtectedFileInput}}


class WorkInline(admin.TabularInline):
    model = Work
    extra = 1


class WorksheetInline(admin.TabularInline):
    model = Worksheet
    extra = 0
    fields = ('image', 'title', 'position')


class MaterialInline(admin.StackedInline):
    model = Material
    extra = 0
    fields = ('title', 'description', 'file', 'vk_video', 'position')
    formfield_overrides = PROTECTED_FILE_WIDGET


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'birth_date', 'is_on_map', 'position')
    list_editable = ('position',)
    list_filter = ('grades',)
    search_fields = ('name', 'full_name', 'region')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (WorkInline, WorksheetInline, MaterialInline)
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'full_name', 'summary', 'portrait', 'position')}),
        ('Биография', {'fields': (
            'birth_date', 'death_date', 'birth_place', 'region', 'tradition', 'biography', 'significance',
        )}),
        ('Методическая разработка', {'fields': ('methodology', 'methodology_file', 'research_question', 'grades')}),
        ('Карта', {'fields': ('map_label', 'map_x', 'map_y', 'map_label_side')}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in ('map_x', 'map_y'):
            kwargs['localize'] = True
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'grades':
            kwargs['widget'] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(boolean=True, description='на карте')
    def is_on_map(self, author):
        return author.on_map


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_video')
    formfield_overrides = PROTECTED_FILE_WIDGET
    list_filter = ('author',)
    search_fields = ('title', 'author__name')

    @admin.display(boolean=True, description='видео')
    def is_video(self, material):
        return material.is_video
