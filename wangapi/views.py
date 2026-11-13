from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import ProtectedError
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import Profile, User
from eventful.models import Eventful
from events.models import Event
from notifications.services import notify, notify_welcome
from recipes.models import ChefProfile, Recipe, Status

from django.db import transaction

from .forms import ForgotResetForm, PictureForm, RegisterForm, SecurityForm, UsernameForm
from .models import Bookmark
from .utils import (
    PLACEHOLDER_SUFFIX,
    decorate_recipes,
    get_model_for,
    saved_items,
    saved_recipes,
    top_saved,
)


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
        notify_welcome(user, f'Karibu, {user.username}!')
        return redirect(_safe_next(request))

    return render(request, 'wangapi/register.html', {
        'form': form,
        'next': request.POST.get('next') or request.GET.get('next') or '',
    })


def _profile_context(request, owner, profile, form, username_form):
    is_owner = request.user.is_authenticated and request.user.pk == owner.pk
    chef = ChefProfile.objects.filter(user=owner).first()
    chef_ok = chef is not None and chef.is_approved

    my_recipes = []
    if chef:
        qs = (
            Recipe.objects.filter(chef=chef)
            .select_related('chef__user')
            .prefetch_related('photos')
        )
        if not is_owner:
            qs = qs.live()
        my_recipes = decorate_recipes(request.user, list(qs))

    show_bookmarks = is_owner or profile.bookmarks_public
    items, saved = [], []
    if show_bookmarks:
        items = saved_items(owner)
        saved = saved_recipes(request.user, owner)

    return {
        'owner': owner,
        'profile': profile,
        'is_owner': is_owner,
        'chef': chef,
        'chef_ok': chef_ok,
        'chef_links': chef.social_links if chef and (chef_ok or is_owner) else [],
        'my_recipes': my_recipes,
        'show_bookmarks': show_bookmarks,
        'items': items,
        'saved_recipes': saved,
        'default_tab': 'recipes' if chef else 'saved',
        'form': form,
        'username_form': username_form,
    }


@login_required(login_url='wangapi_login')
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = PictureForm(instance=profile)
    # A separate copy, so a rejected rename doesn't change the name shown in the navbar.
    username_form = UsernameForm(instance=User.objects.get(pk=request.user.pk))

    if request.method == 'POST':
        action = request.POST.get('action', 'picture')
        if action == 'username':
            username_form = UsernameForm(
                request.POST, instance=User.objects.get(pk=request.user.pk)
            )
            if username_form.is_valid():
                user = username_form.save()
                notify(request.user, f'Your username is now {user.username}.')
                return redirect('wangapi_profile')
        elif action == 'privacy':
            profile.bookmarks_public = request.POST.get('bookmarks_public') == 'on'
            profile.save(update_fields=['bookmarks_public'])
            return redirect('wangapi_profile')
        else:
            form = PictureForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                notify(request.user, 'Your picture was updated.')
                return redirect('wangapi_profile')

    return render(
        request, 'wangapi/profile.html',
        _profile_context(request, request.user, profile, form, username_form),
    )


def public_profile_view(request, username):
    """Public page for a verified cook. Anyone else's page is a 404."""
    owner = User.objects.filter(username__iexact=username).first()
    if owner is None:
        raise Http404
    if request.user.is_authenticated and request.user.pk == owner.pk:
        return redirect('wangapi_profile')
    if not ChefProfile.objects.filter(user=owner, status=Status.APPROVED).exists():
        raise Http404
    profile, _ = Profile.objects.get_or_create(user=owner)
    return render(
        request, 'wangapi/profile.html',
        _profile_context(request, owner, profile, None, None),
    )


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
        # Recipes can only be saved once they are live.
        manager = model.objects
        queryset = manager.live() if hasattr(manager, 'live') else manager.all()
        if not queryset.filter(pk=pk).exists():
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

@login_required(login_url='wangapi_login')
def security_view(request):
    form = SecurityForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        password_changed, hint_changed = form.save()
        if password_changed:
            update_session_auth_hash(request, request.user)  # keeps this device logged in
        if password_changed and hint_changed:
            text = 'Your password and hint were updated.'
        elif password_changed:
            text = 'Your password was changed.'
        else:
            text = 'Your hint was saved.'
        notify(request.user, text)
        return redirect('wangapi_profile')
    return render(request, 'wangapi/security.html', {
        'form': form,
        'has_hint': form.profile.has_hint,
        'hint_question': form.profile.hint_question,
    })


FORGOT_KEY = 'forgot_uid'


def forgot_view(request):
    if request.user.is_authenticated:
        return redirect('wangapi_security')
    if request.GET.get('reset'):
        request.session.pop(FORGOT_KEY, None)
        return redirect('wangapi_forgot')

    profile = None
    uid = request.session.get(FORGOT_KEY)
    if uid:
        profile = Profile.objects.select_related('user').filter(user_id=uid).first()
        if profile is None or not profile.has_hint:
            request.session.pop(FORGOT_KEY, None)
            profile = None

    # Step 1: which account?
    if profile is None:
        error = ''
        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            candidate = (
                Profile.objects.select_related('user')
                .filter(user__username__iexact=username).first()
            )
            if candidate and candidate.has_hint:
                request.session[FORGOT_KEY] = candidate.user_id
                return redirect('wangapi_forgot')
            error = ("We couldn't find an account with a hint for that username. "
                     "If you never added a hint, ask the admin to reset your password.")
        return render(request, 'wangapi/forgot.html', {'step': 1, 'error': error})

    # Step 2: answer the hint and choose a new password
    form = ForgotResetForm(profile.user, request.POST or None)
    locked = profile.hint_locked
    if request.method == 'POST' and not locked and form.is_valid():
        with transaction.atomic():
            fresh = (
                Profile.objects.select_for_update().select_related('user')
                .get(pk=profile.pk)
            )
            ok = fresh.check_hint(form.cleaned_data['answer'])
        if ok:
            user = fresh.user
            user.set_password(form.cleaned_data['new_password'])
            user.save(update_fields=['password'])
            request.session.pop(FORGOT_KEY, None)
            notify(user, 'Your password was reset using your hint. If this was not you, contact the admin.')
            messages.success(request, 'Password changed. Sign in with your new password.')
            return redirect('wangapi_login')
        if fresh.hint_locked:
            notify(fresh.user, 'Someone got your hint answer wrong several times. Password reset is paused for 30 minutes.')
        form.add_error('answer', "That answer doesn't match.")
        locked = fresh.hint_locked

    return render(request, 'wangapi/forgot.html', {
        'step': 2, 'form': form, 'question': profile.hint_question, 'locked': locked,
    })
