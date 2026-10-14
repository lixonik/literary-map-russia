import django.db.models.functions.text
from django.db import migrations, models
from django.db.models.functions import Lower


def lowercase_emails(apps, schema_editor):
    apps.get_model('accounts', 'User').objects.update(email=Lower('email'))


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(error_messages={'unique': 'Пользователь с такой почтой уже зарегистрирован.'}, max_length=254, unique=True, verbose_name='электронная почта'),
        ),
        migrations.RunPython(lowercase_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('email'), name='unique_user_email_case_insensitive', violation_error_message='Пользователь с такой почтой уже зарегистрирован.'),
        ),
    ]
