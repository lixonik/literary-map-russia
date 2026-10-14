import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField(unique=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(11)], verbose_name='класс')),
            ],
            options={
                'verbose_name': 'класс',
                'verbose_name_plural': 'классы',
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text='Латиницей, например: gamzatov', unique=True, verbose_name='адрес страницы')),
                ('name', models.CharField(help_text='Например: Расул Гамзатов', max_length=120, verbose_name='имя на сайте')),
                ('full_name', models.CharField(max_length=200, verbose_name='ФИО')),
                ('summary', models.CharField(help_text='Показывается в карточке на главной', max_length=300, verbose_name='краткое описание')),
                ('region', models.CharField(max_length=120, verbose_name='регион')),
                ('birth_place', models.CharField(max_length=200, verbose_name='место рождения')),
                ('birth_date', models.DateField(verbose_name='дата рождения')),
                ('death_date', models.DateField(blank=True, null=True, verbose_name='дата смерти')),
                ('tradition', models.CharField(max_length=120, verbose_name='литературная традиция')),
                ('biography', models.TextField(help_text='Абзацы разделяйте пустой строкой', verbose_name='биография')),
                ('significance', models.TextField(blank=True, verbose_name='темы и значение творчества')),
                ('methodology', models.TextField(blank=True, help_text='Абзацы разделяйте пустой строкой. Пока поле пустое, на странице автора показывается заготовка раздела', verbose_name='текст методической разработки')),
                ('research_question', models.CharField(blank=True, max_length=300, verbose_name='вопрос для исследования')),
                ('map_label', models.CharField(max_length=40, verbose_name='подпись на карте')),
                ('map_x', models.DecimalField(blank=True, decimal_places=2, help_text='Отступ от левого края контура в процентах. Оставьте пустым, если автора нет на карте', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='точка на карте: X, %')),
                ('map_y', models.DecimalField(blank=True, decimal_places=2, help_text='Отступ от верхнего края контура в процентах', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='точка на карте: Y, %')),
                ('map_label_side', models.CharField(choices=[('right', 'справа от точки'), ('left', 'слева от точки')], default='right', max_length=5, verbose_name='сторона подписи')),
                ('position', models.PositiveSmallIntegerField(default=0, verbose_name='порядок')),
                ('grades', models.ManyToManyField(blank=True, related_name='authors', to='literature.grade', verbose_name='изучается в классах')),
            ],
            options={
                'verbose_name': 'автор',
                'verbose_name_plural': 'авторы',
                'ordering': ['position', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='название')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
                ('file', models.FileField(help_text='Аудио: mp3, m4a, aac, wav, ogg. Видео: mp4, m4v, mov, webm', upload_to='materials/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['mp3', 'm4a', 'aac', 'wav', 'ogg', 'mp4', 'm4v', 'mov', 'webm'])], verbose_name='файл')),
                ('position', models.PositiveSmallIntegerField(default=0, verbose_name='порядок')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='literature.author', verbose_name='автор')),
            ],
            options={
                'verbose_name': 'аудио- или видеоматериал',
                'verbose_name_plural': 'аудио- и видеоматериалы',
                'ordering': ['position', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Без кавычек', max_length=200, verbose_name='название')),
                ('position', models.PositiveSmallIntegerField(default=0, verbose_name='порядок')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='works', to='literature.author', verbose_name='автор')),
            ],
            options={
                'verbose_name': 'ключевое произведение',
                'verbose_name_plural': 'ключевые произведения',
                'ordering': ['position', 'id'],
            },
        ),
    ]
