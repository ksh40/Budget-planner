from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import re
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone


def verification_storage():
    return FileSystemStorage(location=settings.MEDIA_ROOT)

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('attendee', 'Attendee'),
        ('organiser', 'Organiser'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendee')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Organiser verification
    verification_document = models.FileField(upload_to='verification_docs/',storage=verification_storage, blank=True, null=True)
    verification_document_hash = models.CharField(max_length=64, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    verification_notes = models.TextField(blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.username

    def is_organiser(self):
        return self.role == 'organiser'

    def is_attendee(self):
        return self.role == 'attendee'


HINT_MAX_TRIES = 5
HINT_LOCK_MINUTES = 30


def _norm(answer):
    """'  My  Dog ' and 'my dog' count as the same answer."""
    return re.sub(r'\s+', ' ', answer or '').strip().lower()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    interests = models.TextField(blank=True, help_text='Comma-separated interests')
    bookmarks_public = models.BooleanField(default=False)

    # Password-reset hint
    hint_question = models.CharField(max_length=120, blank=True)
    hint_answer_hash = models.CharField(max_length=128, blank=True)
    hint_failed = models.PositiveSmallIntegerField(default=0)
    hint_locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} profile'

    @property
    def has_hint(self):
        return bool(self.hint_question and self.hint_answer_hash)

    @property
    def hint_locked(self):
        return bool(self.hint_locked_until and self.hint_locked_until > timezone.now())

    def set_hint(self, question, answer):
        self.hint_question = question.strip()
        self.hint_answer_hash = make_password(_norm(answer))
        self.hint_failed = 0
        self.hint_locked_until = None
        self.save(update_fields=[
            'hint_question', 'hint_answer_hash', 'hint_failed', 'hint_locked_until',
        ])

    def check_hint(self, answer):
        
        if self.hint_locked or not self.has_hint:
            return False
        if check_password(_norm(answer), self.hint_answer_hash):
            self.hint_failed = 0
            self.hint_locked_until = None
            self.save(update_fields=['hint_failed', 'hint_locked_until'])
            return True
        self.hint_failed += 1
        if self.hint_failed >= HINT_MAX_TRIES:
            self.hint_failed = 0
            self.hint_locked_until = timezone.now() + timedelta(minutes=HINT_LOCK_MINUTES)
        self.save(update_fields=['hint_failed', 'hint_locked_until'])
        return False

