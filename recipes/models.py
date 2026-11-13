from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from notifications.models import Notification
from notifications.services import notify
from django.urls import reverse

MAX_PHOTOS = 4


class Status(models.TextChoices):
    PENDING = "pending", "Pending review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class ChefProfile(models.Model):
    """The verification step: a user must add at least one link before posting."""

    LINK_FIELDS = ("instagram", "tiktok", "twitter", "youtube", "website")
    LINK_LABELS = {
        "instagram": "Instagram",
        "tiktok": "TikTok",
        "twitter": "Twitter / X",
        "youtube": "YouTube",
        "website": "Website",
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chef_profile"
    )
    display_name = models.CharField(
        max_length=60,
        blank=True,
        help_text="Optional name or fake name shown on recipes. Defaults to the username.",
    )
    instagram = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    website = models.URLField(blank=True)
    latest_post_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    moderator_note = models.CharField(max_length=255, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        if not any(getattr(self, f) for f in self.LINK_FIELDS):
            raise ValidationError("Add at least one social media or website link.")

    @property
    def name(self):
        return self.display_name or self.user.get_username()

    @property
    def is_approved(self):
        return self.status == Status.APPROVED

    @property
    def social_links(self):
        return [
            (self.LINK_LABELS[f], getattr(self, f))
            for f in self.LINK_FIELDS
            if getattr(self, f)
        ]

    def approve(self):
        self.status = Status.APPROVED
        self.moderator_note = ""
        self.reviewed_at = timezone.now()
        self.save()
        notify(
            self.user,
            "Your cooking profile was approved. You can now post recipes.",
            url=reverse("recipes:create"),
            kind=Notification.Kind.VERIFICATION,
        )

    def reject(self, note=""):
        self.status = Status.REJECTED
        self.moderator_note = note
        self.reviewed_at = timezone.now()
        self.save()
        text = "Your cooking profile was not approved."
        if note:
            text += f" {note}"
        notify(self.user, text, kind=Notification.Kind.VERIFICATION)


class RecipeQuerySet(models.QuerySet):
    def live(self):
        return self.filter(status=Status.APPROVED)

    def within_budget(self, amount):
        return self.filter(price__lte=amount)


class Recipe(models.Model):
    class Meal(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        SNACK = "snack", "Snack"
        SUPPER = "supper", "Supper"

    class SkillLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        EXPERT = "expert", "Expert"

    skill_level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices,
        default=SkillLevel.BEGINNER
    )

    chef = models.ForeignKey(
        ChefProfile, on_delete=models.CASCADE, related_name="recipes"
    )
    title = models.CharField(max_length=120)
    meal_type = models.CharField(max_length=10, choices=Meal.choices, db_index=True)
    ingredients = models.TextField(
        help_text="One per line. Add alternatives, e.g. Alt: egg instead of smokies."
    )
    instructions = models.TextField(help_text="One step per line. No need to add numbers.")
    tips = models.TextField(
        blank=True, help_text="Optional tips, alternatives or FAQs."
    )
    cooking_time = models.CharField(
        max_length=20, help_text="Free text, e.g. 30 or 40-50."
    )
    price = models.PositiveIntegerField(
        db_index=True, help_text="Estimated total in KSH."
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    moderator_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def ingredient_lines(self):
        return [l.strip() for l in self.ingredients.splitlines() if l.strip()]

    @property
    def instruction_lines(self):
        return [l.strip() for l in self.instructions.splitlines() if l.strip()]

    @property
    def image(self):
        """Cover photo, so analytics and compact cards can treat recipes like other posts."""
        photos = list(self.photos.all())
        return photos[0].image if photos else None

    @property
    def has_tips(self):
        return bool(self.tips.strip())

    def approve(self):
        self.status = Status.APPROVED
        self.moderator_note = ""
        self.save()
        notify(
            self.chef.user,
            f"Your recipe \u201c{self.title}\u201d is live.",
            kind=Notification.Kind.RECIPE,
        )

    def reject(self, note=""):
        self.status = Status.REJECTED
        self.moderator_note = note
        self.save()
        text = f"Your recipe \u201c{self.title}\u201d needs a change."
        if note:
            text += f" {note}"
        notify(self.chef.user, text, kind=Notification.Kind.RECIPE)

    def remove_for_report(self):
        user = self.chef.user
        title = self.title
        reasons = ", ".join(sorted({r.get_reason_display() for r in self.reports.all()}))
        self.delete()
        text = f"Your recipe post \u201c{title}\u201d was removed due to reports"
        text += f" ({reasons})." if reasons else "."
        notify(user, text, kind=Notification.Kind.RECIPE)


class RecipePhoto(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="recipes")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def clean(self):
        if self.recipe_id:
            others = RecipePhoto.objects.filter(recipe_id=self.recipe_id)
            if self.pk:
                others = others.exclude(pk=self.pk)
            if others.count() >= MAX_PHOTOS:
                raise ValidationError(f"A recipe can have at most {MAX_PHOTOS} photos.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class RecipeReport(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or an unrelated ad"
        OFFENSIVE = "offensive", "Offensive or inappropriate"
        UNSAFE = "unsafe", "Unsafe or wrong instructions"
        COPIED = "copied", "Copied from someone else"
        OTHER = "other", "Something else"

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipe_reports"
    )
    reason = models.CharField(max_length=12, choices=Reason.choices)
    details = models.CharField(max_length=255, blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("recipe", "user")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} reported {self.recipe} ({self.reason})"
