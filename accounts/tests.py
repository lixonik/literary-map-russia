from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from literature.models import Author

User = get_user_model()


class RegistrationTests(TestCase):
    def submit(self, **overrides):
        data = {
            'full_name': 'Иванова Анна Сергеевна',
            'email': 'Anna@Example.com',
            'workplace': 'Школа № 1',
            'research_interests': 'Литература народов России',
            'password1': 'long-unique-pass-42',
            'password2': 'long-unique-pass-42',
        }
        data.update(overrides)
        return self.client.post(reverse('register'), data)

    def test_creates_user_with_profile_fields_and_logs_in(self):
        response = self.submit()

        self.assertRedirects(response, reverse('home'))
        user = User.objects.get()
        self.assertEqual(user.email, 'anna@example.com')
        self.assertEqual(user.full_name, 'Иванова Анна Сергеевна')
        self.assertEqual(user.workplace, 'Школа № 1')
        self.assertEqual(user.research_interests, 'Литература народов России')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_requires_workplace_and_interests(self):
        response = self.submit(workplace='', research_interests='')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertFormError(response.context['form'], 'workplace', 'Обязательное поле.')
        self.assertFormError(response.context['form'], 'research_interests', 'Обязательное поле.')

    def test_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user('anna@example.com', 'other-pass-42', full_name='Анна')

        response = self.submit(email='ANNA@example.com')

        self.assertEqual(User.objects.count(), 1)
        self.assertFormError(response.context['form'], 'email', 'Пользователь с такой почтой уже зарегистрирован.')

    def test_redirects_to_safe_next_only(self):
        author_url = reverse('author', kwargs={'slug': 'tukay'})

        self.assertRedirects(self.submit(next=author_url), author_url)

    def test_ignores_external_next(self):
        response = self.submit(next='https://example.org/')

        self.assertRedirects(response, reverse('home'))


class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user('teacher@example.com', 'long-unique-pass-42', full_name='Учитель')

    def test_login_by_email_ignores_case(self):
        response = self.client.post(
            reverse('login'), {'username': 'Teacher@Example.com', 'password': 'long-unique-pass-42'}
        )

        self.assertRedirects(response, reverse('home'))

    def test_wrong_password_shows_readable_error(self):
        response = self.client.post(reverse('login'), {'username': 'teacher@example.com', 'password': 'wrong'})

        self.assertContains(response, 'Неверная электронная почта или пароль.')

    def test_header_login_link_is_not_nested_on_auth_pages(self):
        for name in ('login', 'register'):
            response = self.client.get(reverse(name))

            self.assertContains(response, f'class="pill" href="{reverse("login")}"')

    def test_header_login_link_returns_to_current_page(self):
        response = self.client.get(reverse('author', kwargs={'slug': 'tukay'}))

        self.assertContains(response, f'href="{reverse("login")}?next=/authors/tukay/"')

    def test_logout_requires_post(self):
        self.client.login(username='teacher@example.com', password='long-unique-pass-42')

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_returns_to_current_page(self):
        author_url = reverse('author', kwargs={'slug': 'tukay'})
        self.client.login(username='teacher@example.com', password='long-unique-pass-42')

        page = self.client.get(author_url)
        response = self.client.post(reverse('logout'), {'next': author_url})

        self.assertContains(page, f'<input type="hidden" name="next" value="{author_url}">', html=True)
        self.assertRedirects(response, author_url)


class EmailUniquenessTests(TestCase):
    def test_email_is_lowercased_on_clean(self):
        user = User(email='Mixed.Case@Example.COM', full_name='Учитель')
        user.set_password('long-unique-pass-42')

        user.full_clean()

        self.assertEqual(user.email, 'mixed.case@example.com')

    def test_database_rejects_case_insensitive_duplicates(self):
        User.objects.create_user('teacher@example.com', 'long-unique-pass-42', full_name='Учитель')

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(email='Teacher@example.com', full_name='Дубль')


class AdminTests(TestCase):
    def setUp(self):
        admin = User.objects.create_superuser('admin@example.com', 'long-unique-pass-42', full_name='Администратор')
        self.client.force_login(admin)

    def test_admin_pages_render(self):
        author = self.client.get(reverse('admin:literature_author_changelist'))
        author_change = self.client.get(
            reverse('admin:literature_author_change', args=[Author.objects.get(slug='gamzatov').pk])
        )
        user_add = self.client.get(reverse('admin:accounts_user_add'))
        user_change = self.client.get(reverse('admin:accounts_user_change', args=[User.objects.get().pk]))

        for response in (author, author_change, user_add, user_change):
            self.assertEqual(response.status_code, 200)

    def test_map_coordinates_accept_comma_and_dot(self):
        response = self.client.get(
            reverse('admin:literature_author_change', args=[Author.objects.get(slug='gamzatov').pk])
        )
        map_x = response.context['adminform'].form.fields['map_x']

        self.assertEqual(map_x.clean('18,5'), Decimal('18.5'))
        self.assertEqual(map_x.clean('18.5'), Decimal('18.5'))
        self.assertContains(response, 'name="map_x" value="18,73"')

    def add_user(self, email):
        return self.client.post(reverse('admin:accounts_user_add'), {
            'email': email,
            'full_name': 'Второй администратор',
            'usable_password': 'true',
            'password1': 'long-unique-pass-42',
            'password2': 'long-unique-pass-42',
        })

    def test_admin_add_user_stores_lowercase_email(self):
        self.add_user('Second.Admin@Example.com')

        self.assertTrue(User.objects.filter(email='second.admin@example.com').exists())

    def test_admin_rejects_duplicate_email_in_other_case(self):
        self.add_user('second@example.com')

        response = self.add_user('SECOND@example.com')

        self.assertEqual(User.objects.filter(email__iexact='second@example.com').count(), 1)
        self.assertEqual(
            response.context['adminform'].form.errors,
            {'email': ['Пользователь с такой почтой уже зарегистрирован.']},
        )

    def test_admin_change_rejects_email_of_another_user(self):
        self.add_user('second@example.com')
        second = User.objects.get(email='second@example.com')
        page = self.client.get(reverse('admin:accounts_user_change', args=[second.pk]))
        form = page.context['adminform'].form

        data = {name: value for name, value in form.initial.items() if value is not None and name != 'password'}
        data.update({'email': 'ADMIN@example.com', 'groups': [], 'user_permissions': [], 'is_active': 'on'})
        data['date_joined_0'], data['date_joined_1'] = '01.01.2026', '00:00:00'
        response = self.client.post(reverse('admin:accounts_user_change', args=[second.pk]), data)

        second.refresh_from_db()
        self.assertEqual(second.email, 'second@example.com')
        self.assertEqual(
            response.context['adminform'].form.errors['email'],
            ['Пользователь с такой почтой уже зарегистрирован.'],
        )

    def test_login_works_for_admin_created_user(self):
        self.add_user('Second.Admin@Example.com')
        self.client.logout()

        response = self.client.post(
            reverse('login'), {'username': 'second.admin@example.com', 'password': 'long-unique-pass-42'}
        )

        self.assertRedirects(response, reverse('home'))
