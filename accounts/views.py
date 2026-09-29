from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, VerificationForm, ProfileSetupForm
from django.contrib.auth.forms import AuthenticationForm
import hashlib
from django.shortcuts import get_object_or_404, render
from accounts.models import User

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            from .emails import send_welcome_email
            send_welcome_email(user)
            login(request, user)
            messages.success(request, f'Welcome to Evently, {user.username}!')
            if user.role == 'attendee':
                return redirect('profile_setup')
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('/accounts/login/')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def verification_submit_view(request):
    if request.user.role != 'organiser':
        messages.error(request, 'Only organisers can submit verification documents.')
        return redirect('/')

    if request.user.is_verified:
        messages.info(request, 'Your account is already verified.')
        return redirect('/accounts/profile/')

    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.verification_status = 'pending'
            if request.FILES.get('verification_document'):
                from .utils import hash_document
                user.verification_document_hash = hash_document(
                    request.FILES['verification_document']
                )
            user.save()
            from .emails import send_verification_submitted_email, send_verification_submitted_admin_email
            send_verification_submitted_email(user)
            send_verification_submitted_admin_email(user)
            messages.success(request, 'Document submitted. Awaiting admin review.')
            return redirect('/accounts/profile/')
    else:
        form = VerificationForm(instance=request.user)

    return render(request, 'accounts/verification_submit.html', {'form': form})

@login_required
def verification_status_view(request):
    return render(request, 'accounts/verification_status.html', {'user': request.user})

@login_required
def profile_setup(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile set up successfully!')
            return redirect('home')
    else:
        form = ProfileSetupForm(instance=profile)

    return render(request, 'accounts/profile_setup.html', {'form': form})

import hashlib
from django.shortcuts import get_object_or_404, render
from accounts.models import User

def verify_document_hash(request, user_pk):
    user = get_object_or_404(User, pk=user_pk)

    if not user.verification_document:
        return render(request, 'accounts/verify_hash.html', {
            'user': user,
            'no_document': True,
        })

    sha256 = hashlib.sha256()
    for chunk in user.verification_document.chunks():
        sha256.update(chunk)
    current_hash = sha256.hexdigest()

    is_valid = current_hash == user.verification_document_hash

    return render(request, 'accounts/verify_hash.html', {
        'user': user,
        'is_valid': is_valid,
        'current_hash': current_hash,
        'stored_hash': user.verification_document_hash,
        'no_document': False,
    })