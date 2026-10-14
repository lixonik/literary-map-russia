from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import get_valid_filename

from .storage import ProtectedStorage
from .vk import normalize_vk_embed

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

METHODOLOGY_FILE_EXTENSIONS = ['pdf', 'doc', 'docx', 'odt', 'rtf', 'ppt', 'pptx']

PERCENT_VALIDATORS = [MinValueValidator(0), MaxValueValidator(100)]


def delete_stored_files(instance, *field_names):
    for field_name in field_names:
        stored_file = getattr(instance, field_name)
        if stored_file:
            stored_file.delete(save=False)


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
    portrait = models.ImageField('портрет', upload_to='portraits/', blank=True)
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
        help_text='Абзацы разделяйте пустой строкой. Пока нет ни текста, ни файла, на странице автора показывается заготовка раздела',
    )
    methodology_file = models.FileField(
        'файл методической разработки',
        upload_to='methodology/',
        blank=True,
        validators=[FileExtensionValidator(METHODOLOGY_FILE_EXTENSIONS)],
        help_text='PDF, Word, PowerPoint. Можно вместо текста или вместе с ним. Открывается всем посетителям',
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

    @property
    def methodology_file_extension(self):
        return Path(self.methodology_file.name).suffix.lstrip('.').upper()

    @property
    def methodology_file_size(self):
        try:
            return self.methodology_file.size
        except OSError:
            return None


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


class Worksheet(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='worksheets', verbose_name='автор')
    image = models.ImageField('изображение', upload_to='worksheets/')
    title = models.CharField('подпись', max_length=200, blank=True)
    position = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = 'рабочий лист'
        verbose_name_plural = 'рабочие листы'

    def __str__(self):
        return self.title or f'Рабочий лист {self.pk}'


class Material(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='materials', verbose_name='автор')
    title = models.CharField('название', max_length=200)
    description = models.TextField('описание', blank=True)
    file = models.FileField(
        'файл',
        upload_to='materials/%Y/%m/',
        storage=ProtectedStorage(),
        blank=True,
        validators=[FileExtensionValidator(list(MATERIAL_CONTENT_TYPES))],
        help_text='Аудио: mp3, m4a, aac, wav, ogg. Видео: mp4, m4v, mov, webm. Скачивают только зарегистрированные',
    )
    vk_video = models.CharField(
        'видео ВКонтакте',
        max_length=1000,
        blank=True,
        help_text=(
            'Вместо файла: ссылка на видео ВКонтакте или код для встраивания (правый клик по видео, «Копировать код для встраивания»). '
            'Видео должно быть открытым'
        ),
    )
    position = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        ordering = ['position', 'id']
        verbose_name = 'аудио- или видеоматериал'
        verbose_name_plural = 'аудио- и видеоматериалы'

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.vk_video:
            try:
                self.vk_video = normalize_vk_embed(self.vk_video)
            except ValidationError as error:
                raise ValidationError({'vk_video': error.messages})
        if bool(self.file) == bool(self.vk_video):
            raise ValidationError('Загрузите файл или вставьте видео ВКонтакте: нужно что-то одно.')

    @property
    def is_vk(self):
        return bool(self.vk_video)

    @property
    def extension(self):
        return Path(self.file.name).suffix.lower().lstrip('.')

    @property
    def content_type(self):
        return MATERIAL_CONTENT_TYPES.get(self.extension, 'application/octet-stream')

    @property
    def is_video(self):
        return self.is_vk or self.content_type.startswith('video/')

    @property
    def download_name(self):
        return get_valid_filename(f'{self.title}.{self.extension}')


@receiver(post_delete, sender=Author)
def delete_author_files(sender, instance, **kwargs):
    delete_stored_files(instance, 'portrait', 'methodology_file')


@receiver(post_delete, sender=Worksheet)
def delete_worksheet_image(sender, instance, **kwargs):
    delete_stored_files(instance, 'image')


@receiver(post_delete, sender=Material)
def delete_material_file(sender, instance, **kwargs):
    delete_stored_files(instance, 'file')
