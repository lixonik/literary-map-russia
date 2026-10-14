import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .media import parse_range
from .models import Author, Material

AUDIO_BYTES = bytes(range(256)) * 4


class HomePageTests(TestCase):
    def test_renders_map_points_and_author_cards(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'class="map__point', count=9)
        self.assertContains(response, 'class="author-card"', count=10)
        self.assertContains(response, '9 авторов · 9 литературных регионов')

    def test_map_coordinates_are_not_localized(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, '--x: 18.73%; --y: 90.01%')

    def test_points_carry_grades_for_filter(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'data-grades="5 6"')
        self.assertContains(response, 'data-grade="11"')


class AuthorPageTests(TestCase):
    def test_shows_required_facts(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'gamzatov'}))

        self.assertContains(response, 'Гамзатов Расул Гамзатович')
        self.assertContains(response, '8 сентября 1923 — 3 ноября 2003')
        self.assertContains(response, 'село Цада, Дагестанская АССР')
        self.assertContains(response, '«Журавли»')
        self.assertContains(response, 'Текст разработки готовится')

    def test_methodology_text_replaces_placeholder(self):
        Author.objects.filter(slug='tukay').update(methodology='Цель занятия.\n\nХод урока.')

        response = self.client.get(reverse('author', kwargs={'slug': 'tukay'}))

        self.assertContains(response, '<p>Цель занятия.</p>', html=True)
        self.assertNotContains(response, 'Текст разработки готовится')

    def test_unknown_author_returns_404(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'unknown'}))

        self.assertEqual(response.status_code, 404)


class ParseRangeTests(TestCase):
    def test_parses_open_ended_and_suffix_ranges(self):
        self.assertEqual(parse_range('bytes=0-1', 100), (0, 1))
        self.assertEqual(parse_range('bytes=10-', 100), (10, 99))
        self.assertEqual(parse_range('bytes=-20', 100), (80, 99))
        self.assertEqual(parse_range('bytes=50-500', 100), (50, 99))

    def test_ignores_unsupported_headers(self):
        self.assertIsNone(parse_range('', 100))
        self.assertIsNone(parse_range('bytes=0-1,5-6', 100))
        self.assertIsNone(parse_range('items=0-1', 100))


class MaterialAccessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp()
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.material = Material.objects.create(
            author=Author.objects.get(slug='gamzatov'),
            title='Журавли',
            file=SimpleUploadedFile('reading.mp3', AUDIO_BYTES, content_type='audio/mpeg'),
        )
        self.stream_url = reverse('material-stream', kwargs={'pk': self.material.pk})
        self.download_url = reverse('material-download', kwargs={'pk': self.material.pk})

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
        author_url = reverse('author', kwargs={'slug': 'gamzatov'})

        response = self.client.get(author_url)

        self.assertContains(response, self.stream_url)
        self.assertNotContains(response, self.download_url)
        self.assertContains(response, 'Скачивание доступно после')

    def test_deleting_material_removes_file(self):
        storage, name = self.material.file.storage, self.material.file.name

        self.material.delete()

        self.assertFalse(storage.exists(name))

    def test_missing_file_returns_404(self):
        self.material.file.storage.delete(self.material.file.name)

        response = self.client.get(self.stream_url)

        self.assertEqual(response.status_code, 404)
