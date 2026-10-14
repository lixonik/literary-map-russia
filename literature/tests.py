import io
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .media import parse_range
from .models import Author, Material, Worksheet
from .vk import normalize_vk_embed

AUDIO_BYTES = bytes(range(256)) * 4
VK_IFRAME = (
    '<iframe src="https://vkvideo.ru/video_ext.php?oid=-22822305&amp;id=456241864&amp;hash=e037414127166efe&amp;hd=2" '
    'width="853" height="480" allow="autoplay; encrypted-media; fullscreen; picture-in-picture;" '
    'frameborder="0" allowfullscreen></iframe>'
)
VK_EMBED_URL = 'https://vkvideo.ru/video_ext.php?oid=-22822305&id=456241864&hash=e037414127166efe'


def png_upload(name='image.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (30, 40), '#7d97bd').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class TemporaryMediaMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_dir = tempfile.mkdtemp()
        cls.media_override = override_settings(
            MEDIA_ROOT=Path(cls.media_dir) / 'media',
            PROTECTED_MEDIA_ROOT=Path(cls.media_dir) / 'protected',
        )
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        shutil.rmtree(cls.media_dir, ignore_errors=True)
        super().tearDownClass()


class HomePageTests(TestCase):
    def test_renders_map_points_and_author_cards(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'class="map__point', count=12)
        self.assertContains(response, 'class="author-card"', count=12)
        self.assertContains(response, '12 авторов · 11 литературных регионов')

    def test_map_coordinates_are_not_localized(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, '--x: 18.73%; --y: 90.01%')

    def test_points_carry_grades_for_filter(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'data-grades="4 5 6 11"')
        self.assertContains(response, 'data-grade="11"')


class DistributionTests(TestCase):
    def grades_of(self, slug):
        return list(Author.objects.get(slug=slug).grades.values_list('number', flat=True))

    def test_authors_follow_client_distribution(self):
        expected = {
            'gamzatov': [4, 5, 6, 11],
            'karim': [5, 6, 11],
            'kuliev': [6, 11],
            'tukay': [6, 10],
            'akmulla': [10],
            'khetagurov': [10],
            'aigi': [11],
            'aitmatov': [11],
            'jalil': [11],
            'kugultinov': [11],
            'rytkeu': [11],
            'shestalov': [11],
        }

        self.assertEqual({slug: self.grades_of(slug) for slug in expected}, expected)

    def test_program_works_are_listed(self):
        for slug, title in (('aitmatov', 'Белый пароход'), ('tukay', 'Книга'), ('kuliev', 'Что б ни делалось на свете…')):
            with self.subTest(slug=slug):
                self.assertTrue(Author.objects.get(slug=slug).works.filter(title=title).exists())

    def test_new_authors_are_on_map_with_pages(self):
        for slug, full_name in (('akmulla', 'Камалетдинов Мифтахетдин Камалетдинович'), ('khetagurov', 'Хетагуров Коста Леванович')):
            author = Author.objects.get(slug=slug)
            response = self.client.get(author.get_absolute_url())
            with self.subTest(slug=slug):
                self.assertTrue(author.on_map)
                self.assertContains(response, full_name)
                self.assertContains(response, '10 класс')

    def test_grade_ten_lists_three_authors(self):
        tenth = Author.objects.filter(grades__number=10).order_by('slug').values_list('slug', flat=True)

        self.assertEqual(list(tenth), ['akmulla', 'khetagurov', 'tukay'])


class FaviconTests(TestCase):
    def test_favicon_ico_is_served(self):
        response = self.client.get('/favicon.ico')

        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].endswith('img/favicon.ico'))
        self.assertTrue((Path(settings.BASE_DIR) / 'static' / 'img' / 'favicon.ico').is_file())

    def test_pages_declare_png_icon_for_safari(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'rel="icon" href="/static/img/favicon.png" type="image/png"')
        self.assertTrue((Path(settings.BASE_DIR) / 'static' / 'img' / 'favicon.png').is_file())


class AuthorMapPointValidationTests(TestCase):
    def setUp(self):
        self.author = Author.objects.get(slug='karim')

    def test_requires_both_coordinates(self):
        for x, y, missing in ((Decimal('30'), None, 'map_y'), (None, Decimal('40'), 'map_x')):
            self.author.map_x, self.author.map_y = x, y
            with self.subTest(missing=missing), self.assertRaises(ValidationError) as caught:
                self.author.full_clean()
            self.assertIn(missing, caught.exception.message_dict)

    def test_allows_both_or_neither(self):
        for x, y in ((Decimal('30'), Decimal('40')), (None, None)):
            self.author.map_x, self.author.map_y = x, y
            with self.subTest(x=x, y=y):
                self.author.full_clean()


class AitmatovPlacementTests(TestCase):
    def test_marked_in_moscow(self):
        aitmatov = Author.objects.get(slug='aitmatov')

        self.assertTrue(aitmatov.on_map)
        self.assertEqual(aitmatov.region, 'Кыргызстан · жил в Москве')
        self.assertIn('Высших литературных курсах', aitmatov.biography)


class AuthorPageTests(TestCase):
    def test_shows_required_facts(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'gamzatov'}))

        self.assertContains(response, 'Гамзатов Расул Гамзатович')
        self.assertContains(response, '8 сентября 1923 — 3 ноября 2003')
        self.assertContains(response, 'село Цада, Дагестанская АССР')
        self.assertContains(response, '«Журавли»')
        self.assertContains(response, 'Разработка готовится')
        self.assertContains(response, 'Рабочие листы к разработке пока не добавлены.')

    def test_methodology_text_replaces_placeholder(self):
        Author.objects.filter(slug='tukay').update(methodology='Цель занятия.\n\nХод урока.')

        response = self.client.get(reverse('author', kwargs={'slug': 'tukay'}))

        self.assertContains(response, '<p>Цель занятия.</p>', html=True)
        self.assertNotContains(response, 'Разработка готовится')

    def test_unknown_author_returns_404(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'unknown'}))

        self.assertEqual(response.status_code, 404)


class AuthorAttachmentsTests(TemporaryMediaMixin, TestCase):
    def setUp(self):
        self.author = Author.objects.get(slug='karim')
        self.url = reverse('author', kwargs={'slug': 'karim'})

    def test_shows_portrait(self):
        self.author.portrait = png_upload('karim.png')
        self.author.save()

        response = self.client.get(self.url)

        self.assertContains(response, 'author-hero--with-portrait')
        self.assertContains(response, f'src="{self.author.portrait.url}"')

    def test_methodology_file_is_open_to_everyone(self):
        self.author.methodology_file = SimpleUploadedFile('lesson.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        self.author.save()

        response = self.client.get(self.url)

        self.assertContains(response, f'href="{self.author.methodology_file.url}"')
        self.assertContains(response, 'Файл методической разработки')
        self.assertNotContains(response, 'Разработка готовится')

    def test_worksheets_are_listed(self):
        worksheet = Worksheet.objects.create(author=self.author, title='Лист 1', image=png_upload('sheet.png'))

        response = self.client.get(self.url)

        self.assertContains(response, f'href="{worksheet.image.url}"')
        self.assertContains(response, 'Лист 1')
        self.assertNotContains(response, 'Рабочие листы к разработке пока не добавлены.')

    def test_replacing_or_clearing_files_removes_old_ones(self):
        self.author.portrait = png_upload('first.png')
        self.author.methodology_file = SimpleUploadedFile('first.pdf', b'%PDF-1.4', content_type='application/pdf')
        self.author.save()
        worksheet = Worksheet.objects.create(author=self.author, image=png_upload('first-sheet.png'))
        storage = self.author.portrait.storage
        old_names = [self.author.portrait.name, self.author.methodology_file.name, worksheet.image.name]

        with self.captureOnCommitCallbacks(execute=True):
            self.author.portrait = png_upload('second.png')
            self.author.methodology_file = None
            self.author.save()
            worksheet.image = png_upload('second-sheet.png')
            worksheet.save()

        self.assertFalse(any(storage.exists(name) for name in old_names))
        self.assertTrue(storage.exists(self.author.portrait.name))
        self.assertTrue(storage.exists(worksheet.image.name))

    def test_deleting_author_removes_files(self):
        self.author.portrait = png_upload('karim.png')
        self.author.save()
        worksheet = Worksheet.objects.create(author=self.author, image=png_upload('sheet.png'))
        storage, names = self.author.portrait.storage, [self.author.portrait.name, worksheet.image.name]

        with self.captureOnCommitCallbacks(execute=True):
            self.author.delete()

        self.assertFalse(any(storage.exists(name) for name in names))


class ParseRangeTests(SimpleTestCase):
    def test_parses_open_ended_and_suffix_ranges(self):
        self.assertEqual(parse_range('bytes=0-1', 100), (0, 1))
        self.assertEqual(parse_range('bytes=10-', 100), (10, 99))
        self.assertEqual(parse_range('bytes=-20', 100), (80, 99))
        self.assertEqual(parse_range('bytes=50-500', 100), (50, 99))

    def test_ignores_unsupported_headers(self):
        self.assertIsNone(parse_range('', 100))
        self.assertIsNone(parse_range('bytes=0-1,5-6', 100))
        self.assertIsNone(parse_range('items=0-1', 100))


class VkEmbedTests(SimpleTestCase):
    def test_accepts_embed_code_and_player_url(self):
        self.assertEqual(normalize_vk_embed(VK_IFRAME), VK_EMBED_URL)
        self.assertEqual(normalize_vk_embed(VK_EMBED_URL.replace('vkvideo.ru', 'www.vk.com')), VK_EMBED_URL.replace('vkvideo.ru', 'vk.com'))

    def test_accepts_page_links_and_codes_without_access_key(self):
        player = 'https://vk.ru/video_ext.php?oid=-22822305&id=456241864'

        for value in (
            'https://vkvideo.ru/video-22822305_456241864',
            'https://vk.com/video-22822305_456241864?list=ln-abc',
            'https://vk.com/videos-22822305?z=video-22822305_456241864%2Fpl_-22822305_-2',
            '<iframe src="https://vk.ru/video_ext.php?oid=-22822305&id=456241864&hd=2"></iframe>',
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize_vk_embed(value), player)

    def test_rejects_foreign_hosts_schemes_and_non_video_pages(self):
        for value in (
            VK_EMBED_URL.replace('vkvideo.ru', 'evil.example'),
            VK_EMBED_URL.replace('https', 'javascript'),
            '<iframe src="https://youtube.com/embed/abc"></iframe>',
            'https://vk.com/club22822305',
            'https://vk.ru/video_ext.php?oid=abc&id=1',
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                normalize_vk_embed(value)


class MaterialValidationTests(TestCase):
    def setUp(self):
        self.author = Author.objects.get(slug='gamzatov')

    def test_requires_exactly_one_source(self):
        empty = Material(author=self.author, title='Пусто')
        both = Material(
            author=self.author,
            title='Оба',
            vk_video=VK_IFRAME,
            file=SimpleUploadedFile('a.mp3', AUDIO_BYTES, content_type='audio/mpeg'),
        )

        for material in (empty, both):
            with self.subTest(title=material.title), self.assertRaises(ValidationError):
                material.full_clean()

    def test_normalizes_vk_embed_code(self):
        material = Material(author=self.author, title='Чтение', vk_video=VK_IFRAME)

        material.full_clean()

        self.assertEqual(material.vk_video, VK_EMBED_URL)


class VkMaterialPageTests(TestCase):
    def setUp(self):
        self.material = Material.objects.create(
            author=Author.objects.get(slug='gamzatov'), title='Журавли', vk_video=VK_EMBED_URL
        )

    def test_renders_vk_player_without_download(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'gamzatov'}))

        self.assertContains(response, '<iframe src="https://vkvideo.ru/video_ext.php?oid=-22822305&amp;id=456241864')
        self.assertNotContains(response, 'Скачивание доступно после')
        self.assertNotContains(response, reverse('material-download', kwargs={'pk': self.material.pk}))

    def test_stream_and_download_return_404(self):
        self.client.force_login(get_user_model().objects.create_user('r@example.com', 'test-pass-123', full_name='Р'))

        for name in ('material-stream', 'material-download'):
            response = self.client.get(reverse(name, kwargs={'pk': self.material.pk}))
            self.assertEqual(response.status_code, 404)


class MaterialAccessTests(TemporaryMediaMixin, TestCase):
    def setUp(self):
        self.material = Material.objects.create(
            author=Author.objects.get(slug='gamzatov'),
            title='Журавли',
            file=SimpleUploadedFile('reading.mp3', AUDIO_BYTES, content_type='audio/mpeg'),
        )
        self.stream_url = reverse('material-stream', kwargs={'pk': self.material.pk})
        self.download_url = reverse('material-download', kwargs={'pk': self.material.pk})

    def test_file_is_stored_outside_public_media(self):
        stored = Path(self.material.file.path)

        self.assertTrue(stored.is_relative_to(settings.PROTECTED_MEDIA_ROOT))
        self.assertFalse(stored.is_relative_to(settings.MEDIA_ROOT))
        with self.assertRaises(ValueError):
            self.material.file.url

    def test_anyone_can_stream(self):
        response = self.client.get(self.stream_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'audio/mpeg')
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        self.assertEqual(b''.join(response.streaming_content), AUDIO_BYTES)

    def test_stream_supports_range_requests(self):
        response = self.client.get(self.stream_url, HTTP_RANGE='bytes=0-1')

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Content-Range'], f'bytes 0-1/{len(AUDIO_BYTES)}')
        self.assertEqual(b''.join(response.streaming_content), AUDIO_BYTES[:2])

    def test_unsatisfiable_range_returns_416(self):
        response = self.client.get(self.stream_url, HTTP_RANGE=f'bytes={len(AUDIO_BYTES)}-')

        self.assertEqual(response.status_code, 416)

    def test_anonymous_download_redirects_to_login(self):
        response = self.client.get(self.download_url)

        self.assertRedirects(response, f"{reverse('login')}?next={self.download_url}")

    def test_registered_user_downloads_attachment(self):
        user = get_user_model().objects.create_user('reader@example.com', 'test-pass-123', full_name='Читатель')
        self.client.force_login(user)

        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))
        self.assertEqual(b''.join(response.streaming_content), AUDIO_BYTES)

    def test_author_page_hides_download_link_for_anonymous(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'gamzatov'}))

        self.assertContains(response, self.stream_url)
        self.assertNotContains(response, self.download_url)
        self.assertContains(response, 'Скачивание доступно после')

    def test_admin_pages_render_uploaded_material_with_stream_link(self):
        admin = get_user_model().objects.create_superuser('admin@example.com', 'test-pass-123', full_name='Админ')
        self.client.force_login(admin)

        author_page = self.client.get(reverse('admin:literature_author_change', args=[self.material.author.pk]))
        material_page = self.client.get(reverse('admin:literature_material_change', args=[self.material.pk]))

        for response in (author_page, material_page):
            self.assertContains(response, f'href="{self.stream_url}"')

    def test_deleting_material_removes_file(self):
        storage, name = self.material.file.storage, self.material.file.name

        with self.captureOnCommitCallbacks(execute=True):
            self.material.delete()

        self.assertFalse(storage.exists(name))

    def test_replacing_material_file_removes_old_one(self):
        storage, old_name = self.material.file.storage, self.material.file.name

        with self.captureOnCommitCallbacks(execute=True):
            self.material.file = SimpleUploadedFile('new.mp3', AUDIO_BYTES, content_type='audio/mpeg')
            self.material.save()

        self.assertFalse(storage.exists(old_name))
        self.assertTrue(storage.exists(self.material.file.name))

    def test_missing_file_returns_404(self):
        self.material.file.storage.delete(self.material.file.name)

        response = self.client.get(self.stream_url)

        self.assertEqual(response.status_code, 404)
