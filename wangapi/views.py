from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import Profile, User
from eventful.models import Eventful
from events.models import Event

from .forms import PictureForm, RegisterForm
from .models import Bookmark
from .utils import PLACEHOLDER_SUFFIX, get_model_for, saved_items, top_saved


def _safe_next(request):
    target = request.POST.get('next') or request.GET.get('next') or ''
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return reverse('homeplan')


class WangapiLoginView(LoginView):
    template_name = 'wangapi/login.html'
    redirect_authenticated_user = True


def register_view(request):
    if request.user.is_authenticated:
        return redirect('wangapi_profile')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Karibu, {user.username}!')
        return redirect(_safe_next(request))

    return render(request, 'wangapi/register.html', {
        'form': form,
        'next': request.POST.get('next') or request.GET.get('next') or '',
    })


@login_required(login_url='wangapi_login')
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Picture updated.')
            return redirect('wangapi_profile')
    else:
        form = PictureForm(instance=profile)

    return render(request, 'wangapi/profile.html', {
        'profile': profile,
        'form': form,
        'items': saved_items(request.user),
    })


@require_POST
def toggle_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    kind = request.POST.get('kind', '')
    model = get_model_for(kind)
    try:
        pk = int(request.POST.get('pk', ''))
    except ValueError:
        return JsonResponse({'error': 'bad id'}, status=400)
    if model is None:
        return JsonResponse({'error': 'unknown post type'}, status=400)

    if request.POST.get('mode') == 'remove':
        Bookmark.objects.filter(user=request.user, kind=kind, object_id=pk).delete()
        saved = False
    else:
        if not model.objects.filter(pk=pk).exists():
            return JsonResponse({'error': 'not found'}, status=404)
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user, kind=kind, object_id=pk
        )
        if not created:
            bookmark.delete()
        saved = created

    count = Bookmark.objects.filter(kind=kind, object_id=pk).count()
    return JsonResponse({'saved': saved, 'count': count})


@login_required(login_url='wangapi_login')
def delete_account_view(request):
    user = request.user
    if user.is_staff or user.is_superuser:
        messages.error(request, "Staff accounts can't be deleted here.")
        return redirect('wangapi_profile')

    error = ''
    if request.method == 'POST':
        if user.check_password(request.POST.get('password', '')):
            try:
                user.delete()
            except ProtectedError:
                error = "This account is linked to other records, so it can't be deleted here. Ask the admin."
            else:
                logout(request)
                messages.success(request, 'Your account has been deleted.')
                return redirect('homeplan')
        else:
            error = "That password isn't right."

    return render(request, 'wangapi/delete_account.html', {'error': error})


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_staff, login_url='wangapi_login')
def analytics_view(request):
    week_ago = timezone.now() - timedelta(days=7)
    accounts_total = User.objects.count()
    wangapi_accounts = User.objects.filter(email__endswith=PLACEHOLDER_SUFFIX).count()
    evently_events = Event.objects.filter(status='approved').count()
    eventful_events = Eventful.objects.count()

    return render(request, 'wangapi/analytics.html', {
        'accounts_total': accounts_total,
        'wangapi_accounts': wangapi_accounts,
        'evently_accounts': accounts_total - wangapi_accounts,
        'new_accounts': User.objects.filter(date_joined__gte=week_ago).count(),
        'events_total': evently_events + eventful_events,
        'evently_events': evently_events,
        'eventful_events': eventful_events,
        'saves_total': Bookmark.objects.count(),
        'top': top_saved(),
    })
