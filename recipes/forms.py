from django import forms
from django.core.exceptions import ValidationError

from .models import MAX_PHOTOS, ChefProfile, Recipe, RecipeReport

MAX_PHOTO_BYTES = 3 * 1024 * 1024
_image_field = forms.ImageField()


def check_photos(files, keep=0):

    total = keep + len(files)
    if total == 0:
        raise ValidationError("Add at least one photo.")
    if total > MAX_PHOTOS:
        raise ValidationError(f"A recipe can have up to {MAX_PHOTOS} photos in total.")
    for f in files:
        if f.size > MAX_PHOTO_BYTES:
            raise ValidationError("Each photo must be under 3 MB.")
        _image_field.clean(f)
    return files


class ChefApplicationForm(forms.ModelForm):
    class Meta:
        model = ChefProfile
        fields = [
            "display_name", "instagram", "tiktok", "twitter",
            "youtube", "website", "latest_post_url",
        ]
        labels = {
            "display_name": "Username/Alias",
            "twitter": "Twitter",
            "latest_post_url": "Link to your latest food post (optional)",
        }
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "Optional. Defaults to your username"}),
            "instagram": forms.URLInput(attrs={"placeholder": "https://instagram.com/uracc"}),
            "tiktok": forms.URLInput(attrs={"placeholder": "https://tiktok.com/@uracc"}),
            "twitter": forms.URLInput(attrs={"placeholder": "https://x.com/uracc"}),
            "youtube": forms.URLInput(attrs={"placeholder": "https://youtube.com/@uracc"}),
            "website": forms.URLInput(attrs={"placeholder": "https://urwebsite.com"}),
            "latest_post_url": forms.URLInput(attrs={"placeholder": "Paste a link"}),
        }


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            "title", "meal_type", "skill_level", "ingredients", "instructions",
            "tips", "cooking_time", "price",
        ]
        labels = {
            "title": "Recipe name",
             "skill_level": "Skill level",
            "tips": "Tips, alternatives or FAQs (optional)",
            "price": "Estimated total price (KSH)",
        }
        widgets = {
            "ingredients": forms.Textarea(attrs={"rows": 5}),
            "instructions": forms.Textarea(attrs={"rows": 5}),
            "tips": forms.Textarea(attrs={"rows": 3}),
            "cooking_time": forms.TextInput(attrs={"placeholder": "30 or 40-50"}),
            "price": forms.NumberInput(attrs={"min": 0, "inputmode": "numeric", "placeholder": "250"}),
        }

class RecipeReportForm(forms.ModelForm):
    class Meta:
        model = RecipeReport
        fields = ["reason", "details"]
        labels = {"details": "Anything else we should know? (optional)"}