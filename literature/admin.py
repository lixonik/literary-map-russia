from django import forms
from django.contrib import admin

from .models import Author, Material, Work

admin.site.site_header = 'Литературная карта народов России'
admin.site.site_title = 'Литературная карта'
admin.site.index_title = 'Содержимое сайта'


class WorkInline(admin.TabularInline):
    model = Work
    extra = 1


class MaterialInline(admin.StackedInline):
    model = Material
    extra = 0


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'birth_date', 'is_on_map', 'position')
    list_editable = ('position',)
    list_filter = ('grades',)
    search_fields = ('name', 'full_name', 'region')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (WorkInline, MaterialInline)
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'full_name', 'summary', 'position')}),
        ('Биография', {'fields': (
            'birth_date', 'death_date', 'birth_place', 'region', 'tradition', 'biography', 'significance',
        )}),
        ('Методическая разработка', {'fields': ('methodology', 'research_question', 'grades')}),
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
    list_filter = ('author',)
    search_fields = ('title', 'author__name')

    @admin.display(boolean=True, description='видео')
    def is_video(self, material):
        return material.is_video
