from decimal import Decimal

from django.db import migrations

MOSCOW_PARAGRAPH = (
    'В 1956–1958 годах Айтматов учился в Москве на Высших литературных курсах при Литературном институте '
    'имени А. М. Горького.'
)
OLD_REGION = 'Кыргызстан · вне карты России'
NEW_REGION = 'Кыргызстан · жил в Москве'


def place_in_moscow(apps, schema_editor):
    Author = apps.get_model('literature', 'Author')
    author = Author.objects.filter(slug='aitmatov', map_x__isnull=True, map_y__isnull=True).first()
    if author is None:
        return
    author.map_x = Decimal('16.00')
    author.map_y = Decimal('47.00')
    author.map_label_side = 'left'
    if author.region == OLD_REGION:
        author.region = NEW_REGION
    if MOSCOW_PARAGRAPH not in author.biography:
        first, _, rest = author.biography.partition('\n\n')
        author.biography = '\n\n'.join(part for part in (first, MOSCOW_PARAGRAPH, rest) if part)
    author.save()


def remove_from_moscow(apps, schema_editor):
    Author = apps.get_model('literature', 'Author')
    author = Author.objects.filter(slug='aitmatov').first()
    if author is None:
        return
    author.map_x = None
    author.map_y = None
    author.map_label_side = 'right'
    if author.region == NEW_REGION:
        author.region = OLD_REGION
    author.biography = author.biography.replace(f'\n\n{MOSCOW_PARAGRAPH}', '')
    author.save()


class Migration(migrations.Migration):
    dependencies = [
        ('literature', '0003_media_and_worksheets'),
    ]

    operations = [
        migrations.RunPython(place_in_moscow, remove_from_moscow),
    ]
