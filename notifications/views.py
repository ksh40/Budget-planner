from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Notification


def _safe(request, target):
    ok = url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )
    return target if ok else "/"


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(_safe(request, request.POST.get("next", "/")))

@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(_safe(request, request.POST.get("next", "/")))


@login_required
def open_notification(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])
    return redirect(_safe(request, n.url or "/"))

@login_required
@require_POST
def delete(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({"ok": True, "unread": unread})
    return redirect(_safe(request, request.POST.get("next", "/")))


@login_required
@require_POST
def delete_all(request):
    Notification.objects.filter(user=request.user).delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "unread": 0})
    return redirect(_safe(request, request.POST.get("next", "/")))