from .models import Notification


def nav_notifications(request):
    """Adds nav_notifications (latest 8) and nav_unread to every template.

    In the navbar: {{ nav_unread.count }} for the red number.
    Both are lazy, so pages that never print them run no query.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    qs = Notification.objects.filter(user=user)
    return {"nav_notifications": qs[:8], "nav_unread": qs.filter(is_read=False)}
