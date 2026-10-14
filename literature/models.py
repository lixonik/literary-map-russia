from pathlib import Path

from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import get_valid_filename

MATERIAL_CONTENT_TYPES = {
    'mp3': 'audio/mpeg',
    'm4a': 'audio/mp4',
    'aac': 'audio/aac',
    'wav': 'audio/wav',
    'ogg': 'audio/ogg',
    'mp4': 'video/mp4',
    'm4v': 'video/mp4',
    'mov': 'video/quicktime',
    'webm': 'video/webm',
}

PERCENT_VALIDATORS = [MinValueValidator(0), MaxValueValidator(100)]


class Grade(models.Model):
    number = models.PositiveSmallIntegerField(
        'класс', unique=True, validators=[MinValueValidator(1), MaxValueValidator(11)]
    )

    class Meta:
        ordering = ['number']
        verbose_name = 'класс'
        verbose_name_plural = 'классы'

    def __str__(self):
        return f'{self.number} класс'


class Author(models.Model):
    class LabelSide(models.TextChoices):
        RIGHT = 'right', 'справа от точки'
        LEFT = 'left', 'слева от точки'

    slug = models.SlugField('адрес страницы', unique=True, help_text='Латиницей, например: gamzatov')
    name = models.CharField('имя на сайте', max_length=120, help_text='Например: Расул Гамзатов')
    full_name = models.CharField('ФИО', max_length=200)
    summary = models.CharField('краткое описание', max_length=300, help_text='Показывается в карточке на главной')
    region = models.CharField('регион', max_length=120)
    birth_place = models.CharField('место рождения', max_length=200)
    birth_date = models.DateField('дата рождения')
    death_date = models.DateField('дата смерти', null=True, blank=True)
    tradition = models.CharField('литературная традиция', max_length=120)
    biography = models.TextField('биография', help_text='Абзацы разделяйте пустой строкой')
    significance = models.TextField('темы и значение творчества', blank=True)
    methodology = models.TextField(
        'текст методической разработки',
        blank=True,
        help_text='Абзацы разделяйте пустой строкой. Пока поле пустое, на странице автора показывается заготовка раздела',
    )
    research_question = models.CharField('вопрос для исследования', max_length=300, blank=True)
    grades = models.ManyToManyField(Grade, verbose_name='изучается в классах', related_name='authors', blank=True)
    map_label = models.CharField('подпись на карте', max_length=40)
    map_x = models.DecimalField(
        'точка на карте: X, %',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=PERCENT_VALIDATORS,
        help_text='Отступ от левого края контура в процентах. Оставьте пустым, если автора нет на карте',
    )
    map_y = models.DecimalField(
        'точка на карте: Y, %',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=PERCENT_VALIDATORS,
        help_text='Отступ от верхнего края контура в процентах',
    )
    map_label_side = models.CharField('сторона подписи', max_length=5, choices=LabelSide, default=LabelSide.RIGHT)
    position = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        ordering = ['position', 'name']
        verbose_name = 'автор'
        verbose_name_plural = 'авторы'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('author', kwargs={'slug': self.slug})

    @property
    def on_map(self):
        return self.map_x is not None and self.map_y is not None


class Work(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='works', verbose_name='автор')
    title = models.CharField('название', max_length=200, help_text='Без кавычек')
    position = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = 'ключевое произведение'
        verbose_name_plural = 'ключевые произведения'

    def __str__(self):
        return f'«{self.title}»'


class Material(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='materials', verbose_name='автор')
    title = models.CharField('название', max_length=200)
    description = models.TextField('описание', blank=True)
    file = models.FileField(
        'файл',
        upload_to='materials/%Y/%m/',
        validators=[FileExtensionValidator(list(MATERIAL_CONTENT_TYPES))],
        help_text='Аудио: mp3, m4a, aac, wav, ogg. Видео: mp4, m4v, mov, webm',
    )
    position = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = 'аудио- или видеоматериал'
        verbose_name_plural = 'аудио- и видеоматериалы'

    def __str__(self):
        return self.title

    @property
    def extension(self):
        return Path(self.file.name).suffix.lower().lstrip('.')

    @property
    def content_type(self):
        return MATERIAL_CONTENT_TYPES.get(self.extension, 'application/octet-stream')

    @property
    def is_video(self):
        return self.content_type.startswith('video/')

    @property
    def download_name(self):
        return get_valid_filename(f'{self.title}.{self.extension}')


@receiver(post_delete, sender=Material)
def delete_material_file(sender, instance, **kwargs):
    instance.file.delete(save=False)
