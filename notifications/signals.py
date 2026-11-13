from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import notify_welcome


@receiver(user_logged_in)
def welcome_on_login(sender, request, user, **kwargs):
    notify_welcome(user)
