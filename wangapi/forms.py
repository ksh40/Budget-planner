import re

from django import forms
from django.contrib.auth import password_validation

from accounts.models import Profile, User

from .utils import PLACEHOLDER_SUFFIX

USERNAME_RE = re.compile(r'^[A-Za-z0-9_.]{3,30}$')


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)

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
        
        agree = forms.BooleanField(
        required=True,
        error_messages={'required': 'Tick the box to agree to the privacy policy.'},
        )
        if username and password:
            try:
                password_validation.validate_password(password, User(username=username))
            except forms.ValidationError as error:
                self.add_error('password', error)
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
        Profile.objects.get_or_create(user=user)
        return user
    

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
