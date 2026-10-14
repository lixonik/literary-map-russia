from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

DUPLICATE_EMAIL_MESSAGE = 'Пользователь с такой почтой уже зарегистрирован.'


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Укажите электронную почту')
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields['is_staff'] or not extra_fields['is_superuser']:
            raise ValueError('У суперпользователя должны быть is_staff=True и is_superuser=True')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(
        'электронная почта', unique=True, error_messages={'unique': DUPLICATE_EMAIL_MESSAGE}
    )
    full_name = models.CharField('ФИО', max_length=255)
    workplace = models.CharField('место работы', max_length=255, blank=True)
    research_interests = models.TextField('сферы научных интересов', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='unique_user_email_case_insensitive',
                violation_error_message=DUPLICATE_EMAIL_MESSAGE,
            ),
        ]

    def __str__(self):
        return self.full_name or self.email

    def clean(self):
        super().clean()
        self.email = self.email.lower()

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name
