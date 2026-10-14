# Literary Map of the Peoples of Russia

**English** | [Русский](README.ru.md)

A Django navigator site for literature teachers, school students and philology students: an interactive map of writers from the peoples of Russia, author pages, and lesson plans with audio and video materials. The site interface is in Russian.

## Features

- **Home page**: a map with author points, author cards, a lesson-plan toolkit and a "Literature by grade" block. Selecting a grade keeps only the authors studied in that grade on the map and in the list.
- **Author page**: portrait, full name, life dates, birthplace, literary tradition, biography, key works and a "Lesson plan" section: text and/or a lesson-plan file, worksheets (images), audio and video. Until a lesson plan is added, the page shows a placeholder for the section.
- **Access to materials**: everything is open for viewing to all visitors. Only registered users can download uploaded audio and video. VK videos are shown in the embedded VK player.
- **Registration**: full name, email, workplace, research interests and password. Users sign in with their email.
- **Admin** at `/admin/`: all site content is edited without touching the code.

## Getting started

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

On Windows, activate the virtual environment with `.venv\Scripts\activate` and copy the file with `copy .env.example .env`.

The site opens at http://127.0.0.1:8000/, the admin at http://127.0.0.1:8000/admin/.

`migrate` creates 12 authors and grades 1 to 11 right away, so the site is not empty afterwards.

Put a secret key into `.env`. You can generate one like this:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Without a key the site starts only in development mode (`DJANGO_DEBUG=1`).

Tests:

```bash
python manage.py test
```

## Admin access

### Create an administrator

Run this in the project directory with the virtual environment activated:

```bash
python manage.py createsuperuser
```

The command asks for, in order:

- **email**: it is used as the login;
- **full name** (prompted as «ФИО»);
- **password**, twice. Characters are not shown while you type the password, this is expected.

If the password is too short or too common, Django warns and asks whether to create the user anyway: answering `y` creates it. Use a strong password on a server reachable from the internet.

### Sign in

1. Start the site with `python manage.py runserver`.
2. Open http://127.0.0.1:8000/admin/ (on a server: `https://<your domain>/admin/`).
3. Enter the administrator's email and password. Email letter case does not matter.

The «Войти» (Sign in) button in the site header also signs the administrator in, but it returns to the site. The admin is reachable only at `/admin/`.

### More administrators and password changes

- **Make a registered user an administrator**: in the admin open **Пользователи** (Users), select the user, tick «Статус персонала» (Staff status, grants admin access) and «Статус суперпользователя» (Superuser status, grants all permissions), then click «Сохранить» (Save). Instead of superuser status you can grant individual permissions in the «Права пользователя» (User permissions) field.
- **Change a password**, including a forgotten one, with the command below. Type the email in lowercase, as it is stored in the database:

```bash
python manage.py changepassword admin@example.com
```

## Editing content in the admin

The **Авторы** (Authors) section:

- **Portrait**: the «портрет» (portrait) field, any image. Shown on the right of the author page header.
- **Lesson plan**: the «текст методической разработки» (lesson plan text) field (separate paragraphs with a blank line) and/or the «файл методической разработки» (lesson plan file) field (PDF, Word, PowerPoint). The file is open to all visitors.
- **Worksheets**: the «Рабочие листы» (Worksheets) block in the author form, one image per worksheet, the caption is optional. The site shows them as a gallery, a click opens the full image.
- **Audio and video**: the block at the bottom of the author form. Each material has either an uploaded file or a VK video, exactly one of them:
  - file: mp3, m4a, aac, wav, ogg (audio) and mp4, m4v, mov, webm (video). mp4 and mp3 work best in Safari;
  - VK: paste a regular video link or the embed code (right-click the video, «Копировать код для встраивания», i.e. Copy embed code) into the «видео ВКонтакте» (VK video) field. The video must be public, otherwise visitors who are not signed in to VK will not see it.
- **Grades**: the checkboxes in the «изучается в классах» (studied in grades) field drive the filter on the home page.
- **Map point**: X and Y set the offset from the left and top edges of the Russia outline in percent, «сторона подписи» (label side) sets where the label is placed. If X and Y are empty, the author appears only in the list.
- **Order**: the number sets the order of the cards and their number on the home page.

## Structure

```
config/       settings, URL routing
accounts/     user model with email login, registration
literature/   authors, works, grades, worksheets, materials, VK videos, media file delivery
templates/    page templates
static/       styles, grade filter script, map outline, logo
```

## Technical notes

- Files are stored in two directories:
  - `media/` is public: portraits, lesson-plan files, worksheets. In development Django serves it at `/media/`, on a server it can be published directly;
  - `protected/` is private: uploaded audio and video. They are served only through the application: `/materials/<id>/` for playback (with HTTP Range support, without which Safari does not play video) and `/materials/<id>/download/` for downloads after signing in. Do not publish `protected/` through the web server, otherwise the download restriction can be bypassed.
- The download restriction is enforced by the interface and by permissions on the download link. A file that the browser plays can technically be saved with third-party tools. Only encrypted streaming (DRM) gives full protection, which is excessive for an educational site.
- Authors' dates and birthplaces were checked against the Russian Wikipedia. The links between authors and grades come from the topic distribution provided by the client; for grades 5 and 6 they match the federal working program for literature. Grades 1-3 have no authors (according to the distribution, folklore is studied there), and grades 7-9 are not in the distribution at all.
- Map points were taken from the original mockup and placed schematically so that labels do not overlap. Some points are geographically off (Karim, Shestalov, Tukay and Aigi the most). Aitmatov was born outside Russia, so his point is placed on Moscow, where he studied at the Higher Literary Courses in 1956-1958. Coordinates can be edited in the admin.
- The Russia outline is built from [Natural Earth](https://www.naturalearthdata.com/) data (public domain).
- For deployment: `DJANGO_DEBUG=0`, your own `DJANGO_SECRET_KEY`, the domain in `DJANGO_ALLOWED_HOSTS`, then `python manage.py collectstatic`.
