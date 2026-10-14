import django.core.validators
import django.db.models.deletion
import literature.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('literature', '0002_initial_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='methodology_file',
            field=models.FileField(blank=True, help_text='PDF, Word, PowerPoint. Можно вместо текста или вместе с ним. Открывается всем посетителям', upload_to='methodology/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'doc', 'docx', 'odt', 'rtf', 'ppt', 'pptx'])], verbose_name='файл методической разработки'),
        ),
        migrations.AddField(
            model_name='author',
            name='portrait',
            field=models.ImageField(blank=True, upload_to='portraits/', verbose_name='портрет'),
        ),
        migrations.AddField(
            model_name='material',
            name='vk_video',
            field=models.CharField(blank=True, help_text='Вместо файла: ссылка на видео ВКонтакте или код для встраивания (правый клик по видео, «Копировать код для встраивания»). Видео должно быть открытым', max_length=1000, verbose_name='видео ВКонтакте'),
        ),
        migrations.AlterField(
            model_name='author',
            name='methodology',
            field=models.TextField(blank=True, help_text='Абзацы разделяйте пустой строкой. Пока нет ни текста, ни файла, на странице автора показывается заготовка раздела', verbose_name='текст методической разработки'),
        ),
        migrations.AlterField(
            model_name='material',
            name='file',
            field=models.FileField(blank=True, help_text='Аудио: mp3, m4a, aac, wav, ogg. Видео: mp4, m4v, mov, webm. Скачивают только зарегистрированные', storage=literature.storage.ProtectedStorage(), upload_to='materials/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(['mp3', 'm4a', 'aac', 'wav', 'ogg', 'mp4', 'm4v', 'mov', 'webm'])], verbose_name='файл'),
        ),
        migrations.CreateModel(
            name='Worksheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='worksheets/', verbose_name='изображение')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='подпись')),
                ('position', models.PositiveSmallIntegerField(default=0, verbose_name='порядок')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='worksheets', to='literature.author', verbose_name='автор')),
            ],
            options={
                'verbose_name': 'рабочий лист',
                'verbose_name_plural': 'рабочие листы',
                'ordering': ['position', 'id'],
            },
        ),
    ]
