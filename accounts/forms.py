from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Profile


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            ('attendee', 'Attendee'),
            ('organiser', 'Organiser'),
        ]

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass


class VerificationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['verification_document']

    def clean_verification_document(self):
        doc = self.cleaned_data.get('verification_document')
        if doc:
            ext = doc.name.split('.')[-1].lower()
            if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                raise forms.ValidationError('Only PDF, JPG and PNG files are allowed.')
            if doc.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 5MB.')
        return doc

class ProfileSetupForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['location', 'interests', 'bio', 'profile_picture']
        widgets = {
            'interests': forms.TextInput(attrs={'placeholder': 'e.g. music, tech, food, sports'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Nairobi, Westlands'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us a bit about yourself...'}),
        }