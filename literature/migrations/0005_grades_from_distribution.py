import datetime
from decimal import Decimal

from django.db import migrations

GRADES = {
    'gamzatov': [4, 5, 6, 11],
    'karim': [5, 6, 11],
    'kuliev': [6, 11],
    'tukay': [6, 10],
    'aigi': [11],
    'aitmatov': [11],
    'jalil': [11],
    'kugultinov': [11],
    'rytkeu': [11],
    'shestalov': [11],
}

PREVIOUS_GRADES = {
    'gamzatov': [5, 6],
    'karim': [5, 6],
    'kuliev': [6],
    'tukay': [6],
}

EXTRA_WORKS = {
    'aitmatov': ['Белый пароход'],
    'tukay': ['Книга'],
    'kuliev': ['Что б ни делалось на свете…'],
}

NEW_AUTHORS = [
    {
        'slug': 'akmulla',
        'name': 'Акмулла',
        'full_name': 'Камалетдинов Мифтахетдин Камалетдинович',
        'summary': 'Поэт-просветитель и мыслитель, призывавший народ к знаниям.',
        'region': 'Республика Башкортостан',
        'birth_place': 'деревня Туксанбаево, Оренбургская губерния',
        'birth_date': datetime.date(1831, 12, 26),
        'death_date': datetime.date(1895, 10, 20),
        'tradition': 'Башкирская, татарская и казахская литература',
        'biography': (
            'Акмулла — литературное имя Мифтахетдина Камалетдинова, поэта, просветителя и мыслителя. Он родился '
            'в деревне Туксанбаево, ныне Миякинский район Башкортостана.\n\n'
            'Чтобы уклониться от многолетней военной службы, он ушёл к казахам; там его и стали называть Акмуллой. '
            'Позже он учительствовал в Петропавловске и в Акмолинской области.\n\n'
            'В 1867–1871 годах Акмулла был заключён в Троицкую тюрьму, где написал стихотворение «Место моё — '
            'в зиндане». В 1895 году он был убит по дороге из Троицка в Златоуст.'
        ),
        'significance': (
            'Исследователи по-разному определяют язык его стихов: башкирские учёные считают, что он писал в основном '
            'на башкирском и казахском, а исследователи старотатарской литературы называют его язык смешанным '
            'казахско-татарским. Его творчество входит сразу в несколько литературных традиций.'
        ),
        'research_question': 'Как в стихах Акмуллы звучит призыв к знанию и просвещению?',
        'works': ['Башкиры мои, надо учиться!', 'Место моё — в зиндане', 'Назидания'],
        'grades': [10],
        'map_label': 'Акмулла',
        'map_x': '42.50',
        'map_y': '53.50',
        'map_label_side': 'right',
    },
    {
        'slug': 'khetagurov',
        'name': 'Коста Хетагуров',
        'full_name': 'Хетагуров Коста Леванович',
        'summary': 'Осетинский поэт, драматург и художник, основоположник осетинской литературы.',
        'region': 'Республика Северная Осетия — Алания',
        'birth_place': 'село Нар, Терская область',
        'birth_date': datetime.date(1859, 10, 15),
        'death_date': datetime.date(1906, 4, 1),
        'tradition': 'Осетинская и русская литература',
        'biography': (
            'Коста Хетагуров родился в горном селе Нар. Он писал на осетинском и русском языках, был поэтом, '
            'драматургом, публицистом, этнографом и живописцем.\n\n'
            'В 1881 году он поступил в Петербургскую академию художеств, но в 1883 году был исключён из-за '
            'прекращения выплаты стипендии.\n\n'
            'В 1899 году во Владикавказе вышел его сборник стихотворений на осетинском языке «Осетинская лира» '
            '(«Ирон фæндыр»).'
        ),
        'significance': 'Хетагурова считают основоположником осетинской литературы.',
        'research_question': 'Какие темы и образы объединяют стихотворения сборника «Осетинская лира»?',
        'works': ['Осетинская лира', 'Фатима', 'Хетаг'],
        'grades': [10],
        'map_label': 'Хетагуров',
        'map_x': '21.00',
        'map_y': '85.50',
        'map_label_side': 'right',
    },
]


def apply_distribution(apps, schema_editor):
    Author = apps.get_model('literature', 'Author')
    Grade = apps.get_model('literature', 'Grade')
    Work = apps.get_model('literature', 'Work')
    grades = {grade.number: grade for grade in Grade.objects.all()}

    for slug, numbers in GRADES.items():
        author = Author.objects.filter(slug=slug).first()
        if author is not None:
            author.grades.add(*(grades[number] for number in numbers))

    for slug, titles in EXTRA_WORKS.items():
        author = Author.objects.filter(slug=slug).first()
        if author is None:
            continue
        existing = set(author.works.values_list('title', flat=True))
        position = author.works.count()
        for title in titles:
            if title not in existing:
                position += 1
                Work.objects.create(author=author, title=title, position=position)

    next_position = (Author.objects.order_by('-position').values_list('position', flat=True).first() or 0) + 1
    for offset, data in enumerate(NEW_AUTHORS):
        if Author.objects.filter(slug=data['slug']).exists():
            continue
        data = dict(data)
        works = data.pop('works')
        numbers = data.pop('grades')
        data['map_x'] = Decimal(data['map_x'])
        data['map_y'] = Decimal(data['map_y'])
        author = Author.objects.create(position=next_position + offset, **data)
        Work.objects.bulk_create(
            Work(author=author, title=title, position=index) for index, title in enumerate(works, start=1)
        )
        author.grades.set(grades[number] for number in numbers)


def revert_distribution(apps, schema_editor):
    Author = apps.get_model('literature', 'Author')
    Work = apps.get_model('literature', 'Work')
    Author.objects.filter(slug__in=[data['slug'] for data in NEW_AUTHORS]).delete()
    for slug, numbers in GRADES.items():
        added = set(numbers) - set(PREVIOUS_GRADES.get(slug, []))
        for author in Author.objects.filter(slug=slug):
            author.grades.remove(*author.grades.filter(number__in=added))
    for slug, titles in EXTRA_WORKS.items():
        Work.objects.filter(author__slug=slug, title__in=titles).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('literature', '0004_aitmatov_in_moscow'),
    ]

    operations = [
        migrations.RunPython(apply_distribution, revert_distribution),
    ]
