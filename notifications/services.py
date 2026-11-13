from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification


def notify(user, message, url="", kind=Notification.Kind.GENERAL):
    """Create a notification. Use this everywhere instead of messages.success()."""
    return Notification.objects.create(
        user=user, message=message[:255], url=url, kind=kind
    )


def notify_welcome(user, message=None):
    Notification.objects.update_or_create(
        user=user,
        kind=Notification.Kind.WELCOME,
        defaults={
            "message": message or f"Welcome back, {user.get_username()}. You are logged in.",
            "is_read": False,
            "created_at": timezone.now(),
        },
    )


def notify_staff(message, url=""):
    """Tell every active staff member something needs their attention."""
    staff = get_user_model().objects.filter(is_staff=True, is_active=True)
    Notification.objects.bulk_create(
        [
            Notification(user=u, message=message[:255], url=url, kind=Notification.Kind.GENERAL)
            for u in staff
        ]
    )
