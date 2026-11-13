import re

from django import forms
from django.contrib.auth import password_validation

from accounts.models import Profile, User

from .utils import PLACEHOLDER_SUFFIX

USERNAME_RE = re.compile(r'^[A-Za-z0-9_.]{3,30}$')


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)
    hint_question = forms.CharField(max_length=120)
    hint_answer = forms.CharField(max_length=100, min_length=2)
    agree = forms.BooleanField(
        required=True,
        error_messages={'required': 'Tick the box to agree to the privacy policy.'},
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not USERNAME_RE.match(username):
            raise forms.ValidationError('Use 3 to 30 letters, numbers, dots or underscores.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That username is taken. Try another.')
        return username

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get('username')
        password = cleaned.get('password')
        answer = (cleaned.get('hint_answer') or '').lower()
        

        if username and password:
            try:
                password_validation.validate_password(password, User(username=username))
            except forms.ValidationError as error:
                self.add_error('password', error)
        if answer and ((password and answer == password.lower())
                       or (username and answer == username.lower())):
            self.add_error('hint_answer', "The answer can't be your password or username.")
        return cleaned

    def save(self):
        username = self.cleaned_data['username']
        user = User(
            username=username,
            email=f'{username.lower()}{PLACEHOLDER_SUFFIX}',
            role='attendee',
        )
        user.set_password(self.cleaned_data['password'])
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.set_hint(self.cleaned_data['hint_question'], self.cleaned_data['hint_answer'])
        return user


class SecurityForm(forms.Form):
    
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)
    hint_question = forms.CharField(max_length=120, required=False)
    hint_answer = forms.CharField(max_length=100, required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.profile, _ = Profile.objects.get_or_create(user=user)

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.user.check_password(password):
            raise forms.ValidationError("That isn't your current password.")
        return password

    def clean(self):
        cleaned = super().clean()
        new = cleaned.get('new_password') or ''
        confirm = cleaned.get('confirm_password') or ''
        question = (cleaned.get('hint_question') or '').strip()
        answer = (cleaned.get('hint_answer') or '').strip()

        if new or confirm:
            if new != confirm:
                self.add_error('confirm_password', "The two passwords don't match.")
            else:
                try:
                    password_validation.validate_password(new, self.user)
                except forms.ValidationError as error:
                    self.add_error('new_password', error)

        if question or answer:
            if not (question and answer):
                self.add_error('hint_answer', 'Fill in both the hint and its answer.')
            elif answer.lower() in {new.lower(), self.user.username.lower()} - {''}:
                self.add_error('hint_answer', "The answer can't be your password or username.")
        elif not self.profile.has_hint:
            self.add_error('hint_question', 'Add a hint so you can reset your password if you forget it.')
        elif not new:
            raise forms.ValidationError('Nothing to change. Enter a new password or a new hint.')
        return cleaned

    def save(self):
        """Returns (password_changed, hint_changed)."""
        new = self.cleaned_data.get('new_password')
        question = (self.cleaned_data.get('hint_question') or '').strip()
        answer = (self.cleaned_data.get('hint_answer') or '').strip()
        if new:
            self.user.set_password(new)
            self.user.save(update_fields=['password'])
        if question and answer:
            self.profile.set_hint(question, answer)
        return bool(new), bool(question and answer)


class ForgotResetForm(forms.Form):
    answer = forms.CharField(max_length=100)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        new = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if new and confirm:
            if new != confirm:
                self.add_error('confirm_password', "The two passwords don't match.")
            else:
                try:
                    password_validation.validate_password(new, self.user)
                except forms.ValidationError as error:
                    self.add_error('new_password', error)
        return cleaned


class PictureForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        uploaded = self.files.get('profile_picture')
        if uploaded and uploaded.size > 3 * 1024 * 1024:
            raise forms.ValidationError('Pick a picture under 3 MB.')
        return picture


class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not USERNAME_RE.match(username):
            raise forms.ValidationError('Use 3 to 30 letters, numbers, dots or underscores.')
        taken = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError('That username is taken. Try another.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.email.endswith(PLACEHOLDER_SUFFIX):
            user.email = f'{user.username.lower()}{PLACEHOLDER_SUFFIX}'
        if commit:
            user.save()
        return user
