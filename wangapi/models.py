from django.conf import settings
from django.db import models

from accounts.models import User


class Bookmark(models.Model):
    """One saved post. 'kind' is the model label, e.g. 'food.item'."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wangapi_bookmarks',
    )
    kind = models.CharField(max_length=60)
    object_id = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'kind', 'object_id'],
                name='wangapi_unique_bookmark',
            ),
        ]
        indexes = [models.Index(fields=['kind', 'object_id'])]

    def __str__(self):
        return f'{self.user} saved {self.kind} #{self.object_id}'


class WangapiAccount(User):
    """Admin-only view of the accounts created through Wangapi."""

    class Meta:
        proxy = True
        verbose_name = 'Wangapi account'
        verbose_name_plural = 'Wangapi accounts'
