from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Kind(models.TextChoices):
        WELCOME = "welcome", "Welcome"
        VERIFICATION = "verification", "Verification"
        RECIPE = "recipe", "Recipe"
        GENERAL = "general", "General"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.GENERAL)
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]
        constraints = [
            # one rolling "welcome back" notification per user, not one per login
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(kind="welcome"),
                name="one_welcome_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.message[:40]}"
